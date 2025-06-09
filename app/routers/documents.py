from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
from ..database import get_db
from ..models import Document
from ..services.document_processor import DocumentProcessor

router = APIRouter(prefix="/documents", tags=["documents"])
document_processor = DocumentProcessor()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check if file is a PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Save file to disk
        filepath = document_processor.save_pdf(file_content, file.filename)
        
        # Create document record in database
        db_document = Document(filename=file.filename, filepath=filepath)
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Create index for the document
        document_processor.create_index(db_document.id, filepath)
        
        return {
            "id": db_document.id,
            "filename": db_document.filename,
            "upload_date": db_document.upload_date
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("/", response_model=List[dict])
def get_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "upload_date": doc.upload_date
        }
        for doc in documents
    ]


@router.post("/{document_id}/reindex", status_code=status.HTTP_200_OK)
def reindex_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    # Check if document exists
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    try:
        # Check if file exists
        if not os.path.exists(document.filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found at {document.filepath}"
            )
        
        # Create index for the document
        success = document_processor.create_index(document.id, document.filepath)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create index for document"
            )
        
        return {
            "message": f"Document {document_id} reindexed successfully",
            "id": document.id,
            "filename": document.filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reindexing document: {str(e)}"
        )