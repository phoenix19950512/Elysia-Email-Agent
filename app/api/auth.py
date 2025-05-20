import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from app.auth.graph_auth import GraphAuth
from app.services.supabase_service import supabase_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_current_graph(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        user = supabase_service.get_user(email)
        if not user:
            access_token = payload.get("access_token")
            refresh_token: str = payload.get("refresh_token")
        access_token = user["access_token"]
        refresh_token = user["refresh_token"]
        if not refresh_token or not access_token or not email:
            raise credentials_exception
        graph_auth = GraphAuth(email=email, token=access_token, refresh_token=refresh_token)
        is_valid_token = await graph_auth.validate_token(access_token)
        if not is_valid_token:
            raise credentials_exception
        return graph_auth

    except Exception:
        raise credentials_exception
