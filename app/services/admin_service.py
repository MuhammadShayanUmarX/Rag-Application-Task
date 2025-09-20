from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import os
import json
from app.db.models import User, Policy, Form, Query
from app.models.schemas import UserCreate, UserResponse, DocumentProcessResponse
from app.services.document_processor import DocumentProcessor

class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.document_processor = DocumentProcessor()
    
    async def get_users(self) -> List[UserResponse]:
        """Get all users"""
        users = self.db.query(User).all()
        return [UserResponse.from_orm(user) for user in users]
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        user = User(
            employee_id=user_data.employee_id,
            name=user_data.name,
            email=user_data.email,
            department=user_data.department,
            role=user_data.role
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return UserResponse.from_orm(user)
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            # Database health
            db_health = "healthy"
            try:
                self.db.execute("SELECT 1")
            except Exception:
                db_health = "unhealthy"
            
            # Vector database health
            vector_health = "healthy"
            try:
                collections = self.document_processor.chroma_client.list_collections()
                vector_health = "healthy" if collections else "no_data"
            except Exception:
                vector_health = "unhealthy"
            
            # Count records
            policy_count = self.db.query(Policy).count()
            form_count = self.db.query(Form).count()
            query_count = self.db.query(Query).count()
            
            # Recent activity
            recent_queries = self.db.query(Query).filter(
                Query.created_at >= datetime.now() - timedelta(hours=24)
            ).count()
            
            return {
                "status": "healthy" if db_health == "healthy" and vector_health == "healthy" else "degraded",
                "database": db_health,
                "vector_database": vector_health,
                "counts": {
                    "policies": policy_count,
                    "forms": form_count,
                    "queries": query_count
                },
                "recent_activity": {
                    "queries_last_24h": recent_queries
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def reindex_documents(self) -> int:
        """Reindex all documents in the vector database"""
        try:
            # Get all policies
            policies = self.db.query(Policy).filter(Policy.is_active == True).all()
            
            # Clear existing vector database
            self.document_processor.chroma_client.delete_collection("hr_policies")
            self.document_processor.collection = self.document_processor.chroma_client.create_collection("hr_policies")
            
            # Reprocess all policies
            processed_count = 0
            for policy in policies:
                result = await self.document_processor.process_document(
                    file_path=f"temp_policy_{policy.id}.txt",
                    category=policy.category,
                    title=policy.title,
                    description=f"Policy: {policy.title}"
                )
                
                if result["success"]:
                    processed_count += 1
                
                # Update policy chunks in database
                await self._update_policy_chunks(policy, result.get("chunk_ids", []))
            
            return processed_count
            
        except Exception as e:
            print(f"Error reindexing documents: {e}")
            return 0
    
    async def _update_policy_chunks(self, policy, chunk_ids: List[str]) -> None:
        """Update policy chunks in database"""
        # Delete existing chunks
        from app.db.models import PolicyChunk
        self.db.query(PolicyChunk).filter(PolicyChunk.policy_id == policy.id).delete()
        
        # Add new chunks
        for i, chunk_id in enumerate(chunk_ids):
            chunk = PolicyChunk(
                policy_id=policy.id,
                content="",  # Content is in vector DB
                chunk_index=i,
                embedding_id=chunk_id
            )
            self.db.add(chunk)
        
        self.db.commit()
    
    async def store_processed_document(self, result: Dict[str, Any]) -> None:
        """Store processed document results in database"""
        try:
            if result["success"]:
                # Create policy record
                policy = Policy(
                    title=result["title"],
                    content="",  # Content is stored in vector DB
                    category=result["category"],
                    version="1.0"
                )
                
                self.db.add(policy)
                self.db.commit()
                self.db.refresh(policy)
                
                # Store chunk references
                for i, chunk_id in enumerate(result.get("chunk_ids", [])):
                    from app.db.models import PolicyChunk
                    chunk = PolicyChunk(
                        policy_id=policy.id,
                        content="",
                        chunk_index=i,
                        embedding_id=chunk_id
                    )
                    self.db.add(chunk)
                
                self.db.commit()
                
        except Exception as e:
            print(f"Error storing processed document: {e}")
    
    async def create_backup(self) -> str:
        """Create a backup of the system data"""
        try:
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"hr_copilot_backup_{timestamp}.json")
            
            # Export data
            backup_data = {
                "policies": [self._serialize_policy(p) for p in self.db.query(Policy).all()],
                "forms": [self._serialize_form(f) for f in self.db.query(Form).all()],
                "users": [self._serialize_user(u) for u in self.db.query(User).all()],
                "queries": [self._serialize_query(q) for q in self.db.query(Query).all()],
                "timestamp": timestamp
            }
            
            with open(backup_path, "w") as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            return backup_path
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return ""
    
    def _serialize_policy(self, policy) -> Dict[str, Any]:
        """Serialize policy for backup"""
        return {
            "id": policy.id,
            "title": policy.title,
            "content": policy.content,
            "category": policy.category,
            "version": policy.version,
            "is_active": policy.is_active,
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
        }
    
    def _serialize_form(self, form) -> Dict[str, Any]:
        """Serialize form for backup"""
        return {
            "id": form.id,
            "name": form.name,
            "description": form.description,
            "file_path": form.file_path,
            "file_url": form.file_url,
            "category": form.category,
            "is_active": form.is_active,
            "created_at": form.created_at.isoformat() if form.created_at else None,
            "updated_at": form.updated_at.isoformat() if form.updated_at else None
        }
    
    def _serialize_user(self, user) -> Dict[str, Any]:
        """Serialize user for backup"""
        return {
            "id": user.id,
            "employee_id": user.employee_id,
            "name": user.name,
            "email": user.email,
            "department": user.department,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    
    def _serialize_query(self, query) -> Dict[str, Any]:
        """Serialize query for backup"""
        return {
            "id": query.id,
            "user_id": query.user_id,
            "question": query.question,
            "answer": query.answer,
            "response_time_ms": query.response_time_ms,
            "confidence_score": query.confidence_score,
            "created_at": query.created_at.isoformat() if query.created_at else None
        }

