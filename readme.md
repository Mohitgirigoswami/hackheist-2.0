# ⚡ ZeroToDeploy

ZeroToDeploy is a lightning-fast, local-first Vercel alternative. It allows developers to instantly clone, build, and deploy containerized applications from their local machine with a single click.

## Architecture

This project is built using a decoupled Microservices architecture representing three concurrent hackathon development tracks:
- **Track A (Engine)**: Python Docker Worker orchestrating dynamic container provisioning (git clone, docker build, port assignment).
- **Track B (Brain)**: FastAPI & remote PostgreSQL (Neon) orchestrating deployment triggers and managing state.
- **Track C (Face)**: React & Vite with Tailwind CSS v4, delivering a premium glassmorphism dashboard.

## Quick Start

### 1. The Backend (API & Engine)
```bash
cd backend
pip install -r requirements.txt
python main.py
```
*Note: Make sure Docker is running on your machine to provision deployments successfully.*

### 2. The Frontend (UI)
```bash
cd frontend
npm install
npm run dev
```

Visit the frontend at `http://localhost:5173` and trigger your first zero-to-deploy pipeline!
