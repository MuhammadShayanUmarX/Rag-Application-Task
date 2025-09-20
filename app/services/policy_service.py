from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models import Policy, PolicyChunk
from app.models.schemas import PolicyCreate, PolicyResponse, PolicyChunkResponse
from app.services.document_processor import DocumentProcessor

class PolicyService:
    def __init__(self, db: Session):
        self.db = db
        self.document_processor = DocumentProcessor()
    
    async def get_policies(self, category: str = None, is_active: bool = True) -> List[PolicyResponse]:
        """Get all policies with optional filtering"""
        query = self.db.query(Policy).filter(Policy.is_active == is_active)
        
        if category:
            query = query.filter(Policy.category == category)
        
        policies = query.all()
        return [PolicyResponse.from_orm(policy) for policy in policies]
    
    async def get_policy(self, policy_id: int) -> Optional[PolicyResponse]:
        """Get a specific policy by ID"""
        policy = self.db.query(Policy).filter(Policy.id == policy_id).first()
        if policy:
            return PolicyResponse.from_orm(policy)
        return None
    
    async def create_policy(self, policy_data: PolicyCreate) -> PolicyResponse:
        """Create a new policy"""
        policy = Policy(
            title=policy_data.title,
            content=policy_data.content,
            category=policy_data.category,
            version=policy_data.version,
            is_active=policy_data.is_active
        )
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        # Process the policy content into chunks
        await self._process_policy_chunks(policy)
        
        return PolicyResponse.from_orm(policy)
    
    async def update_policy(self, policy_id: int, policy_data: PolicyCreate) -> Optional[PolicyResponse]:
        """Update an existing policy"""
        policy = self.db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            return None
        
        policy.title = policy_data.title
        policy.content = policy_data.content
        policy.category = policy_data.category
        policy.version = policy_data.version
        policy.is_active = policy_data.is_active
        
        self.db.commit()
        self.db.refresh(policy)
        
        # Reprocess chunks if content changed
        if policy.content != policy_data.content:
            await self._reprocess_policy_chunks(policy)
        
        return PolicyResponse.from_orm(policy)
    
    async def delete_policy(self, policy_id: int) -> bool:
        """Soft delete a policy"""
        policy = self.db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            return False
        
        policy.is_active = False
        self.db.commit()
        return True
    
    async def get_policy_chunks(self, policy_id: int) -> List[PolicyChunkResponse]:
        """Get chunks for a specific policy"""
        chunks = self.db.query(PolicyChunk).filter(
            PolicyChunk.policy_id == policy_id
        ).order_by(PolicyChunk.chunk_index).all()
        
        return [PolicyChunkResponse.from_orm(chunk) for chunk in chunks]
    
    async def _process_policy_chunks(self, policy: Policy) -> None:
        """Process policy content into searchable chunks"""
        try:
            # Create a temporary file for processing
            temp_file = f"temp_policy_{policy.id}.txt"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(policy.content)
            
            # Process the document
            result = await self.document_processor.process_document(
                file_path=temp_file,
                category=policy.category,
                title=policy.title,
                description=f"Policy: {policy.title}"
            )
            
            if result["success"]:
                # Store chunk references in database
                for i, chunk_id in enumerate(result.get("chunk_ids", [])):
                    chunk = PolicyChunk(
                        policy_id=policy.id,
                        content="",  # Content is stored in vector DB
                        chunk_index=i,
                        embedding_id=chunk_id
                    )
                    self.db.add(chunk)
                
                self.db.commit()
            
            # Clean up temp file
            import os
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        except Exception as e:
            print(f"Error processing policy chunks: {e}")
    
    async def _reprocess_policy_chunks(self, policy: Policy) -> None:
        """Reprocess policy chunks after content update"""
        # Delete existing chunks
        self.db.query(PolicyChunk).filter(PolicyChunk.policy_id == policy.id).delete()
        self.db.commit()
        
        # Process new chunks
        await self._process_policy_chunks(policy)
