from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.schemas import FormCreate, FormResponse, PolicyFormLink
from app.services.form_service import FormService

router = APIRouter()

@router.get("/", response_model=List[FormResponse])
async def get_forms(
    category: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Get all forms, optionally filtered by category"""
    try:
        form_service = FormService(db)
        forms = await form_service.get_forms(category, is_active)
        return forms
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forms: {str(e)}")

@router.get("/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific form by ID"""
    try:
        form_service = FormService(db)
        form = await form_service.get_form(form_id)
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        return form
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching form: {str(e)}")

@router.post("/", response_model=FormResponse)
async def create_form(
    form: FormCreate,
    db: Session = Depends(get_db)
):
    """Create a new form"""
    try:
        form_service = FormService(db)
        new_form = await form_service.create_form(form)
        return new_form
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating form: {str(e)}")

@router.put("/{form_id}", response_model=FormResponse)
async def update_form(
    form_id: int,
    form: FormCreate,
    db: Session = Depends(get_db)
):
    """Update an existing form"""
    try:
        form_service = FormService(db)
        updated_form = await form_service.update_form(form_id, form)
        if not updated_form:
            raise HTTPException(status_code=404, detail="Form not found")
        return updated_form
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating form: {str(e)}")

@router.delete("/{form_id}")
async def delete_form(
    form_id: int,
    db: Session = Depends(get_db)
):
    """Delete a form (soft delete)"""
    try:
        form_service = FormService(db)
        success = await form_service.delete_form(form_id)
        if not success:
            raise HTTPException(status_code=404, detail="Form not found")
        return {"message": "Form deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting form: {str(e)}")

@router.post("/link-policy")
async def link_form_to_policy(
    link: PolicyFormLink,
    db: Session = Depends(get_db)
):
    """Link a form to a policy"""
    try:
        form_service = FormService(db)
        success = await form_service.link_form_to_policy(link)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to link form to policy")
        return {"message": "Form linked to policy successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error linking form to policy: {str(e)}")

@router.get("/by-policy/{policy_id}", response_model=List[FormResponse])
async def get_forms_by_policy(
    policy_id: int,
    db: Session = Depends(get_db)
):
    """Get forms linked to a specific policy"""
    try:
        form_service = FormService(db)
        forms = await form_service.get_forms_by_policy(policy_id)
        return forms
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forms by policy: {str(e)}")

