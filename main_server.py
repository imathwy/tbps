from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import subprocess
import json
import os
from process_single import process_single_prop_new
from myexpr import deserialize_expr  # pyright: ignore[reportUnknownVariableType]
from cse import cse
from WL.db_utils import connect_to_db  # pyright: ignore[reportPrivateLocalImportUsage, reportUnknownVariableType]

PROJECT_ROOT = r"/Users/princhern/Documents/structure_search/TreeSelect/Lean_tool"
INPUT_TXT = os.path.join(PROJECT_ROOT, "input_expr.txt")
OUTPUT_JSON = os.path.join(PROJECT_ROOT, "expr_output.json")

app = FastAPI(
    title="Theorem Similarity Search API",
    description="API for finding similar theorems using edit distance and Weisfeiler-Leman kernels",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimilarTheoremsRequest(BaseModel):
    expression: str = Field(..., description="Lean expression to find similar theorems for")
    k: int | None = Field(default=20, ge=1, le=100, description="Number of top similar theorems to return")
    node_ratio: float | None = Field(default=None, ge=1.0, le=2.0, description="Node ratio filter (auto-determined if not provided)")

class TheoremResult(BaseModel):
    name: str
    similarity_score: float
    statement: str
    node_count: int

class SimilarTheoremsResponse(BaseModel):
    success: bool
    results: list[TheoremResult]
    total_processed: int
    expression_parsed: str

class HealthResponse(BaseModel):
    status: str
    version: str
    database_connected: bool
    lean_available: bool

def run_lean(input_str: str):
    """Parse Lean expression using the Lean tool."""
    try:
        with open(INPUT_TXT, "w", encoding="utf-8") as f:
            f.write(input_str.strip())  # pyright: ignore[reportUnusedCallResult]

        result = subprocess.run(
            ["lake", "exe", "Mathlib_Construction"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30
        )

        if result.returncode != 0:
            raise Exception(f"Lean execution failed: {result.stderr}")

        if not os.path.exists(OUTPUT_JSON):
            raise Exception(f"{OUTPUT_JSON} not generated")

        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            name: str = data["input_str"].strip()
            statement_str: str = data["expr_dbg"].strip()
            expr_json = data["your_expr"]

        return [(name, expr_json, statement_str)]

    except subprocess.TimeoutExpired:
        raise Exception("Lean parsing timed out after 30 seconds")
    except Exception as e:
        raise Exception(f"Lean parsing error: {str(e)}")

@app.post("/find-similar-theorems", response_model=SimilarTheoremsResponse)
async def find_similar_theorems(request: SimilarTheoremsRequest):
    """Find similar theorems for a given Lean expression."""
    try:
        # Parse the Lean expression
        steps = run_lean(request.expression)
        if not steps:
            raise HTTPException(status_code=400, detail="Failed to parse Lean expression")

        name, expr_json, statement_str = steps[0]

        # Deserialize and apply CSE transformation
        original_expr = deserialize_expr(expr_json)
        cse_expr = cse(original_expr)

        # Find similar theorems
        results = process_single_prop_new(cse_expr, request.k)

        # Format results
        theorem_results = []
        for theorem_name, similarity, statement, node_count in results:
            theorem_results.append(TheoremResult(
                name=theorem_name,
                similarity_score=round(similarity, 4),
                statement=statement,
                node_count=node_count
            ))

        return SimilarTheoremsResponse(
            success=True,
            results=theorem_results,
            total_processed=len(results),
            expression_parsed=statement_str
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify server status and dependencies."""
    database_connected = False
    lean_available = False

    # Check database connection
    try:
        conn = connect_to_db()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        database_connected = True
    except Exception:
        database_connected = False

    # Check if Lean is available
    try:
        result = subprocess.run(
            ["lake", "--version"],
            cwd=PROJECT_ROOT if os.path.exists(PROJECT_ROOT) else ".",
            capture_output=True,
            text=True,
            timeout=5
        )
        lean_available = result.returncode == 0
    except Exception:
        lean_available = False

    return HealthResponse(
        status="healthy" if database_connected and lean_available else "degraded",
        version="1.0.0",
        database_connected=database_connected,
        lean_available=lean_available
    )

@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Theorem Similarity Search API",
        "version": "1.0.0",
        "endpoints": ["/find-similar-theorems", "/health"],
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
