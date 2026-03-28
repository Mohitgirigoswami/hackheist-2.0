import logging
import sys
import os
from typing import Dict, Any, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, HttpUrl

# Configure professional structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Ensure backend root is in PYTHONPATH so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.docker_worker import process_deployment
from db.connection import get_db_connection

router = APIRouter()

class DeployRequest(BaseModel):
    name: str
    repo_url: HttpUrl
    sub_directory: str = "/"

@router.get("/projects", response_model=Dict[str, List[Dict[str, Any]]])
async def get_projects():
    """ Track B: Fetch all projects from the remote Neon database. """
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to acquire database connection for /projects GET request.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Database service unavailable."
        )
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
            projects = cur.fetchall()
            logger.info(f"Successfully fetched {len(projects)} projects.")
            return {"projects": projects}
    except Exception as e:
        logger.exception(f"Unexpected error executing /projects query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error while fetching projects."
        )
    finally:
        conn.close()

def execute_background_deployment(repo_url: str, project_id: str, sub_directory: str = "/") -> None:
    """
    Background worker function that triggers Mohit's engine logic 
    and updates the database with the result autonomously.
    """
    # 1. Update status to BUILDING before triggering the engine
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE projects SET status = 'BUILDING' WHERE id = %s", (project_id,))
                logger.info(f"Project {project_id} transitioned to BUILDING status.")
        except Exception as e:
            logger.error(f"Failed to update project {project_id} to BUILDING: {e}")
        finally:
            conn.close()

    # 2. Trigger Mohit's docker worker engine with pervasive error handling
    logger.info(f"Handing off deployment for {project_id} to Track A Engine...")
    result = {"status": "FAILED", "assigned_port": None, "message": "Unknown critical failure."}
    
    try:
        # We explicitly cast repo_url to string in case pydantic HttpUrl passes as an object
        result = process_deployment(str(repo_url), project_id, sub_directory)
    except Exception as e:
        # Crucial Hour 7 feature: Prevent background thread crashes
        logger.exception(f"Track A Engine threw an uncaught exception for {project_id}: {e}")
        result["message"] = f"Engine orchestration crash: {str(e)[:100]}"
    
    # 3. Update the remote DB with the engine's deterministic result
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE projects SET status = %s, assigned_port = %s WHERE id = %s",
                    (result.get("status", "FAILED"), result.get("assigned_port"), project_id)
                )
                logger.info(f"Deployment workflow complete. Project {project_id} finalized with status: {result.get('status')}")
        except Exception as e:
            logger.error(f"Failed to persist final deployment state for {project_id}: {e}")
        finally:
            conn.close()
    else:
        logger.error("Critical Database Connection Failure: Could not save final deployment state.")

@router.post("/deploy", status_code=status.HTTP_202_ACCEPTED)
async def deploy_project(req: DeployRequest, background_tasks: BackgroundTasks):
    """ 
    Track B: Insert project into Database and trigger Track A's Engine via non-blocking Background task. 
    """
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection missing during POST /deploy.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Database service connection unavailable."
        )
        
    project_id = None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO projects (name, repo_url, sub_directory, status) VALUES (%s, %s, %s, %s) RETURNING id",
                (req.name, str(req.repo_url), req.sub_directory, 'QUEUED')
            )
            inserted_row = cur.fetchone()
            if inserted_row:
                project_id = str(inserted_row['id'])
                logger.info(f"Successfully queued new deployment: {project_id}")
    except Exception as e:
        logger.exception(f"Database insertion failed for new deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to register deployment in database due to an internal error."
        )
    finally:
        if conn:
            conn.close()

    if not project_id:
        logger.error("Query succeeded but RETURNING sequence failed to yield a UUID.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to retrieve new project UUID sequence."
        )

    try:
        # Execute Track A's workflow non-blocking using FastAPI Background Tasks
        background_tasks.add_task(execute_background_deployment, str(req.repo_url), project_id, req.sub_directory)
    except Exception as e:
        logger.exception(f"Background task dispatch failed for {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize deployment worker thread."
        )

    return {
        "message": "Deployment queued successfully",
        "projectId": project_id,
        "status": "QUEUED"
    }