from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from app.core.config import settings
from app.db.models import Query, QueryFeedback, QueryForm, Form
from app.services.vector_search import VectorSearchService
from app.services.form_service import FormService
import json

class QueryService:
    def __init__(self, db: Session):
        self.db = db
        self.vector_search = VectorSearchService()
        self.form_service = FormService(db)
        openai.api_key = settings.OPENAI_API_KEY
    
    async def process_query(self, question: str, user_id: str = None, context: str = None) -> Dict[str, Any]:
        """Process a user query and return AI-generated response"""
        try:
            # Search for relevant content
            similar_chunks = await self.vector_search.search_similar_content(question, n_results=5)
            
            if not similar_chunks:
                return {
                    "answer": "I couldn't find relevant information for your question. Please try rephrasing or contact HR for assistance.",
                    "confidence_score": 0.0,
                    "sources": [],
                    "suggested_forms": []
                }
            
            # Prepare context for AI
            context_text = self._prepare_context(similar_chunks, context)
            
            # Generate AI response
            ai_response = await self._generate_ai_response(question, context_text)
            
            # Find relevant forms
            suggested_forms = await self._find_relevant_forms(question, similar_chunks)
            
            # Save query to database
            query_record = await self._save_query(question, ai_response, user_id, similar_chunks)
            
            # Prepare sources
            sources = [chunk['title'] for chunk in similar_chunks if chunk['title']]
            sources = list(set(sources))  # Remove duplicates
            
            return {
                "answer": ai_response['answer'],
                "confidence_score": ai_response['confidence'],
                "sources": sources,
                "suggested_forms": suggested_forms,
                "query_id": query_record.id
            }
            
        except Exception as e:
            print(f"Error processing query: {e}")
            return {
                "answer": "I encountered an error processing your question. Please try again or contact HR for assistance.",
                "confidence_score": 0.0,
                "sources": [],
                "suggested_forms": []
            }
    
    def _prepare_context(self, chunks: List[Dict], additional_context: str = None) -> str:
        """Prepare context from similar chunks"""
        context_parts = []
        
        for chunk in chunks:
            section_info = ""
            if chunk.get('section'):
                section_info = f"Section: {chunk['section']}"
            if chunk.get('subsection'):
                section_info += f" - {chunk['subsection']}"
            
            context_part = f"Source: {chunk['title']}\n"
            if section_info:
                context_part += f"{section_info}\n"
            context_part += f"Content: {chunk['content']}\n"
            
            context_parts.append(context_part)
        
        if additional_context:
            context_parts.append(f"Additional Context: {additional_context}")
        
        return "\n---\n".join(context_parts)
    
    async def _generate_ai_response(self, question: str, context: str) -> Dict[str, Any]:
        """Generate AI response using OpenAI"""
        try:
            prompt = f"""
You are an HR assistant helping employees with policy questions. Use the provided context to answer the question accurately and helpfully.

Context:
{context}

Question: {question}

Instructions:
1. Answer based on the provided context
2. Be specific and cite relevant policy sections when possible
3. If the context doesn't contain enough information, say so clearly
4. Provide actionable guidance when appropriate
5. Be professional and helpful
6. If forms are needed, mention them but don't provide links (those will be handled separately)

Answer:"""

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful HR assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Calculate confidence based on response length and specificity
            confidence = min(0.9, max(0.1, len(answer) / 200))
            
            return {
                "answer": answer,
                "confidence": confidence
            }
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return {
                "answer": "I'm unable to generate a response at the moment. Please contact HR directly for assistance.",
                "confidence": 0.0
            }
    
    async def _find_relevant_forms(self, question: str, chunks: List[Dict]) -> List[Dict[str, Any]]:
        """Find relevant forms based on question and context"""
        try:
            # Extract keywords from question
            keywords = self._extract_keywords(question)
            
            # Get forms from database
            forms = await self.form_service.get_forms()
            
            # Score forms based on keyword matching
            scored_forms = []
            for form in forms:
                score = self._calculate_form_relevance(form, keywords, chunks)
                if score > 0.3:  # Threshold for relevance
                    scored_forms.append({
                        "id": form.id,
                        "name": form.name,
                        "description": form.description,
                        "category": form.category,
                        "file_url": form.file_url,
                        "relevance_score": score
                    })
            
            # Sort by relevance score
            scored_forms.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return scored_forms[:3]  # Return top 3 forms
            
        except Exception as e:
            print(f"Error finding relevant forms: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP
        words = text.lower().split()
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords
    
    def _calculate_form_relevance(self, form, keywords: List[str], chunks: List[Dict]) -> float:
        """Calculate relevance score for a form"""
        score = 0.0
        
        # Check form name and description
        form_text = f"{form.name} {form.description or ''} {form.category}".lower()
        
        # Keyword matching
        for keyword in keywords:
            if keyword in form_text:
                score += 0.1
        
        # Category matching with chunks
        for chunk in chunks:
            if chunk.get('category') == form.category:
                score += 0.2
        
        return min(1.0, score)
    
    async def _save_query(self, question: str, ai_response: Dict, user_id: str, chunks: List[Dict]) -> Query:
        """Save query to database"""
        query_record = Query(
            user_id=user_id,
            question=question,
            answer=ai_response['answer'],
            confidence_score=ai_response['confidence']
        )
        
        self.db.add(query_record)
        self.db.commit()
        self.db.refresh(query_record)
        
        return query_record
    
    async def submit_feedback(self, feedback_data) -> None:
        """Submit feedback for a query"""
        feedback = QueryFeedback(
            query_id=feedback_data.query_id,
            rating=feedback_data.rating,
            is_helpful=feedback_data.is_helpful,
            comments=feedback_data.comments
        )
        
        self.db.add(feedback)
        self.db.commit()
    
    async def get_query_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get query history for a user"""
        queries = self.db.query(Query).filter(
            Query.user_id == user_id
        ).order_by(Query.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": query.id,
                "question": query.question,
                "answer": query.answer,
                "confidence_score": query.confidence_score,
                "created_at": query.created_at.isoformat()
            }
            for query in queries
        ]
