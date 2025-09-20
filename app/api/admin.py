from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.schemas import DocumentUpload, DocumentProcessResponse, UserCreate, UserResponse
from app.services.admin_service import AdminService
from app.services.document_processor import DocumentProcessor

router = APIRouter()

@router.post("/upload-document", response_model=DocumentProcessResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: str = "General",
    title: str = "",
    description: str = "",
    db: Session = Depends(get_db)
):
    """Upload and process a new HR document"""
    try:
        admin_service = AdminService(db)
        processor = DocumentProcessor()
        
        # Save uploaded file
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document
        result = await processor.process_document(
            file_path=file_path,
            category=category,
            title=title or file.filename,
            description=description
        )
        
        # Store in database
        await admin_service.store_processed_document(result)
        
        return DocumentProcessResponse(
            success=True,
            chunks_created=result.get("chunks_created", 0),
            message="Document processed successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    db: Session = Depends(get_db)
):
    """Get all users"""
    try:
        admin_service = AdminService(db)
        users = await admin_service.get_users()
        return users
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@router.post("/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    try:
        admin_service = AdminService(db)
        new_user = await admin_service.create_user(user)
        return new_user
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.get("/system-health")
async def get_system_health(
    db: Session = Depends(get_db)
):
    """Get system health status"""
    try:
        admin_service = AdminService(db)
        health = await admin_service.get_system_health()
        return health
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking system health: {str(e)}")

@router.post("/reindex")
async def reindex_documents(
    db: Session = Depends(get_db)
):
    """Reindex all documents in the vector database"""
    try:
        admin_service = AdminService(db)
        result = await admin_service.reindex_documents()
        return {"message": "Reindexing completed", "documents_processed": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing documents: {str(e)}")

@router.get("/backup")
async def create_backup(
    db: Session = Depends(get_db)
):
    """Create a backup of the system data"""
    try:
        admin_service = AdminService(db)
        backup_path = await admin_service.create_backup()
        return {"message": "Backup created successfully", "backup_path": backup_path}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating backup: {str(e)}")

