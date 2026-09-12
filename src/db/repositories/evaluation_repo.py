from sqlalchemy.orm import Session
from src.db.schemas.app.evaluations import Evaluation


class EvaluationRepository:
    """Repository for evaluation operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, prompt_id: str = None, document_id: str = None):
        """Create a new evaluation."""
        from src.db.schemas.app.evaluations import Evaluation as EvalModel
        evaluation = EvalModel(name=name, prompt_id=prompt_id, document_id=document_id)
        self.session.add(evaluation)
        self.session.flush()
        return evaluation

    def get_by_document(self, document_id: str):
        """Get evaluation by document_id."""
        return self.session.query(Evaluation).filter_by(document_id=document_id).first()

    def get_passed(self):
        """Get passed evaluations."""
        return self.session.query(Evaluation).filter(Evaluation.passed == True).all()