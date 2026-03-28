import os
import subprocess
import socket
import shutil
import glob

def get_available_port() -> int:
    """Dynamically assign an available ephemeral host port to the container."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def clone_repo(repo_url: str, project_id: str) -> str:
    """Clone a target git repository."""
    # Place repositories in a neighboring tmp_deployments folder
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tmp_deployments"))
    clone_dir = os.path.join(base_dir, project_id)
    
    if os.path.exists(clone_dir):
        print(f"[Worker] Found existing directory {clone_dir}, purging first...")
        shutil.rmtree(clone_dir)
        
    print(f"[Worker] Cloning {repo_url} into {clone_dir}...")
    subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    return clone_dir

def generate_dockerfile(source_dir: str) -> str:
    """Generate a dynamic Dockerfile for Node.js or Python if one does not exist."""
    dockerfile_path = os.path.join(source_dir, "Dockerfile")
    
    if os.path.exists(dockerfile_path):
        print(f"[Worker] Native Dockerfile found in {source_dir}.")
        return dockerfile_path

    # Advanced Language Detection Logic (Hour 6)
    is_python = False
    if os.path.exists(os.path.join(source_dir, "requirements.txt")):
        is_python = True
    else:
        # Check if there are any .py files
        py_files = glob.glob(os.path.join(source_dir, "*.py"))
        if py_files:
            is_python = True

    if is_python:
        print(f"[Worker] Python application detected. Generating Python Dockerfile...")
        
        # Ranking-based entrypoint selection
        entrypoint = None
        for candidate in ["main.py", "run.py", "app.py"]:
            if os.path.exists(os.path.join(source_dir, candidate)):
                entrypoint = candidate
                break
        
        if not entrypoint:
            # Fallback to any .py file
            py_files = glob.glob(os.path.join(source_dir, "*.py"))
            if py_files:
                entrypoint = os.path.basename(py_files[0])
            else:
                entrypoint = "main.py"
                
        dockerfile_content = f"""FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN if [ -f "requirements.txt" ]; then pip install --no-cache-dir -r requirements.txt; fi
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
CMD ["python", "{entrypoint}"]
"""
    else:
        print(f"[Worker] Native Dockerfile not found. Generating default Node/Vite Dockerfile...")
        dockerfile_content = """FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
# Use npm install, ignoring dev dependency squashing to ensure builds work
RUN npm install
COPY . .

# Try standard React/Vite build scripts if they exist
RUN npm run build --if-present

# Install serve for static files
RUN npm install -g serve

EXPOSE 3000

# Smarter entrypoint: Serve dist/build if standard Vite/CRA app, else run npm start
CMD if [ -d "dist" ]; then serve -s dist -l 3000; elif [ -d "build" ]; then serve -s build -l 3000; else npm start; fi
"""

    with open(dockerfile_path, 'w') as f:
        f.write(dockerfile_content)
        
    return dockerfile_path

def build_image(source_dir: str, project_id: str) -> str:
    """Build the Docker image locally via Docker CLI."""
    image_tag = f"project-{project_id}:latest"
    print(f"[Worker] Building Docker image {image_tag}...")
    subprocess.run(["docker", "build", "-t", image_tag, "."], cwd=source_dir, check=True)
    return image_tag

def run_container(image_tag: str, project_id: str, port: int) -> str:
    """Run the built Docker image mapping to the dynamically assigned host port."""
    container_name = f"container-{project_id}"
    print(f"[Worker] Running container {container_name} for image {image_tag} on port {port}...")
    
    # Prevent name conflicts if deploying the same project again
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, check=False)
    
    cmd = ["docker", "run", "-d", "-p", f"{port}:3000", "--name", container_name, image_tag]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    return res.stdout.strip()  # Returns container ID

def process_deployment(repo_url: str, project_id: str, sub_directory: str = "/") -> dict:
    """
    Main orchestration function for Track A.
    Coordinates clone -> dockerfile generation -> image build -> container execution.
    """
    print(f"\n[Worker] --- Starting Deployment Workflow for {project_id} ---")
    print(f"[Worker] Repository: {repo_url} | Subdirectory: {sub_directory}")
    
    try:
        source_dir = clone_repo(repo_url, project_id)
        
        target_dir = source_dir
        if sub_directory and sub_directory != "/":
            target_dir = os.path.abspath(os.path.join(source_dir, sub_directory.strip("/")))
            if not os.path.isdir(target_dir):
                raise ValueError(f"Subdirectory {sub_directory} not found in the repository.")
        
        generate_dockerfile(target_dir)
        image_tag = build_image(target_dir, project_id)
        
        # Cleanup cloned workspace post-build to conserve disk space
        shutil.rmtree(source_dir, ignore_errors=True)
        print(f"[Worker] Cleaned up temporary directory {source_dir}")
        
        assigned_port = get_available_port()
        container_id = run_container(image_tag, project_id, assigned_port)
        
        print(f"[Worker] Deployment {project_id} Successful on Port: {assigned_port}")
        return {
            "status": "RUNNING",
            "project_id": project_id,
            "assigned_port": assigned_port,
            "container_id": container_id,
            "message": "Deployment workflow completed via Track A engine."
        }
    except subprocess.CalledProcessError as e:
        error_msg = f"Subprocess command failed: {e.cmd}"
        print(f"[Worker] ERROR: {error_msg}")
        return {"status": "FAILED", "project_id": project_id, "message": error_msg}
    except Exception as e:
        print(f"[Worker] ERROR: {e}")
        return {"status": "FAILED", "project_id": project_id, "message": str(e)}