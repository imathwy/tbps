from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Protocol

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

class TheoremHandler(Protocol):
    """Protocol defining the interface for theorem search handlers."""

    async def find_similar_theorems(
        self,
        expression: str,
        k: int,
        node_ratio: float | None = None
    ) -> tuple[list[TheoremResult], str]:
        """
        Find similar theorems for the given expression.
        Returns: (list of theorem results, parsed expression string)
        """
        ...

    async def check_health(self) -> tuple[bool, bool, str]:
        """
        Check the health of dependencies.
        Returns: (database_connected, lean_available, version)
        """
        ...

def create_app(handler: TheoremHandler, title: str, description: str) -> FastAPI:
    """Create FastAPI app with the given handler."""
    app = FastAPI(
        title=title,
        description=description,
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/find-similar-theorems", response_model=SimilarTheoremsResponse)
    async def find_similar_theorems_endpoint(request: SimilarTheoremsRequest):
        """Find similar theorems for a given Lean expression."""
        try:
            # Use default value if k is None
            k_value = request.k if request.k is not None else 20

            # Call handler
            results, parsed_expression = await handler.find_similar_theorems(
                request.expression,
                k_value,
                request.node_ratio
            )

            return SimilarTheoremsResponse(
                success=True,
                results=results,
                total_processed=len(results),
                expression_parsed=parsed_expression
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    @app.get("/health", response_model=HealthResponse)
    async def health_check_endpoint():
        """Health check endpoint to verify server status and dependencies."""
        try:
            database_connected, lean_available, version = await handler.check_health()

            return HealthResponse(
                status="healthy" if database_connected and lean_available else "degraded",
                version=version,
                database_connected=database_connected,
                lean_available=lean_available
            )
        except Exception as err:
            return HealthResponse(
                status=f"error: {err}",
                version="unknown",
                database_connected=False,
                lean_available=False
            )

    @app.get("/")
    async def root_endpoint():
        """Root endpoint with basic API information."""
        return {
            "message": app.title,
            "version": app.version,
            "endpoints": ["/find-similar-theorems", "/health"],
            "docs": "/docs"
        }

    return app
