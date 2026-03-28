import os
import subprocess
import socket
import shutil
import glob
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import json
import time

from typing import Dict, Any, List

app = FastAPI(title="ZeroToDeploy BYOC Node")

# Global store for live logs during build/deploy
deployment_logs: Dict[str, List[str]] = {}

class BuildRequest(BaseModel):
    repo_url: str
    project_id: str
    sub_directory: str = "/"
    env_vars: Dict[str, str] = {}

def get_available_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def log(project_id: str, message: str):
    if project_id not in deployment_logs:
        deployment_logs[project_id] = []
    deployment_logs[project_id].append(message)
    print(f"[{project_id}] {message}")

def run_command(cmd: List[str], project_id: str, cwd: str = None) -> str:
    log(project_id, f"Running: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    full_output = []
    for line in process.stdout:
        line = line.strip()
        if line:
            log(project_id, line)
            full_output.append(line)
            
    process.wait()
    if process.returncode != 0:
        raise Exception(f"Command failed with code {process.returncode}")
    
    return "\n".join(full_output)

def clone_repo(repo_url: str, project_id: str) -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "tmp_deployments"))
    os.makedirs(base_dir, exist_ok=True)
    clone_dir = os.path.join(base_dir, project_id)
    
    if os.path.exists(clone_dir):
        log(project_id, f"Purging existing directory {clone_dir}...")
        shutil.rmtree(clone_dir)
        
    log(project_id, f"Cloning {repo_url} into workspace...")
    run_command(["git", "clone", repo_url, clone_dir], project_id)
    return clone_dir

def generate_dockerfile(source_dir: str, project_id: str) -> Dict[str, str]:
    dockerfile_path = os.path.join(source_dir, "Dockerfile")
    framework = "Unknown"
    
    if os.path.exists(dockerfile_path):
        log(project_id, "Using existing Dockerfile found in repository.")
        return {"path": dockerfile_path, "framework": "Docker"}

    log(project_id, "No Dockerfile found. Auto-generating one...")

    is_python = False
    if os.path.exists(os.path.join(source_dir, "requirements.txt")) or glob.glob(os.path.join(source_dir, "*.py")):
        is_python = True
        framework = "Python"
        log(project_id, "Detected Python environment.")

    if is_python:
        # ... python logic ...
        entrypoint = "main.py"
        for candidate in ["main.py", "run.py", "app.py"]:
            if os.path.exists(os.path.join(source_dir, candidate)):
                entrypoint = candidate
                break
        else:
            py_files = glob.glob(os.path.join(source_dir, "*.py"))
            if py_files:
                entrypoint = os.path.basename(py_files[0])
        
        log(project_id, f"Using {entrypoint} as entry point.")

        dockerfile_content = f"""FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN if [ -f "requirements.txt" ]; then pip install --no-cache-dir -r requirements.txt; fi
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
CMD ["python", "{entrypoint}"]
"""
    else:
        framework = "Node.js"
        log(project_id, "Detected Node.js environment.")
        dockerfile_content = """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build --if-present
RUN npm install -g serve
EXPOSE 3000
CMD if [ -d "dist" ]; then serve -s dist -l 3000; elif [ -d "build" ]; then serve -s build -l 3000; else npm start; fi
"""
    with open(dockerfile_path, 'w') as f:
        f.write(dockerfile_content)
    log(project_id, "Dockerfile generated successfully.")
    return {"path": dockerfile_path, "framework": framework}

def build_image(source_dir: str, project_id: str) -> str:
    image_tag = f"project-{project_id}:latest"
    log(project_id, f"Building Docker image {image_tag}...")
    run_command(["docker", "build", "-t", image_tag, "."], project_id, cwd=source_dir)
    return image_tag

def run_container(image_tag: str, project_id: str, port: int, framework: str, env_vars: Dict[str, str] = {}) -> str:
    container_name = f"container-{project_id}"
    log(project_id, f"Removing existing container {container_name} if it exists...")
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, check=False)
    
    target_port = "8000" if framework == "Python" else "3000"
    cmd = ["docker", "run", "-d", "-p", f"{port}:{target_port}", "--name", container_name]
    for key, value in env_vars.items():
        cmd.extend(["-e", f"{key}={value}"])
    cmd.append(image_tag)
    
    log(project_id, f"Starting container on port {port}...")
    container_id = run_command(cmd, project_id)
    return container_id

@app.get("/logs/{project_id}")
async def get_logs(project_id: str):
    return {"logs": deployment_logs.get(project_id, ["No logs found for this project."])}

@app.post("/delete/{project_id}")
async def delete_project(project_id: str):
    log(project_id, f"--- Deleting Project {project_id} ---")
    try:
        container_name = f"container-{project_id}"
        image_tag = f"project-{project_id}:latest"
        
        log(project_id, f"Stopping and removing container {container_name}...")
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, check=False)
        
        log(project_id, f"Removing image {image_tag}...")
        subprocess.run(["docker", "rmi", "-f", image_tag], capture_output=True, check=False)
        
        # Clean up logs
        if project_id in deployment_logs:
            del deployment_logs[project_id]
            
        return {"status": "DELETED", "message": "Project resources purged from node."}
    except Exception as e:
        log(project_id, f"Delete Error: {str(e)}")
        return {"status": "FAILED", "message": str(e)}

@app.post("/build")
async def build_project(req: BuildRequest):
    start_time = time.time()
    log(req.project_id, f"--- Starting Build Instruction for {req.project_id} ---")
    try:
        source_dir = clone_repo(req.repo_url, req.project_id)
        target_dir = source_dir
        if req.sub_directory and req.sub_directory != "/":
            target_dir = os.path.abspath(os.path.join(source_dir, req.sub_directory.strip("/")))
        
        gen_result = generate_dockerfile(target_dir, req.project_id)
        image_tag = build_image(target_dir, req.project_id)
        
        assigned_port = get_available_port()
        container_id = run_container(image_tag, req.project_id, assigned_port, gen_result["framework"], req.env_vars)
        
        # Cleanup source directory
        shutil.rmtree(source_dir, ignore_errors=True)
        
        duration = round(time.time() - start_time, 2)
        log(req.project_id, f"Deployment complete in {duration}s! Workspace cleaned up.")
        
        return {
            "status": "RUNNING",
            "project_id": req.project_id,
            "assigned_port": assigned_port,
            "container_id": container_id,
            "framework": gen_result["framework"],
            "build_duration": duration,
            "message": "Deployment completed successfully on remote BYOC node."
        }
    except Exception as e:
        log(req.project_id, f"CRITICAL ERROR: {str(e)}")
        return {"status": "FAILED", "project_id": req.project_id, "message": str(e)}

if __name__ == "__main__":
    print("Starting ZeroToDeploy Autonomous Worker Node on Port 5000...")
    uvicorn.run(app, host="0.0.0.0", port=5000)
