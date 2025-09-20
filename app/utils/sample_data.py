from sqlalchemy.orm import Session
from app.db.models import Policy, Form, User
from app.services.document_processor import DocumentProcessor
import os

async def create_sample_data(db: Session):
    """Create sample data for testing and demonstration"""
    
    # Create sample policies
    sample_policies = [
        {
            "title": "Paid Time Off (PTO) Policy",
            "content": """
            PAID TIME OFF (PTO) POLICY
            
            1. ELIGIBILITY
            All full-time employees are eligible for PTO after completing 90 days of employment.
            Part-time employees accrue PTO on a pro-rated basis.
            
            2. ACCRUAL RATES
            - 0-2 years: 15 days per year
            - 3-5 years: 20 days per year
            - 6+ years: 25 days per year
            
            3. REQUEST PROCESS
            - Submit PTO requests at least 2 weeks in advance
            - Use the online PTO request form
            - Manager approval required
            - Blackout periods may apply during peak business times
            
            4. CARRYOVER
            Up to 5 days may be carried over to the next year.
            Unused PTO beyond 5 days will be forfeited.
            
            5. EMERGENCY LEAVE
            For unexpected situations, contact your manager immediately.
            Emergency leave may be approved retroactively.
            """,
            "category": "PTO"
        },
        {
            "title": "Travel and Expense Reimbursement Policy",
            "content": """
            TRAVEL AND EXPENSE REIMBURSEMENT POLICY
            
            1. ELIGIBLE EXPENSES
            - Airfare (economy class only)
            - Hotel accommodations (up to $200/night)
            - Ground transportation (taxis, rideshare, rental cars)
            - Meals (up to $50/day)
            - Business-related phone calls and internet
            
            2. REQUIRED DOCUMENTATION
            - Original receipts for all expenses
            - Business purpose for each expense
            - Travel dates and destinations
            - Complete expense report form
            
            3. SUBMISSION PROCESS
            - Submit within 30 days of travel
            - Use the online expense reporting system
            - Attach all receipts
            - Manager approval required
            
            4. REIMBURSEMENT TIMELINE
            - Processed within 10 business days of approval
            - Direct deposit to employee's bank account
            - Email notification when processed
            
            5. PROHIBITED EXPENSES
            - Personal entertainment
            - Alcohol (except business dinners)
            - Personal phone calls
            - Upgrades without prior approval
            """,
            "category": "Reimbursement"
        },
        {
            "title": "Remote Work Policy",
            "content": """
            REMOTE WORK POLICY
            
            1. ELIGIBILITY
            Remote work is available for eligible positions with manager approval.
            Employees must have reliable internet and suitable workspace.
            
            2. WORK SCHEDULE
            - Maintain regular business hours
            - Available for meetings and collaboration
            - Respond to communications within 2 hours
            - Track time accurately
            
            3. EQUIPMENT AND TECHNOLOGY
            - Company laptop provided
            - VPN access required
            - Video conferencing capabilities
            - Secure file sharing protocols
            
            4. PERFORMANCE EXPECTATIONS
            - Meet all job requirements
            - Maintain productivity levels
            - Regular check-ins with manager
            - Complete all assigned tasks on time
            
            5. WORKSPACE REQUIREMENTS
            - Quiet, professional environment
            - Adequate lighting for video calls
            - Secure storage for company materials
            - Backup internet connection recommended
            """,
            "category": "General"
        }
    ]
    
    # Create sample forms
    sample_forms = [
        {
            "name": "PTO Request Form",
            "description": "Request paid time off using this form",
            "category": "PTO",
            "file_url": "/forms/pto-request.pdf"
        },
        {
            "name": "Expense Report Form",
            "description": "Submit travel and business expenses for reimbursement",
            "category": "Reimbursement",
            "file_url": "/forms/expense-report.pdf"
        },
        {
            "name": "Remote Work Agreement",
            "description": "Agreement for remote work arrangements",
            "category": "General",
            "file_url": "/forms/remote-work-agreement.pdf"
        },
        {
            "name": "Benefits Enrollment Form",
            "description": "Enroll in company benefits programs",
            "category": "Benefits",
            "file_url": "/forms/benefits-enrollment.pdf"
        }
    ]
    
    # Create sample users
    sample_users = [
        {
            "employee_id": "EMP001",
            "name": "John Smith",
            "email": "john.smith@company.com",
            "department": "Engineering",
            "role": "Software Engineer"
        },
        {
            "employee_id": "EMP002",
            "name": "Sarah Johnson",
            "email": "sarah.johnson@company.com",
            "department": "HR",
            "role": "HR Manager"
        },
        {
            "employee_id": "EMP003",
            "name": "Mike Davis",
            "email": "mike.davis@company.com",
            "department": "Sales",
            "role": "Sales Manager"
        }
    ]
    
    # Add policies to database
    for policy_data in sample_policies:
        policy = Policy(
            title=policy_data["title"],
            content=policy_data["content"],
            category=policy_data["category"],
            version="1.0",
            is_active=True
        )
        db.add(policy)
    
    # Add forms to database
    for form_data in sample_forms:
        form = Form(
            name=form_data["name"],
            description=form_data["description"],
            category=form_data["category"],
            file_url=form_data["file_url"],
            is_active=True
        )
        db.add(form)
    
    # Add users to database
    for user_data in sample_users:
        user = User(
            employee_id=user_data["employee_id"],
            name=user_data["name"],
            email=user_data["email"],
            department=user_data["department"],
            role=user_data["role"],
            is_active=True
        )
        db.add(user)
    
    db.commit()
    
    # Process policies into vector database
    processor = DocumentProcessor()
    policies = db.query(Policy).all()
    
    for policy in policies:
        # Create temporary file for processing
        temp_file = f"temp_policy_{policy.id}.txt"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(policy.content)
        
        # Process the document
        result = await processor.process_document(
            file_path=temp_file,
            category=policy.category,
            title=policy.title,
            description=f"Policy: {policy.title}"
        )
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    print("Sample data created successfully!")

async def clear_sample_data(db: Session):
    """Clear all sample data"""
    from app.db.models import Policy, Form, User, PolicyChunk, Query, QueryFeedback
    
    # Clear all data
    db.query(QueryFeedback).delete()
    db.query(Query).delete()
    db.query(PolicyChunk).delete()
    db.query(Policy).delete()
    db.query(Form).delete()
    db.query(User).delete()
    
    db.commit()
    print("Sample data cleared!")

