// Dynamically determine the API URL. If the user is on LAN, use the current host's port 8000.
// If the user is running locally but the backend is on a friend's machine, they should update this.
const API_URL = `http://${window.location.hostname}:8000/api`;

export const getProjects = async () => {
  try {
    const res = await fetch(`${API_URL}/projects`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return await res.json();
  } catch (error) {
    console.error("Error fetching projects:", error);
    return { projects: [] };
  }
};

export const deployProject = async (name, repo_url, sub_directory = "/", env_vars = {}) => {
  try {
    const res = await fetch(`${API_URL}/deploy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, repo_url, sub_directory, env_vars }),
    });
    if (!res.ok) throw new Error('Failed to deploy project');
    return await res.json();
  } catch (error) {
    console.error("Error deploying project:", error);
    throw error;
  }
};

export const getProjectLogs = async (projectId) => {
  try {
    const res = await fetch(`${API_URL}/projects/${projectId}/logs`);
    if (!res.ok) throw new Error('Failed to fetch logs');
    return await res.json();
  } catch (error) {
    console.error("Error fetching logs:", error);
    return { logs: ["Error fetching logs from server."] };
  }
};

export const deleteProject = async (projectId) => {
  try {
    const res = await fetch(`${API_URL}/projects/${projectId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete project');
    return await res.json();
  } catch (error) {
    console.error("Error deleting project:", error);
    throw error;
  }
};

export const redeployProject = async (projectId) => {
  try {
    const res = await fetch(`${API_URL}/projects/${projectId}/redeploy`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to redeploy project');
    return await res.json();
  } catch (error) {
    console.error("Error redeploying project:", error);
    throw error;
  }
};