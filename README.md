# Skialp Report Website

## Backend: FastAPI (Python)
- **What it does:** Serves skialp reports by fetching weather & avalanche data from external APIs.
- **Technologies Used:**
  - **FastAPI** – Lightweight Python web framework for APIs.
  - **Uvicorn** – ASGI server to run FastAPI.
  - **Requests** – Fetches data from Open-Meteo API.
  - **Fly.io** – Deploys & hosts the backend.

- **Deployment Steps:**
  - Created `main.py` with a `/report` endpoint.
  - Configured a `Dockerfile` for Fly.io.
  - Deployed backend with `flyctl deploy`.
  - **Live Backend:** `https://your-app-name.fly.dev/report`

---

## Frontend: React (Vite) 
- **What it does:** Fetches and displays the skialp report from the backend.
- **Technologies Used:**
  - **React** – Frontend framework for building UI.
  - **Vite** – Fast build tool for React apps.
  - **Axios** – Fetches data from the backend.
  - **Vercel** – Deploys & hosts the frontend.

- **Deployment Steps:**
  - Created a React project using Vite.
  - Built a simple UI to display the report.
  - Connected the frontend to the FastAPI backend.
  - Deployed with `vercel deploy`.
  - **Live Frontend:** `https://your-vercel-app.vercel.app`

---

## Current Status:
- Fully working **skialp report website**.
- Backend fetches **real-time weather & avalanche data**.
- Frontend displays reports **live from FastAPI**.

