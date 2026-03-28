from fastapi import APIRouter
from pydantic import BaseModel
import sys
import os

# Ensure backend root is in PYTHONPATH so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.docker_worker import process_deployment

router = APIRouter()

class DeployRequest(BaseModel):
    name: str
    repo_url: str

@router.get("/projects")
async def get_projects():
    """ Track B: Stub for GET /api/projects """
    # TODO: Fetch from PostgreSQL database using connection.py
    return {"projects": []}

@router.post("/deploy")
async def deploy_project(req: DeployRequest):
    """ Track B: Stub for POST /api/deploy """
    # 1. TODO: Insert new project explicitly into the database with 'QUEUED' status
    
    project_id = "stub-id-1234" # Should be generated from DB insert
    
    # 2. Trigger Track A's worker
    print(f"[API] Triggering deployment for {req.name}")
    # result = process_deployment(req.repo_url, project_id) # Uncomment to execute worker
    
    return {
        "message": "Deployment started",
        "projectId": project_id,
        "status": "QUEUED"
    }