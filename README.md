# Backend – PDF QA Application

This repository contains the backend for the PDF Question Answering (QA) application. It handles document uploads, processes PDFs using NLP services, and provides API routes for chat-based interactions.

---

## Project Structure
```plaintext
backend/
├── app/
│ ├── routers/ # API route handlers
│ │ ├── chat.py
│ │ └── document.py
│ ├── services/ # Core services (DB, QA, document processing)
│ │ ├── document_service.py
│ │ ├── qa_service.py
│ │ ├── database.py
│ │ └── models.py
│ └── main.py # FastAPI app entry point
├── indices/ # Vector indices or cache files
├── uploads/ # Uploaded PDF files
├── .env # Environment variables (not committed)
├── .gitignore
├── requirements.txt # Python dependencies
├── aiplanet.db # Local SQLite database
```


## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-backend-repo.git
cd your-backend-repo
```

2. Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Dependencies
```bash
pip install -r requirements.txt
```

4. Setup Environment Variables
Create a .env file in the root directory and include your configuration, such as:
```env
GEMINI_API_KEY=gemini_api_key
```

5. Run the Server
```bash
uvicorn app.main:app --reload
```

Server will start at http://localhost:8000

Key Endpoints
Method	Endpoint	Description
POST	/upload	Upload a PDF file
POST	/chat	Ask questions from uploaded PDF

Frontend Repository
You can find the frontend interface for this application here:
👉 Frontend Repository: [Backend Repository](https://github.com/JAYANTJOSHI001/aiplant-frontend)
