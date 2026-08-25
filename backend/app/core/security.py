from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
def create_token(user: User) -> str:
    return jwt.encode({"sub": str(user.id), "role": user.role.name, "exp": datetime.now(timezone.utc)+timedelta(hours=8)}, settings.secret_key, algorithm="HS256")
def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload=jwt.decode(token, settings.secret_key, algorithms=['HS256'])
        user_id=int(payload['sub'])
    except (JWTError, KeyError, ValueError): raise HTTPException(status_code=401, detail="Invalid authentication")
    user=db.get(User,user_id)
    if not user or not user.is_active: raise HTTPException(status_code=401, detail="Inactive user")
    # Finish authentication's read transaction so workflow endpoints can open
    # their own explicit atomic transaction on the same request session.
    _ = user.role.name
    db.commit()
    return user
def require_roles(*roles: str):
    def checker(user: User = Depends(current_user)):
        if user.role.name not in roles: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Insufficient permission")
        return user
    return checker
