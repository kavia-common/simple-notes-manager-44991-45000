import os
import uvicorn

def main():
    """Run the FastAPI app with uvicorn on port 3001."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3001"))
    uvicorn.run("api.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
