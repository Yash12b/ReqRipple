from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.security import hash_password, verify_password, create_access_token
from app.core.errors import EntityConflictError, AuthenticationError


class AuthService:
    @staticmethod
    def register(db: Session, data: UserRegister) -> dict:
        existing = db.query(User).filter(User.email == data.email.lower()).first()
        if existing:
            raise EntityConflictError(f"A user with email '{data.email}' already exists.")

        user = User(
            email=data.email.lower(),
            name=data.name,
            password_hash=hash_password(data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(user.id)
        return {"user": user, "access_token": token, "token_type": "bearer"}

    @staticmethod
    def login(db: Session, data: UserLogin) -> dict:
        user = db.query(User).filter(User.email == data.email.lower()).first()
        if not user or not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationError("User account is inactive.")

        token = create_access_token(user.id)
        return {"user": user, "access_token": token, "token_type": "bearer"}

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthenticationError("User not found.")
        return user
