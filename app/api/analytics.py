from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.db.database import get_db
from app.models.schemas import AnalyticsResponse, QueryAnalytics
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get system analytics and KPIs"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = await analytics_service.get_analytics(days)
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")

@router.get("/queries", response_model=list[QueryAnalytics])
async def get_query_analytics(
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get detailed query analytics"""
    try:
        analytics_service = AnalyticsService(db)
        queries = await analytics_service.get_query_analytics(
            limit, offset, start_date, end_date
        )
        return queries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching query analytics: {str(e)}")

@router.get("/performance")
async def get_performance_metrics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get performance metrics including response times and accuracy"""
    try:
        analytics_service = AnalyticsService(db)
        metrics = await analytics_service.get_performance_metrics(days)
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching performance metrics: {str(e)}")

@router.get("/categories")
async def get_category_analytics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get analytics by policy category"""
    try:
        analytics_service = AnalyticsService(db)
        categories = await analytics_service.get_category_analytics(days)
        return categories
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category analytics: {str(e)}")

@router.get("/misrouting")
async def get_misrouting_analysis(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get misrouting analysis and suggestions"""
    try:
        analytics_service = AnalyticsService(db)
        analysis = await analytics_service.get_misrouting_analysis(days)
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching misrouting analysis: {str(e)}")

