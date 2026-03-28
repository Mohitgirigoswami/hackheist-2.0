from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.api import router as api_router
from db.connection import verify_schema, get_db_connection
import uvicorn
import asyncio
import requests
import os

app = FastAPI(title="ZeroToDeploy API")

# Ensure Track C (React) can communicate with Track B (FastAPI) properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Broad CORS for hackathon development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def health_check_loop():
    """ Periodically check health of all RUNNING containers. """
    while True:
        await asyncio.sleep(30) # Check every 30 seconds
        conn = get_db_connection()
        if not conn: continue
        
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, assigned_port FROM projects WHERE status = 'RUNNING'")
                projects = cur.fetchall()
                
                for p in projects:
                    pid, port = p['id'], p['assigned_port']
                    if not port: continue
                    
                    try:
                        # Simple TCP check or HTTP GET
                        worker_ip = os.environ.get("WORKER_IP", "127.0.0.1")
                        resp = requests.get(f"http://{worker_ip}:{port}", timeout=2)
                        if resp.status_code >= 500:
                            cur.execute("UPDATE projects SET status = 'UNHEALTHY' WHERE id = %s", (pid,))
                    except:
                        cur.execute("UPDATE projects SET status = 'DOWN' WHERE id = %s", (pid,))
        except Exception as e:
            print(f"Health check error: {e}")
        finally:
            conn.close()

@app.on_event("startup")
async def on_startup():
    print("Starting up FastAPI backend server...")
    verify_schema()
    # Start health check loop in the background
    asyncio.create_task(health_check_loop())

# Include API routes from Hour 1 Track B roadmap
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "API is running. Visit /docs for the Swagger UI."}

if __name__ == "__main__":
    # Start the Uvicorn dev server programmatically
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
