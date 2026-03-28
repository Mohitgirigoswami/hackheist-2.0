import os
import subprocess
import socket

def get_available_port() -> int:
    """
    Stub to dynamically assign an available host port to the container.
    """
    # TODO: Implement port finding logic (e.g., binding to port 0 to find a free port)
    return 3005

def clone_repo(repo_url: str, project_id: str) -> str:
    """
    Stub to clone a target git repository to a local directory.
    """
    clone_dir = f"/tmp/deployments/{project_id}"
    print(f"[Stub] Cloning {repo_url} into {clone_dir}...")
    # TODO: Implement subprocess call for `git clone`
    return clone_dir

def generate_dockerfile(source_dir: str) -> str:
    """
    Stub to generate a Dockerfile dynamically if one does not exist
    in the cloned repository.
    """
    print(f"[Stub] Checking for / generating Dockerfile in {source_dir}...")
    # TODO: Implement logic to inspect the project and create Dockerfile
    return os.path.join(source_dir, "Dockerfile")

def build_image(source_dir: str, project_id: str) -> str:
    """
    Stub to build the Docker image using the Docker CLI or SDK.
    """
    image_tag = f"project-{project_id}:latest"
    print(f"[Stub] Building Docker image {image_tag} from {source_dir}...")
    # TODO: Implement `docker build` subprocess
    return image_tag

def run_container(image_tag: str, project_id: str, port: int) -> str:
    """
    Stub to run the Docker container with the assigned port.
    """
    print(f"[Stub] Running container for {image_tag} on port {port}...")
    # TODO: Implement `docker run` subprocess with volume and network mappings
    container_id = "stub_container_123"
    return container_id

def process_deployment(repo_url: str, project_id: str) -> dict:
    """
    Main orchestration function for deployment requested by Track B.
    This coordinates the entire clone -> build -> run pipeline.
    """
    print(f"Starting deployment workflow for Project: {project_id}")
    print(f"Repository: {repo_url}")
    
    # 1. Clone
    source_dir = clone_repo(repo_url, project_id)
    
    # 2. Generate Dockerfile (if missing)
    generate_dockerfile(source_dir)
    
    # 3. Build Image
    image_tag = build_image(source_dir, project_id)
    
    # 4. Port Management
    assigned_port = get_available_port()
    
    # 5. Run Container
    container_id = run_container(image_tag, project_id, assigned_port)
    
    return {
        "status": "BUILDING",
        "project_id": project_id,
        "assigned_port": assigned_port,
        "container_id": container_id,
        "message": "Deployment workflow started (STUB)."
    }