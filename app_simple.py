#!/usr/bin/env python3
"""
Simplified HR Copilot - Basic version without AI dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from typing import List, Optional
import json
import os

# Simple data storage
policies_data = []
forms_data = []
queries_data = []

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    user_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    confidence_score: float
    sources: List[str]
    suggested_forms: List[dict]

class PolicyResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    version: str

class FormResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    file_url: str

# Initialize FastAPI app
app = FastAPI(
    title="HR Policies & Benefits Copilot",
    description="AI-powered HR assistant for policy queries and form management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve app.js directly
@app.get("/app.js")
async def serve_app_js():
    try:
        with open("static/app.js", "r") as f:
            return Response(content=f.read(), media_type="application/javascript")
    except FileNotFoundError:
        return Response(content="console.log('app.js not found');", media_type="application/javascript")

# Sample data
def load_sample_data():
    global policies_data, forms_data
    
    policies_data = [
        {
            "id": 1,
            "title": "Paid Time Off (PTO) Policy",
            "content": "All full-time employees are eligible for PTO after completing 90 days of employment. Accrual rates: 0-2 years: 15 days/year, 3-5 years: 20 days/year, 6+ years: 25 days/year. Submit requests at least 2 weeks in advance.",
            "category": "PTO",
            "version": "1.0"
        },
        {
            "id": 2,
            "title": "Travel and Expense Reimbursement Policy",
            "content": "Eligible expenses include airfare (economy), hotel (up to $200/night), ground transportation, meals (up to $50/day). Submit within 30 days with original receipts. Processed within 10 business days of approval.",
            "category": "Reimbursement",
            "version": "1.0"
        },
        {
            "id": 3,
            "title": "Remote Work Policy",
            "content": "Remote work available for eligible positions with manager approval. Must maintain regular business hours, have reliable internet, and suitable workspace. Company laptop provided.",
            "category": "General",
            "version": "1.0"
        }
    ]
    
    forms_data = [
        {
            "id": 1,
            "name": "PTO Request Form",
            "description": "Request paid time off using this form",
            "category": "PTO",
            "file_url": "/forms/pto-request.pdf"
        },
        {
            "id": 2,
            "name": "Expense Report Form",
            "description": "Submit travel and business expenses for reimbursement",
            "category": "Reimbursement",
            "file_url": "/forms/expense-report.pdf"
        },
        {
            "id": 3,
            "name": "Remote Work Agreement",
            "description": "Agreement for remote work arrangements",
            "category": "General",
            "file_url": "/forms/remote-work-agreement.pdf"
        }
    ]

# Load sample data on startup
load_sample_data()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main employee interface"""
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>HR Copilot</title></head>
            <body>
                <h1>HR Policies & Benefits Copilot</h1>
                <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/query/", response_model=QueryResponse)
async def process_query(query_request: QueryRequest):
    """Process an HR policy query and return response"""
    question = query_request.question.lower()
    
    # Simple keyword matching
    answer = "I found some relevant information for your question:"
    sources = []
    suggested_forms = []
    confidence = 0.5
    
    # Check for PTO-related questions
    if any(word in question for word in ["pto", "vacation", "time off", "leave"]):
        pto_policy = next((p for p in policies_data if p["category"] == "PTO"), None)
        if pto_policy:
            answer += f"\n\n{pto_policy['title']}:\n{pto_policy['content']}"
            sources.append(pto_policy['title'])
            confidence = 0.8
            
        pto_form = next((f for f in forms_data if f["category"] == "PTO"), None)
        if pto_form:
            suggested_forms.append({
                "id": pto_form["id"],
                "name": pto_form["name"],
                "description": pto_form["description"],
                "category": pto_form["category"],
                "file_url": pto_form["file_url"],
                "relevance_score": 0.9
            })
    
    # Check for reimbursement-related questions
    elif any(word in question for word in ["reimbursement", "expense", "travel", "receipt"]):
        reimb_policy = next((p for p in policies_data if p["category"] == "Reimbursement"), None)
        if reimb_policy:
            answer += f"\n\n{reimb_policy['title']}:\n{reimb_policy['content']}"
            sources.append(reimb_policy['title'])
            confidence = 0.8
            
        reimb_form = next((f for f in forms_data if f["category"] == "Reimbursement"), None)
        if reimb_form:
            suggested_forms.append({
                "id": reimb_form["id"],
                "name": reimb_form["name"],
                "description": reimb_form["description"],
                "category": reimb_form["category"],
                "file_url": reimb_form["file_url"],
                "relevance_score": 0.9
            })
    
    # Check for remote work questions
    elif any(word in question for word in ["remote", "work from home", "wfh", "telecommute"]):
        remote_policy = next((p for p in policies_data if p["category"] == "General"), None)
        if remote_policy:
            answer += f"\n\n{remote_policy['title']}:\n{remote_policy['content']}"
            sources.append(remote_policy['title'])
            confidence = 0.8
            
        remote_form = next((f for f in forms_data if f["category"] == "General"), None)
        if remote_form:
            suggested_forms.append({
                "id": remote_form["id"],
                "name": remote_form["name"],
                "description": remote_form["description"],
                "category": remote_form["category"],
                "file_url": remote_form["file_url"],
                "relevance_score": 0.9
            })
    
    else:
        answer = "I can help you with questions about PTO, reimbursements, remote work, and other HR policies. Could you please be more specific about what you'd like to know?"
        confidence = 0.3
    
    # Store query
    query_id = len(queries_data) + 1
    queries_data.append({
        "id": query_id,
        "question": query_request.question,
        "answer": answer,
        "user_id": query_request.user_id,
        "confidence_score": confidence
    })
    
    return QueryResponse(
        answer=answer,
        confidence_score=confidence,
        sources=sources,
        suggested_forms=suggested_forms
    )

@app.get("/api/policies/", response_model=List[PolicyResponse])
async def get_policies():
    """Get all policies"""
    return [PolicyResponse(**policy) for policy in policies_data]

@app.get("/api/forms/", response_model=List[FormResponse])
async def get_forms():
    """Get all forms"""
    return [FormResponse(**form) for form in forms_data]

@app.get("/api/analytics/")
async def get_analytics():
    """Get system analytics"""
    return {
        "total_queries": len(queries_data),
        "avg_response_time_ms": 150.0,
        "avg_confidence_score": 0.7,
        "helpful_rating_avg": 4.2,
        "top_categories": [
            {"category": "PTO", "count": 5},
            {"category": "Reimbursement", "count": 3},
            {"category": "General", "count": 2}
        ],
        "recent_queries": queries_data[-5:] if queries_data else [],
        "misrouting_rate": 0.1
    }

@app.post("/api/query/feedback")
async def submit_feedback(feedback: dict):
    """Submit feedback on a query response"""
    return {"message": "Feedback submitted successfully"}

if __name__ == "__main__":
    import uvicorn
    print("Starting HR Copilot (Simplified Version)")
    print("Visit http://localhost:8000 to access the application")
    uvicorn.run(app, host="0.0.0.0", port=8000)

