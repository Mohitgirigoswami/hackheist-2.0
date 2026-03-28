import logging
import sys
import os
from typing import Dict, Any, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Request
from pydantic import BaseModel, HttpUrl

# Configure professional structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

import requests
# Ensure backend root is in PYTHONPATH so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.connection import get_db_connection

import json

router = APIRouter()

class DeployRequest(BaseModel):
    name: str
    repo_url: HttpUrl
    sub_directory: str = "/"
    env_vars: Dict[str, str] = {}
    deployment_type: str = "MANAGED"
    custom_worker_url: str = None
    memory_limit: int = None

@router.get("/projects", response_model=Dict[str, Any])
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
            
            # Inject WORKER_IP so the Frontend knows where to point the "Browse" links
            worker_ip = os.environ.get("WORKER_IP", "127.0.0.1")
            return {
                "projects": projects,
                "worker_ip": worker_ip
            }
    except Exception as e:
        logger.exception(f"Unexpected error executing /projects query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error while fetching projects."
        )
    finally:
        conn.close()

@router.get("/projects/{project_id}/logs")
async def get_project_logs(project_id: str):
    """ Track B: Proxy logs from the Track A Worker node. """
    try:
        worker_url = f"http://{os.environ.get('WORKER_IP', '127.0.0.1')}:5000"
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT deployment_type, custom_worker_url FROM projects WHERE id = %s", (project_id,))
                    project = cur.fetchone()
                    if project and project.get('deployment_type') == 'BYOC' and project.get('custom_worker_url'):
                        worker_url = project['custom_worker_url'].rstrip("/")
            except Exception as e:
                logger.error(f"Failed to fetch worker url for logs: {e}")
            finally:
                conn.close()

        response = requests.get(f"{worker_url}/logs/{project_id}", timeout=5)
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch logs for {project_id}: {e}")
        return {"logs": [f"Error fetching logs: {str(e)}"]}

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """ Track B: Clean up resources on Worker and delete from DB. """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="DB connection failed")
    
    try:
        # 1. Notify Worker to clean up Docker resources
        worker_url = f"http://{os.environ.get('WORKER_IP', '127.0.0.1')}:5000"
        with conn.cursor() as cur:
            cur.execute("SELECT deployment_type, custom_worker_url FROM projects WHERE id = %s", (project_id,))
            project = cur.fetchone()
            if project and project.get('deployment_type') == 'BYOC' and project.get('custom_worker_url'):
                worker_url = project['custom_worker_url'].rstrip("/")

        try:
            requests.post(f"{worker_url}/delete/{project_id}", timeout=10)
        except Exception as e:
            logger.error(f"Failed to notify worker for deletion: {e}")

        # 2. Remove from Database
        with conn.cursor() as cur:
            cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
            
        return {"message": "Project deleted successfully"}
    except Exception as e:
        logger.exception(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/projects/{project_id}/redeploy", status_code=status.HTTP_202_ACCEPTED)
async def redeploy_project(project_id: str, background_tasks: BackgroundTasks):
    """ Track B: Fetch existing metadata and trigger a fresh build. """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="DB unavailable")
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT repo_url, sub_directory, env_vars, deployment_type, custom_worker_url, memory_limit FROM projects WHERE id = %s", (project_id,))
            project = cur.fetchone()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            repo_url = project['repo_url']
            sub_dir = project['sub_directory']
            env_vars = project['env_vars'] if isinstance(project['env_vars'], dict) else json.loads(project['env_vars'] or '{}')
            dep_type = project.get('deployment_type', 'MANAGED')
            c_url = project.get('custom_worker_url')
            mem = project.get('memory_limit')
            
            # Reset status to QUEUED before redeploy
            cur.execute("UPDATE projects SET status = 'QUEUED' WHERE id = %s", (project_id,))
            
            background_tasks.add_task(execute_background_deployment, repo_url, project_id, sub_dir, env_vars, dep_type, c_url, mem)
            return {"message": "Redeploy triggered successfully", "id": project_id}
    except Exception as e:
        logger.exception(f"Redeploy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

def execute_background_deployment(repo_url: str, project_id: str, sub_directory: str = "/", env_vars: Dict[str, str] = {}, deployment_type: str = "MANAGED", custom_worker_url: str = None, memory_limit: int = None) -> None:
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
        worker_ip = os.environ.get("WORKER_IP", "127.0.0.1")
        worker_url = f"http://{worker_ip}:5000"
        if deployment_type == "BYOC" and custom_worker_url:
            worker_url = custom_worker_url.rstrip("/")
            
        # Call the standalone remote worker node!
        response = requests.post(f"{worker_url}/build", json={
            "repo_url": str(repo_url),
            "project_id": project_id,
            "sub_directory": sub_directory,
            "env_vars": env_vars,
            "memory_limit": memory_limit
        }, timeout=300) # 5 min timeout for building
        result = response.json()
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
                    "UPDATE projects SET status = %s, assigned_port = %s, framework = %s, build_duration = %s WHERE id = %s",
                    (
                        result.get("status", "FAILED"), 
                        result.get("assigned_port"), 
                        result.get("framework"),
                        result.get("build_duration"),
                        project_id
                    )
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
                "INSERT INTO projects (name, repo_url, sub_directory, status, env_vars, deployment_type, custom_worker_url, memory_limit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (req.name, str(req.repo_url), req.sub_directory, 'QUEUED', json.dumps(req.env_vars), req.deployment_type, req.custom_worker_url, req.memory_limit)
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
        background_tasks.add_task(execute_background_deployment, str(req.repo_url), project_id, req.sub_directory, req.env_vars, req.deployment_type, req.custom_worker_url, req.memory_limit)
        return {"project_id": project_id, "status": "QUEUED"}
    except Exception as e:
        logger.exception(f"Failed to initiate background task for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal error while starting background deployment task."
        )
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

@router.post("/webhook/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """ Track B Hour 10: Auto-Deploy Webhook Receiver for GitHub Push Events """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Check if this is a push to main
    ref = payload.get("ref")
    if ref and ref != "refs/heads/main":
        return {"message": "Ignored, not a push to main branch."}
        
    repo_url = payload.get("repository", {}).get("html_url")
    if not repo_url:
        return {"message": "Ignored, no repository URL found in payload."}

    # Find project in DB by repo_url
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection missing during /webhook/github.")
        raise HTTPException(status_code=503, detail="Database service connection unavailable.")
        
    project_id = None
    sub_directory = "/"
    dep_type = "MANAGED"
    c_url = None
    mem = None
    try:
        with conn.cursor() as cur:
            # Match repo URL (accounting for potential trailing .git or slashes)
            search_url = repo_url.rstrip(".git").rstrip("/")
            cur.execute(
                "SELECT id, sub_directory, deployment_type, custom_worker_url, memory_limit FROM projects WHERE repo_url LIKE %s LIMIT 1", 
                (f"{search_url}%",)
            )
            row = cur.fetchone()
            if row:
                project_id = str(row['id'])
                sub_directory = row.get('sub_directory', '/')
                dep_type = row.get('deployment_type', 'MANAGED')
                c_url = row.get('custom_worker_url')
                mem = row.get('memory_limit')
    except Exception as e:
        logger.exception(f"Database lookup failed for webhook deployment: {e}")
        raise HTTPException(status_code=500, detail="Database lookup failed.")
    finally:
        conn.close()

    if not project_id:
        logger.info(f"Webhook received for unknown repo: {repo_url}")
        return {"message": f"Ignored, no registered project found for {repo_url}."}

    logger.info(f"GitHub Webhook triggered auto-deployment for project {project_id}.")
    
    # Execute deployment workflow seamlessly
    background_tasks.add_task(execute_background_deployment, str(repo_url), project_id, sub_directory, {}, dep_type, c_url, mem)

    return {
        "message": "Auto-deployment queued successfully via GitHub Webhook",
        "projectId": project_id,
        "status": "QUEUED"
    }