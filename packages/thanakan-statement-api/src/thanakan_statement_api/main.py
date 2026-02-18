"""FastAPI application for Thai bank PDF statement parsing."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import parse, export

app = FastAPI(
    title="Thanakan Statement API",
    description="API for parsing Thai bank PDF statements",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5200",
        "http://localhost:3000",
        "https://thanakan.kunben.co",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(parse.router, prefix="/api/v1", tags=["parse"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
