import uvicorn
from base_server import create_app
from handlers import ProductionHandler

# Create production handler
handler = ProductionHandler()

# Create FastAPI app with production handler
app = create_app(
    handler=handler,
    title="Theorem Similarity Search API",
    description="API for finding similar theorems using edit distance and Weisfeiler-Leman kernels"
)

if __name__ == "__main__":
    uvicorn.run(
        "main_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
