import uvicorn
from base_server import create_app
from handlers import MockHandler

# Create mock handler
handler = MockHandler()

# Create FastAPI app with mock handler
app = create_app(
    handler=handler,
    title="Mock Theorem Similarity Search API",
    description="Mock API for testing theorem similarity search without dependencies"
)

# Add mock-specific endpoint
@app.get("/mock-info")
async def mock_info():
    """Endpoint providing information about the mock server."""
    return {
        "is_mock": True,
        "available_mock_theorems": len(handler.mock_theorem_names),
        "sample_theorems": handler.mock_theorem_names[:5],
        "sample_statements": handler.mock_statements[:3],
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
