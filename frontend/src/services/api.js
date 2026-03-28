const API_URL = 'http://localhost:8000/api';

export const getProjects = async () => {
  try {
    const res = await fetch(`${API_URL}/projects`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return await res.json();
  } catch (error) {
    console.error("Error fetching projects:", error);
    return { projects: [] };
  }, sub_directory = "/") => {
  try {
    const res = await fetch(`${API_URL}/deploy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, repo_url, sub_directory }),
    });
    if (!res.ok) throw new Error('Failed to deploy project');
    return await res.json();
  } catch (error) {
    console.error("Error deploying project:", error);
    throw error;
  }
};

};

export const deployProject = async (name, repo_url