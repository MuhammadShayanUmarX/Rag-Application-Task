from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models import Form, PolicyForm
from app.models.schemas import FormCreate, FormResponse, PolicyFormLink

class FormService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_forms(self, category: str = None, is_active: bool = True) -> List[FormResponse]:
        """Get all forms with optional filtering"""
        query = self.db.query(Form).filter(Form.is_active == is_active)
        
        if category:
            query = query.filter(Form.category == category)
        
        forms = query.all()
        return [FormResponse.from_orm(form) for form in forms]
    
    async def get_form(self, form_id: int) -> Optional[FormResponse]:
        """Get a specific form by ID"""
        form = self.db.query(Form).filter(Form.id == form_id).first()
        if form:
            return FormResponse.from_orm(form)
        return None
    
    async def create_form(self, form_data: FormCreate) -> FormResponse:
        """Create a new form"""
        form = Form(
            name=form_data.name,
            description=form_data.description,
            file_path=form_data.file_path,
            file_url=form_data.file_url,
            category=form_data.category,
            is_active=form_data.is_active
        )
        
        self.db.add(form)
        self.db.commit()
        self.db.refresh(form)
        
        return FormResponse.from_orm(form)
    
    async def update_form(self, form_id: int, form_data: FormCreate) -> Optional[FormResponse]:
        """Update an existing form"""
        form = self.db.query(Form).filter(Form.id == form_id).first()
        if not form:
            return None
        
        form.name = form_data.name
        form.description = form_data.description
        form.file_path = form_data.file_path
        form.file_url = form_data.file_url
        form.category = form_data.category
        form.is_active = form_data.is_active
        
        self.db.commit()
        self.db.refresh(form)
        
        return FormResponse.from_orm(form)
    
    async def delete_form(self, form_id: int) -> bool:
        """Soft delete a form"""
        form = self.db.query(Form).filter(Form.id == form_id).first()
        if not form:
            return False
        
        form.is_active = False
        self.db.commit()
        return True
    
    async def link_form_to_policy(self, link_data: PolicyFormLink) -> bool:
        """Link a form to a policy"""
        try:
            # Check if link already exists
            existing_link = self.db.query(PolicyForm).filter(
                PolicyForm.policy_id == link_data.policy_id,
                PolicyForm.form_id == link_data.form_id
            ).first()
            
            if existing_link:
                # Update existing link
                existing_link.relevance_score = link_data.relevance_score
            else:
                # Create new link
                policy_form = PolicyForm(
                    policy_id=link_data.policy_id,
                    form_id=link_data.form_id,
                    relevance_score=link_data.relevance_score
                )
                self.db.add(policy_form)
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"Error linking form to policy: {e}")
            return False
    
    async def get_forms_by_policy(self, policy_id: int) -> List[FormResponse]:
        """Get forms linked to a specific policy"""
        forms = self.db.query(Form).join(PolicyForm).filter(
            PolicyForm.policy_id == policy_id,
            Form.is_active == True
        ).all()
        
        return [FormResponse.from_orm(form) for form in forms]
    
    async def get_policies_by_form(self, form_id: int) -> List[int]:
        """Get policy IDs linked to a specific form"""
        policy_forms = self.db.query(PolicyForm).filter(
            PolicyForm.form_id == form_id
        ).all()
        
        return [pf.policy_id for pf in policy_forms]
    
    async def search_forms(self, query: str, category: str = None) -> List[FormResponse]:
        """Search forms by name, description, or category"""
        search_query = self.db.query(Form).filter(Form.is_active == True)
        
        if query:
            search_query = search_query.filter(
                Form.name.ilike(f"%{query}%") |
                Form.description.ilike(f"%{query}%")
            )
        
        if category:
            search_query = search_query.filter(Form.category == category)
        
        forms = search_query.all()
        return [FormResponse.from_orm(form) for form in forms]
