from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.db.models import Query, QueryFeedback, Policy, Form
from app.models.schemas import AnalyticsResponse, QueryAnalytics

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_analytics(self, days: int = 30) -> AnalyticsResponse:
        """Get comprehensive system analytics"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Total queries
        total_queries = self.db.query(Query).filter(
            Query.created_at >= start_date
        ).count()
        
        # Average response time
        avg_response_time = self.db.query(func.avg(Query.response_time_ms)).filter(
            Query.created_at >= start_date,
            Query.response_time_ms.isnot(None)
        ).scalar() or 0
        
        # Average confidence score
        avg_confidence = self.db.query(func.avg(Query.confidence_score)).filter(
            Query.created_at >= start_date,
            Query.confidence_score.isnot(None)
        ).scalar() or 0
        
        # Average helpful rating
        avg_rating = self.db.query(func.avg(QueryFeedback.rating)).join(Query).filter(
            Query.created_at >= start_date,
            QueryFeedback.rating.isnot(None)
        ).scalar() or 0
        
        # Top categories (based on policy categories)
        top_categories = self.db.query(
            Policy.category,
            func.count(Query.id).label('query_count')
        ).join(Query, Query.question.ilike(f"%{Policy.category}%")).filter(
            Query.created_at >= start_date
        ).group_by(Policy.category).order_by(desc('query_count')).limit(5).all()
        
        # Recent queries
        recent_queries = self.db.query(Query).filter(
            Query.created_at >= start_date
        ).order_by(desc(Query.created_at)).limit(10).all()
        
        recent_queries_data = [
            {
                "id": q.id,
                "question": q.question[:100] + "..." if len(q.question) > 100 else q.question,
                "confidence_score": q.confidence_score,
                "created_at": q.created_at.isoformat()
            }
            for q in recent_queries
        ]
        
        # Misrouting rate (queries with low confidence or negative feedback)
        low_confidence_queries = self.db.query(Query).filter(
            Query.created_at >= start_date,
            Query.confidence_score < 0.5
        ).count()
        
        negative_feedback = self.db.query(QueryFeedback).join(Query).filter(
            Query.created_at >= start_date,
            QueryFeedback.is_helpful == False
        ).count()
        
        misrouting_rate = 0
        if total_queries > 0:
            misrouting_rate = (low_confidence_queries + negative_feedback) / (total_queries * 2)
        
        return AnalyticsResponse(
            total_queries=total_queries,
            avg_response_time_ms=float(avg_response_time),
            avg_confidence_score=float(avg_confidence),
            helpful_rating_avg=float(avg_rating),
            top_categories=[{"category": cat, "count": count} for cat, count in top_categories],
            recent_queries=recent_queries_data,
            misrouting_rate=float(misrouting_rate)
        )
    
    async def get_query_analytics(self, limit: int = 100, offset: int = 0, 
                                 start_date: Optional[datetime] = None, 
                                 end_date: Optional[datetime] = None) -> List[QueryAnalytics]:
        """Get detailed query analytics"""
        query = self.db.query(Query)
        
        if start_date:
            query = query.filter(Query.created_at >= start_date)
        if end_date:
            query = query.filter(Query.created_at <= end_date)
        
        queries = query.order_by(desc(Query.created_at)).offset(offset).limit(limit).all()
        
        # Get feedback for each query
        query_ids = [q.id for q in queries]
        feedback_data = self.db.query(QueryFeedback).filter(
            QueryFeedback.query_id.in_(query_ids)
        ).all()
        
        feedback_map = {f.query_id: f for f in feedback_data}
        
        return [
            QueryAnalytics(
                query_id=q.id,
                question=q.question,
                answer=q.answer,
                response_time_ms=q.response_time_ms or 0,
                confidence_score=q.confidence_score or 0.0,
                rating=feedback_map.get(q.id).rating if feedback_map.get(q.id) else None,
                is_helpful=feedback_map.get(q.id).is_helpful if feedback_map.get(q.id) else None,
                created_at=q.created_at
            )
            for q in queries
        ]
    
    async def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get performance metrics"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Response time metrics
        response_times = self.db.query(Query.response_time_ms).filter(
            Query.created_at >= start_date,
            Query.response_time_ms.isnot(None)
        ).all()
        
        response_times_list = [rt[0] for rt in response_times]
        
        # Confidence score metrics
        confidence_scores = self.db.query(Query.confidence_score).filter(
            Query.created_at >= start_date,
            Query.confidence_score.isnot(None)
        ).all()
        
        confidence_list = [cs[0] for cs in confidence_scores]
        
        # Feedback metrics
        feedback_data = self.db.query(QueryFeedback).join(Query).filter(
            Query.created_at >= start_date
        ).all()
        
        helpful_count = sum(1 for f in feedback_data if f.is_helpful)
        total_feedback = len(feedback_data)
        
        return {
            "response_time": {
                "avg": sum(response_times_list) / len(response_times_list) if response_times_list else 0,
                "min": min(response_times_list) if response_times_list else 0,
                "max": max(response_times_list) if response_times_list else 0,
                "count": len(response_times_list)
            },
            "confidence": {
                "avg": sum(confidence_list) / len(confidence_list) if confidence_list else 0,
                "min": min(confidence_list) if confidence_list else 0,
                "max": max(confidence_list) if confidence_list else 0,
                "count": len(confidence_list)
            },
            "feedback": {
                "helpful_rate": helpful_count / total_feedback if total_feedback > 0 else 0,
                "total_feedback": total_feedback,
                "helpful_count": helpful_count
            }
        }
    
    async def get_category_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics by policy category"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Get all categories
        categories = self.db.query(Policy.category).distinct().all()
        category_list = [cat[0] for cat in categories]
        
        category_stats = {}
        
        for category in category_list:
            # Count queries mentioning this category
            query_count = self.db.query(Query).filter(
                Query.created_at >= start_date,
                Query.question.ilike(f"%{category}%")
            ).count()
            
            # Average confidence for this category
            avg_confidence = self.db.query(func.avg(Query.confidence_score)).filter(
                Query.created_at >= start_date,
                Query.question.ilike(f"%{category}%"),
                Query.confidence_score.isnot(None)
            ).scalar() or 0
            
            # Feedback for this category
            feedback_count = self.db.query(QueryFeedback).join(Query).filter(
                Query.created_at >= start_date,
                Query.question.ilike(f"%{category}%")
            ).count()
            
            helpful_count = self.db.query(QueryFeedback).join(Query).filter(
                Query.created_at >= start_date,
                Query.question.ilike(f"%{category}%"),
                QueryFeedback.is_helpful == True
            ).count()
            
            category_stats[category] = {
                "query_count": query_count,
                "avg_confidence": float(avg_confidence),
                "feedback_count": feedback_count,
                "helpful_rate": helpful_count / feedback_count if feedback_count > 0 else 0
            }
        
        return category_stats
    
    async def get_misrouting_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get misrouting analysis and suggestions"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Queries with low confidence
        low_confidence = self.db.query(Query).filter(
            Query.created_at >= start_date,
            Query.confidence_score < 0.5
        ).all()
        
        # Queries with negative feedback
        negative_feedback = self.db.query(Query).join(QueryFeedback).filter(
            Query.created_at >= start_date,
            QueryFeedback.is_helpful == False
        ).all()
        
        # Common patterns in misrouted queries
        low_confidence_patterns = {}
        for query in low_confidence:
            words = query.question.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    low_confidence_patterns[word] = low_confidence_patterns.get(word, 0) + 1
        
        # Sort patterns by frequency
        common_patterns = sorted(low_confidence_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "low_confidence_queries": len(low_confidence),
            "negative_feedback_queries": len(negative_feedback),
            "common_problem_patterns": [{"pattern": pattern, "count": count} for pattern, count in common_patterns],
            "suggestions": [
                "Consider adding more specific policy content for common query patterns",
                "Review and improve policy documentation for unclear areas",
                "Add more examples and use cases to policy descriptions"
            ]
        }
