from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.api import router as api_router
from db.connection import verify_schema
import uvicorn

app = FastAPI(title="Local Vercel Clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    print("Starting up FastAPI backend server...")
    verify_schema()

# Include API routes from Hour 1 Track B roadmap
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "API is running. Visit /docs for the Swagger UI."}

if __name__ == "__main__":
    # Start the Uvicorn dev server programmatically
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)