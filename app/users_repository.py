from attrs import define

from sqlalchemy import Boolean, Integer, String, Column, ForeignKey
from sqlalchemy.orm import relationship, Session

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    password = Column(String)

    
@define
class UserCreate:
    email: str
    full_name: str
    password: str


class UsersRepository:

    # необходимые методы сюда

    def get_all(self, db: Session, skip: int = 0, limit: int = 10):
        return db.query(User).offset(skip).limit(limit).all()
    
    def get_by_email(self, db: Session, user_email: str):
        return db.query(User).filter(User.email == user_email).first()
    
    def get_by_id(self, db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    def save_user(self, db: Session, user: UserCreate):
        db_user = User(email=user.email, full_name =user.full_name, password=user.password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    # конец решения
