from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import sys
import os

# Ensure backend root is in PYTHONPATH so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.docker_worker import process_deployment
from db.connection import get_db_connection

router = APIRouter()

class DeployRequest(BaseModel):
    name: str
    repo_url: str

@router.get("/projects")
async def get_projects():
    """ Track B: Fetch all projects from the remote Neon database. """
    conn = get_db_connection()
    if not conn:
        return {"projects": []}
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
            projects = cur.fetchall()
            return {"projects": projects}
    except Exception as e:
        print(f"[API] Error fetching projects: {e}")
        return {"projects": []}
    finally:
        conn.close()

def execute_background_deployment(repo_url: str, project_id: str):
    """
    Background worker function that triggers Mohit's engine logic 
    and updates the database with the result.
    """
    # 1. Update status to BUILDING before triggering the engine
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE projects SET status = 'BUILDING' WHERE id = %s", (project_id,))
        except Exception as e:
            print(f"[DB] Error updating status to BUILDING: {e}")
        finally:
            conn.close()

    # 2. Trigger Mohit's docker worker engine
    print(f"[API] Handing off project {project_id} to Track A engine...")
    result = process_deployment(repo_url, project_id)
    
    # 3. Update the remote DB with the engine's result (RUNNING or FAILED)
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # result contains 'status', and potentially 'assigned_port'
                cur.execute(
                    "UPDATE projects SET status = %s, assigned_port = %s WHERE id = %s",
                    (result.get("status", "FAILED"), result.get("assigned_port", None), project_id)
                )
                print(f"[DB] Project {project_id} status updated to {result.get('status')}")
        except Exception as e:
            print(f"[DB] Error saving final project state: {e}")
        finally:
            conn.close()

@router.post("/deploy")
async def deploy_project(req: DeployRequest, background_tasks: BackgroundTasks):
    """ 
    Track B: Insert project into Database and trigger Track A's Engine via Background task. 
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection missing.")
        
    project_id = None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO projects (name, repo_url, status) VALUES (%s, %s, %s) RETURNING id",
                (req.name, req.repo_url, 'QUEUED')
            )
            inserted_row = cur.fetchone()
            if inserted_row:
                project_id = str(inserted_row['id'])
    except Exception as e:
        print(f"[API] Error inserting project: {e}")
        raise HTTPException(status_code=500, detail="Database insert failed.")
    finally:
        conn.close()

    if not project_id:
        raise HTTPException(status_code=500, detail="Failed to retrieve new project UUID.")

    # Execute Track A's workflow non-blocking using FastAPI Background Tasks
    background_tasks.add_task(execute_background_deployment, req.repo_url, project_id)

    return {
        "message": "Deployment queued successfully",
        "projectId": project_id,
        "status": "QUEUED"
    }