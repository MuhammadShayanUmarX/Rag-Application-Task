from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.schemas import PolicyCreate, PolicyResponse, PolicyChunkResponse
from app.services.policy_service import PolicyService

router = APIRouter()

@router.get("/", response_model=List[PolicyResponse])
async def get_policies(
    category: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Get all policies, optionally filtered by category"""
    try:
        policy_service = PolicyService(db)
        policies = await policy_service.get_policies(category, is_active)
        return policies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching policies: {str(e)}")

@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific policy by ID"""
    try:
        policy_service = PolicyService(db)
        policy = await policy_service.get_policy(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching policy: {str(e)}")

@router.post("/", response_model=PolicyResponse)
async def create_policy(
    policy: PolicyCreate,
    db: Session = Depends(get_db)
):
    """Create a new policy"""
    try:
        policy_service = PolicyService(db)
        new_policy = await policy_service.create_policy(policy)
        return new_policy
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating policy: {str(e)}")

@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: int,
    policy: PolicyCreate,
    db: Session = Depends(get_db)
):
    """Update an existing policy"""
    try:
        policy_service = PolicyService(db)
        updated_policy = await policy_service.update_policy(policy_id, policy)
        if not updated_policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        return updated_policy
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating policy: {str(e)}")

@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: int,
    db: Session = Depends(get_db)
):
    """Delete a policy (soft delete)"""
    try:
        policy_service = PolicyService(db)
        success = await policy_service.delete_policy(policy_id)
        if not success:
            raise HTTPException(status_code=404, detail="Policy not found")
        return {"message": "Policy deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting policy: {str(e)}")

@router.get("/{policy_id}/chunks", response_model=List[PolicyChunkResponse])
async def get_policy_chunks(
    policy_id: int,
    db: Session = Depends(get_db)
):
    """Get chunks for a specific policy"""
    try:
        policy_service = PolicyService(db)
        chunks = await policy_service.get_policy_chunks(policy_id)
        return chunks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching policy chunks: {str(e)}")

