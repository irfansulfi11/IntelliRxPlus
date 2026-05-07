from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import uvicorn
import os
from pathlib import Path

# Import routes
from app.api.routes import upload, history, search
from app.api.routes.interactions import router as interactions_router

# Import database setup
from app.db.database import engine
from app.db.base_class import Base

# Import models to ensure tables are created
from app.models.patient import Patient
from app.models.prescription import Prescription

# Create FastAPI app
app = FastAPI(
    title="IntelliRx+ API",
    description="AI-Powered Prescription Reader & Drug Interaction Checker API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",  # Alternative frontend ports
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"❌ Error creating database tables: {e}")

# Include routers
app.include_router(upload.router, tags=["Upload"])
app.include_router(history.router, prefix="/api", tags=["History"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(interactions_router, prefix="/api", tags=["Interactions"])

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "IntelliRx+ API is running",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "IntelliRx+ API",
        "database": "connected"
    }

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error occurred",
            "status_code": 500,
            "type": str(type(exc).__name__)
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 IntelliRx+ API starting up...")
    print("📊 Database connection established")
    print("🔗 CORS configured for frontend access")
    print("📝 API documentation available at: http://127.0.0.1:8000/docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 IntelliRx+ API shutting down...")

if __name__ == "__main__":
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )