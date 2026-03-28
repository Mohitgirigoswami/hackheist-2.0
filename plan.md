# **⚡ Team ZeroToDeploy: Hackathon Playbook & Parallel Execution Strategy**

**Objective:** Build "ZeroToDeploy" in 7 hours with 3 developers working simultaneously.

**Mantra:** Zero merge conflicts, constant forward momentum, test early.

## **1\. The Division of Labor (The 3 Tracks)**

To move at maximum speed, ownership must be absolute.

### **🛠️ Track A: The Engine (Mohit)**

*Responsibilities: Infrastructure, Docker, Observability*

* **Docker Compose:** Write the docker-compose.yml that boots up Prometheus, Grafana, and cAdvisor (PostgreSQL is handled remotely via Supabase/Neon).  
* **The Builder Script:** Write the Python utility (backend/services/docker\_worker.py) that handles the git clone, dynamic Dockerfile generation, docker build, and docker run using Python's subprocess or the docker SDK.  
* **Port Management:** Write the logic to dynamically assign available host ports to containers.  
* **Grafana Dashboards:** Configure the Grafana instance to read from Prometheus/cAdvisor and generate the embeddable iframe URL for the frontend.

### **🧠 Track B: The Brain (Praful)**

*Responsibilities: API, Database, Orchestration*

* **Remote PostgreSQL:** Execute the DB schema creation via the Supabase/Neon Web SQL Editor and configure the .env file with the remote connection string.  
* **FastAPI Server:** Scaffold the Python backend using FastAPI and Uvicorn (backend/main.py, backend/routes/api.py), managing dependencies via requirements.txt.  
* **Webhook/API Receiver:** Build the POST /api/deploy and GET /api/projects endpoints.  
* **Orchestration:** Import and trigger Mohit's docker\_worker.py logic when the /deploy route is hit, and update the remote DB status accordingly using a Python SQL library (like psycopg2 or SQLAlchemy).

### **🎨 Track C: The Face (Sania)**

*Responsibilities: UI/UX, API Integration, User Experience*

* **React/Vite Setup:** Initialize the frontend monorepo folder (/frontend).  
* **Dashboard Design:** Build the UI using Tailwind CSS (Project List, Status Badges, Deploy Form).  
* **Mock API Integration:** Build the frontend against a mocked version of Praful's API so development isn't blocked.  
* **Grafana Embedding:** Embed Mohit's Grafana iframe for project observability.

## **2\. The Hackathon Git Workflow**

We are using a **Monorepo Structure** with strict boundary lines to prevent Praful, Sania, and Mohit from overwriting each other's files.

### **The Conflict-Free Folder Structure**

zerotodeploy/  
├── docker-compose.yml          \<-- Mohit owns this  
├── .env                        \<-- Praful owns this (Supabase/Neon DB connection string)  
├── /backend  
│   ├── requirements.txt        \<-- Praful owns this (FastAPI, uvicorn, psycopg2, docker)  
│   ├── main.py                 \<-- Praful owns this (FastAPI entry point)  
│   ├── /routes                 \<-- Praful owns this  
│   ├── /db                     \<-- Praful owns this (DB connection setup)  
│   └── /services  
│       └── docker\_worker.py    \<-- Mohit owns this\! (Praful only imports it)  
└── /frontend                   \<-- Sania owns this entirely (React/JS)

### **The Branching Strategy**

We will use an ultra-lightweight Feature Branching model. No pull requests—just direct merges to main with communication.

1. **main**: The source of truth. It must ALWAYS be in a runnable state.  
2. **feat/engine** (Mohit's branch)  
3. **feat/api** (Praful's branch)  
4. **feat/ui** (Sania's branch)

**The Rule:** You only pull from main, and you only merge your branch to main when you are explicitly at an "Integration Checkpoint" and have verified it doesn't break the app.

## **3\. Hour-by-Hour Parallel Timeline**

### **Hour 1: Scaffolding & Setup**

* **Track A (Mohit):** Creates docker-compose.yml (Prometheus, Grafana, cAdvisor). Starts writing the docker\_worker.py stub.  
* **Track B (Praful):** Initializes FastAPI in /backend, connects to the remote Supabase/Neon database via connection string, and verifies the schema is created. Starts the Uvicorn dev server.  
* **Track C (Sania):** Initializes React/Vite in /frontend, configures Tailwind, creates base layout components.

### **Hour 2: Core Logic Development**

* **Track A (Mohit):** Implements the git clone, Dockerfile generation, and docker build commands inside the Python worker.  
* **Track B (Praful):** Writes the DB queries and the FastAPI route logic for GET /api/projects and POST /api/deploy.  
* **Track C (Sania):** Builds the "New Deployment" form and the "Projects Table" UI using mocked data.

### **🛑 Hour 3: INTEGRATION CHECKPOINT 1 (API & Database)**

* **Team Action:** 10-minute sync. Praful merges feat/api into main. Sania pulls main.  
* **Goal:** Sania updates the React frontend to point to Praful's *actual* GET /api/projects endpoint (which might just return empty DB arrays for now) instead of the mock. Note: FastAPI runs on http://localhost:8000 by default.  
* **Mohit:** Continues refining docker run logic and port allocation.

### **Hour 4: Wiring the Engine**

* **Track A & B (Mohit \+ Praful):** Pair programming. Mohit merges feat/engine into main. Praful wires the POST /api/deploy endpoint to actually call Mohit's Python process\_deployment() function.  
* **Track C (Sania):** Implements polling or loading states in the UI for the "BUILDING" status. Creates the modal/section for the Grafana iframe.

### **🛑 Hour 5: INTEGRATION CHECKPOINT 2 (End-to-End Test)**

* **Team Action:** EVERYONE on main.  
* **Goal:** We click "Deploy" on Sania's frontend. Praful's FastAPI catches it. Mohit's Engine clones a test repo, builds the Docker image, runs it, and the database updates. Sania's UI shows the app as "RUNNING".  
* **If it fails:** All 3 jump into debugging immediately.

### **Hour 6: Advanced Features (Python Apps & Subdirectories)**

* **Track A (Mohit):** Updates docker\_worker.py to accept a sub\_directory argument. After git clone, the script must change directory to the target subfolder before detecting the language. Adds language detection logic for Python (looks for requirements.txt or main.py) and generates a dynamic Python Dockerfile (FROM python:3.9-slim, pip install \-r, etc.).  
* **Track B (Praful):** Modifies the DB schema to add a sub\_directory column (default /). Updates the POST /api/deploy Pydantic model and route to accept sub\_directory and pass it to Mohit's worker function.  
* **Track C (Sania):** Updates the "New Deployment" form to include an optional "Root Directory" or "Subdirectory" text input. Updates the API payload to send this new field to Praful's backend.

### **Hour 7: Polish, Metrics, & Pitch Prep**

* **Track A (Mohit):** Finalizes the Grafana dashboard and hands the iframe URL structure to Sania.  
* **Track B (Praful):** Adds basic error handling (try/except blocks) so a failed build doesn't crash the Uvicorn server.  
* **Track C (Sania):** Plugs in the Grafana URL. Polishes UI, fixes margins, prepares the demo flow.

## **4\. API Mocking Strategy (For Sania)**

Sania cannot wait for Praful to finish the API. At Hour 1, Sania should create a file called src/services/api.js in the React app.

Instead of actually using fetch() or axios right away, Sania will return Promises that simulate the network delay and return the exact JSON structure defined in our Architecture Plan.

**Sania's frontend/src/services/api.js (Hour 1-2):**

// MOCK API \- Replace with actual fetch calls at Hour 3

export const getProjects \= async () \=\> {  
  return new Promise((resolve) \=\> {  
    setTimeout(() \=\> {  
      resolve({  
        projects: \[  
          {  
            id: "123e4567-e89b-12d3",  
            name: "test-react-app",  
            repo\_url: "\[https://github.com/test/app.git\](https://github.com/test/app.git)",  
            sub\_directory: "/",  
            assigned\_port: 3005,  
            status: "RUNNING", // Toggle this to 'BUILDING' or 'QUEUED' to test UI states  
            created\_at: new Date().toISOString()  
          }  
        \]  
      });  
    }, 500); // 500ms network simulation  
  });  
};

export const deployProject \= async (name, repo\_url, sub\_directory \= "/") \=\> {  
  return new Promise((resolve) \=\> {  
    setTimeout(() \=\> {  
      resolve({  
        message: "Deployment started",  
        projectId: "new-uuid-9876",  
        status: "QUEUED",  
        sub\_directory: sub\_directory  
      });  
    }, 1000);  
  });  
};

*At Hour 3 (Integration Checkpoint 1), Sania simply replaces these mock functions with actual fetch('http://localhost:8000/api/projects') calls (note the default FastAPI port 8000). No UI components need to be changed.*