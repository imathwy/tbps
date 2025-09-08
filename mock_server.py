from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import random
import asyncio

app = FastAPI(
    title="Mock Theorem Similarity Search API",
    description="Mock API for testing theorem similarity search without dependencies",
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

# Mock theorem names from mathlib
MOCK_THEOREM_NAMES = [
    "Nat.add_comm",
    "Nat.mul_comm",
    "Nat.add_assoc",
    "Nat.mul_assoc",
    "list.length_append",
    "list.reverse_reverse",
    "Set.union_comm",
    "Set.inter_comm",
    "Function.comp_assoc",
    "Finset.card_union",
    "Real.add_comm",
    "Real.mul_comm",
    "Int.add_comm",
    "Int.mul_comm",
    "Vector.cons_head_tail",
    "Matrix.mul_assoc",
    "Group.mul_assoc",
    "Ring.add_comm",
    "Field.div_self",
    "Topology.continuous_comp",
    "Measure.measure_union",
    "Probability.prob_union",
    "Analysis.derivative_add",
    "LinearAlgebra.basis_span",
    "Category.comp_assoc",
    "Logic.and_comm",
    "Logic.or_comm",
    "Logic.not_not",
    "Set.subset_union_left",
    "Fintype.card_subset"
]

# Mock theorem statements
MOCK_STATEMENTS = [
    "∀ (a b : Nat), a + b = b + a",
    "∀ (a b : Nat), a * b = b * a",
    "∀ (a b c : Nat), (a + b) + c = a + (b + c)",
    "∀ (l₁ l₂ : list α), list.length (l₁ ++ l₂) = list.length l₁ + list.length l₂",
    "∀ (A B : Set α), A ∪ B = B ∪ A",
    "∀ (f g h : α → β → γ), (f ∘ g) ∘ h = f ∘ (g ∘ h)",
    "∀ (s t : Finset α), s.card + t.card = (s ∪ t).card + (s ∩ t).card",
    "∀ (x y : ℝ), x + y = y + x",
    "∀ (G : Type) [Group G] (a b c : G), (a * b) * c = a * (b * c)",
    "∀ (R : Type) [Ring R] (a b : R), a + b = b + a",
    "∀ (l : list α), list.reverse (list.reverse l) = l",
    "∀ (A B : Set α), A ∩ B = B ∩ A",
    "∀ (p q : Prop), p ∧ q ↔ q ∧ p",
    "∀ (p q : Prop), p ∨ q ↔ q ∨ p",
    "∀ (p : Prop), ¬¬p ↔ p"
]

def generate_mock_results(expression: str, k: int) -> list[TheoremResult]:
    """Generate mock theorem results with realistic similarity scores."""
    results = []

    # Use expression hash to get consistent results for same input
    seed = hash(expression) % 1000
    random.seed(seed)

    # Generate k results
    num_results = min(k, len(MOCK_THEOREM_NAMES))
    selected_names = random.sample(MOCK_THEOREM_NAMES, num_results)
    selected_statements = random.sample(MOCK_STATEMENTS, min(len(MOCK_STATEMENTS), num_results))

    for i, name in enumerate(selected_names):
        # Generate decreasing similarity scores with some randomness
        base_score = 0.95 - (i * 0.08) + random.uniform(-0.05, 0.05)
        base_score = max(0.1, min(0.99, base_score))  # Keep in reasonable range

        statement = selected_statements[i % len(selected_statements)]
        node_count = random.randint(10, 150)

        results.append(TheoremResult(
            name=name,
            similarity_score=round(base_score, 4),
            statement=statement,
            node_count=node_count
        ))

    # Sort by similarity score descending
    results.sort(key=lambda x: x.similarity_score, reverse=True)
    return results

@app.post("/find-similar-theorems", response_model=SimilarTheoremsResponse)
async def find_similar_theorems(request: SimilarTheoremsRequest):
    """Mock endpoint that returns similar theorems for a given Lean expression."""
    try:
        # Simulate processing time (1-3 seconds)
        processing_time = random.uniform(1.0, 3.0)
        await asyncio.sleep(processing_time)

        # Validate expression (basic check)
        if not request.expression.strip():
            raise HTTPException(status_code=400, detail="Expression cannot be empty")

        if len(request.expression) > 1000:
            raise HTTPException(status_code=400, detail="Expression too long (max 1000 characters)")

        # Generate mock results
        results = generate_mock_results(request.expression, request.k)

        # Mock parsed expression
        mock_parsed = f"Mock parsed: {request.expression[:50]}{'...' if len(request.expression) > 50 else ''}"

        return SimilarTheoremsResponse(
            success=True,
            results=results,
            total_processed=len(results),
            expression_parsed=mock_parsed
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mock server error: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Mock health check endpoint."""
    # Simulate occasional service issues for testing
    db_status = random.random() > 0.05  # 95% uptime
    lean_status = random.random() > 0.02  # 98% uptime

    return HealthResponse(
        status="healthy" if db_status and lean_status else "degraded",
        version="1.0.0-mock",
        database_connected=db_status,
        lean_available=lean_status
    )

@app.get("/")
async def root():
    """Root endpoint with mock API information."""
    return {
        "message": "Mock Theorem Similarity Search API",
        "version": "1.0.0-mock",
        "endpoints": ["/find-similar-theorems", "/health"],
        "docs": "/docs",
        "note": "This is a mock server for testing. Results are simulated."
    }

@app.get("/mock-info")
async def mock_info():
    """Endpoint providing information about the mock server."""
    return {
        "is_mock": True,
        "available_mock_theorems": len(MOCK_THEOREM_NAMES),
        "sample_theorems": MOCK_THEOREM_NAMES[:5],
        "sample_statements": MOCK_STATEMENTS[:3],
        "features": [
            "Consistent results for same input",
            "Realistic similarity scores",
            "Simulated processing delays",
            "Random service degradation for testing",
            "No external dependencies required"
        ]
    }

if __name__ == "__main__":
    print("Starting Mock Theorem Similarity Search Server...")
    print("This server simulates the real API without requiring database or Lean dependencies.")
    print("Access the API documentation at: http://localhost:8001/docs")

    uvicorn.run(
        "mock_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )