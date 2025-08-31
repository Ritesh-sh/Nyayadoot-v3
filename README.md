# Legal Chatbot Project

## Overview
This project is a legal chatbot application that consists of two main components:
1. **Backend**: A FastAPI-based backend for processing chat queries and providing legal information.
2. **Frontend**: A React-based user interface for interacting with the chatbot.

---

## Project Structure
```
1/
    .env                # Environment variables for the backend
    main.py             # Entry point for the FastAPI backend
    requirements.txt    # Python dependencies for the backend
    ai/                 # AI-related modules
    api/                # API routing logic
    conversation/       # Conversation state management
    keywords/           # Keyword extraction logic
    retrieval/          # Legal section retrieval logic
    scraping/           # Web scraping utilities
    utils/              # Helper utilities
l-frontend/
    public/             # Static assets for the frontend
    src/                # Source code for the React frontend
    vite.config.js      # Vite configuration for the frontend
    package.json        # Node.js dependencies for the frontend
```

---

## Backend Setup

### Prerequisites
- Python 3.10 or higher
- `pip` (Python package manager)

### Installation
1. Navigate to the backend folder:
   ```bash
   cd 1
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the `1/` directory and configure the required environment variables.

### Running the Backend
Start the FastAPI server:
```bash
python main.py
```

The backend will be available at `http://localhost:8000`.

---

## Frontend Setup

### Prerequisites
- Node.js 16 or higher
- npm (Node.js package manager)

### Installation
1. Navigate to the frontend folder:
   ```bash
   cd l-frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

### Running the Frontend
Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Environment Variables

### Backend
- Configure the `.env` file in the `1/` directory.

### Frontend
- Create a `.env` file in the `l-frontend/` directory and add:
  ```
  VITE_API_URL=http://localhost:8000
  ```

---

## Deployment
### Backend
- Use a production-ready server like `uvicorn` or `gunicorn` with FastAPI.

### Frontend
- Build the frontend for production:
  ```bash
  npm run build
  ```
- Serve the `dist/` folder using a static file server.

---

## License
This project is licensed under the MIT License.
