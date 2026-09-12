from sqlalchemy.orm import Session
from src.db.schemas.app.prompts import Prompt


class PromptRepository:
    """Repository for prompt operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_name(self, name: str):
        """Get prompt by name."""
        return self.session.query(Prompt).filter_by(name=name).first()

    def create(self, name: str, template: str, version: str = "1.0"):
        """Create a new prompt."""
        from src.db.schemas.app.prompts import Prompt as PromptModel
        prompt = PromptModel(name=name, template=template, version=version)
        self.session.add(prompt)
        self.session.flush()
        return prompt

    def get_active(self):
        """Get all active prompts."""
        return self.session.query(Prompt).filter_by(is_active=True).all()

    def deactivate(self, name: str):
        """Deactivate a prompt."""
        prompt = self.get_by_name(name)
        if prompt:
            prompt.is_active = False
            self.session.flush()