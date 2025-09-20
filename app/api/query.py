from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import time

from app.db.database import get_db
from app.models.schemas import QueryRequest, QueryResponse, QueryFeedbackRequest
from app.services.query_service import QueryService
from app.services.vector_search import VectorSearchService

router = APIRouter()

@router.post("/", response_model=QueryResponse)
async def process_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Process an HR policy query and return AI-generated response"""
    try:
        start_time = time.time()
        
        # Initialize services
        query_service = QueryService(db)
        vector_search = VectorSearchService()
        
        # Process the query
        result = await query_service.process_query(
            question=query_request.question,
            user_id=query_request.user_id,
            context=query_request.context
        )
        
        response_time = int((time.time() - start_time) * 1000)
        
        return QueryResponse(
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            sources=result["sources"],
            suggested_forms=result["suggested_forms"],
            response_time_ms=response_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.post("/feedback")
async def submit_feedback(
    feedback: QueryFeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit feedback on a query response"""
    try:
        query_service = QueryService(db)
        await query_service.submit_feedback(feedback)
        return {"message": "Feedback submitted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@router.get("/history/{user_id}")
async def get_query_history(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get query history for a user"""
    try:
        query_service = QueryService(db)
        history = await query_service.get_query_history(user_id, limit)
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching query history: {str(e)}")

