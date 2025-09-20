from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Query Models
class QueryRequest(BaseModel):
    question: str
    user_id: Optional[str] = None
    context: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    confidence_score: float
    sources: List[str]
    suggested_forms: List['FormResponse']
    response_time_ms: int

class QueryFeedbackRequest(BaseModel):
    query_id: int
    rating: int  # 1-5 scale
    is_helpful: bool
    comments: Optional[str] = None

# Policy Models
class PolicyBase(BaseModel):
    title: str
    content: str
    category: str
    version: str = "1.0"
    is_active: bool = True

class PolicyCreate(PolicyBase):
    pass

class PolicyResponse(PolicyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PolicyChunkResponse(BaseModel):
    id: int
    content: str
    chunk_index: int
    policy_id: int
    
    class Config:
        from_attributes = True

# Form Models
class FormBase(BaseModel):
    name: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    category: str
    is_active: bool = True

class FormCreate(FormBase):
    pass

class FormResponse(FormBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PolicyFormLink(BaseModel):
    policy_id: int
    form_id: int
    relevance_score: float = 1.0

# Analytics Models
class AnalyticsResponse(BaseModel):
    total_queries: int
    avg_response_time_ms: float
    avg_confidence_score: float
    helpful_rating_avg: float
    top_categories: List[dict]
    recent_queries: List[dict]
    misrouting_rate: float

class QueryAnalytics(BaseModel):
    query_id: int
    question: str
    answer: str
    response_time_ms: int
    confidence_score: float
    rating: Optional[int] = None
    is_helpful: Optional[bool] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# User Models
class UserBase(BaseModel):
    employee_id: str
    name: str
    email: str
    department: Optional[str] = None
    role: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Document Processing Models
class DocumentUpload(BaseModel):
    file_path: str
    category: str
    title: str
    description: Optional[str] = None

class DocumentProcessResponse(BaseModel):
    success: bool
    chunks_created: int
    message: str

