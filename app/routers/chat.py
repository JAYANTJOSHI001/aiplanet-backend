from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models import Document
from ..services.qa_service import QAService

router = APIRouter(prefix="/chat", tags=["chat"])
qa_service = QAService()

# Request and response models
class QuestionRequest(BaseModel):
    document_id: int
    question: str

class AnswerResponse(BaseModel):
    answer: str

@router.post("/ask", response_model=AnswerResponse)
def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    # Check if document exists
    document = db.query(Document).filter(Document.id == request.document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {request.document_id} not found"
        )
    
    # Get answer to question
    answer = qa_service.get_answer(request.document_id, request.question)
    
    return {"answer": answer}