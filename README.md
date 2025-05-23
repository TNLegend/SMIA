# SMIA Platform (Système de Management de l’Intelligence Artificielle)

## Overview

The SMIA platform is a comprehensive solution designed to support organizations in managing and auditing their Artificial Intelligence systems, following the **ISO/IEC 42001 standard**. The platform includes:

* An **organizational audit module** based on ISO 42001 requirements.
* A **technical AI risk analysis module** with dashboards and metrics.
* User, team, project, and document management features.

The project is split into two parts:

* **Backend:** Python, FastAPI, SQLModel ORM.
* **Frontend:** React, TypeScript, Vite, Material-UI.

---

## Prerequisites

### Backend

* **Python 3.10** or higher
* **pip** (Python package installer)
* **SQLite** (default) or another supported database

### Frontend

* **Node.js** (version 18 or higher recommended)
* **npm** or **yarn** package manager

---

## Installation

### Backend Setup

1.  Clone or download the backend source code.

2.  (Optional but recommended) Create and activate a Python virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate      # On Windows use: venv\Scripts\activate
    ```

3.  Install the required Python dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4.  (Optional) If database migrations are required, apply them now.

5.  Run the FastAPI backend server with:

    ```bash
    uvicorn app.main:app --reload
    ```

    The **Backend API** will be accessible at: `http://127.0.0.1:8000`

### Frontend Setup

1.  Clone or download the frontend source code.

2.  Install dependencies:

    ```bash
    npm install
    # or
    yarn install
    ```

3.  Start the frontend development server:

    ```bash
    npm run dev
    # or
    yarn dev
    ```

    The **Frontend app** will be available at: `http://localhost:5173`

### Configuration

* Ensure the frontend API base URL points to the backend server URL (default `http://localhost:8000`).
* Configure environment variables in `.env` files as needed (backend secrets, DB URL, frontend API URL).
* Adjust authentication secrets, database paths, and CORS policies accordingly.

---

## Usage

1.  Open `http://localhost:5173` in your browser.
2.  Register or log in.
3.  Create or join teams and projects.
4.  Perform ISO 42001 organizational audits.
5.  Upload datasets and AI models for risk analysis.
6.  View dashboards summarizing audit and risk metrics.
7.  Manage users, roles, documents, and notifications.

---

## Project Structure Overview

### Backend (`app/`)

* `main.py`: FastAPI entry point
* `models.py`: ORM models (SQLModel)
* `routers/`: API routes by feature
* `auth.py`: Authentication logic
* `db.py`: Database session management
* `metrics/`: AI risk evaluation pipelines

### Frontend (`src/`)

* `main.tsx`: React app entry point
* `App.tsx`: Main app component with routing
* `components/`: UI components
* `context/`: React contexts for auth & state
* `api/`: Backend API clients
* `pages/`: Route pages

---

## Technologies Used

* **Python**, **FastAPI**, **SQLModel**, **SQLite**, **Uvicorn**
* **React**, **TypeScript**, **Vite**, **Material-UI**
* **JWT Authentication**, **REST API**, **Axios**

---

## Contributing

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/your-feature`).
3.  Commit your changes (`git commit -m 'Add feature'`).
4.  Push your branch (`git push origin feature/your-feature`).
5.  Open a Pull Request.
