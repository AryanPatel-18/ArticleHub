from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from app.schemas.auth_schema import RegistrationRequest,  LoginRequest, LoginResponse, TokenValidationResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.auth_service import register_user, login_user
from app.core.security import decode_access_token


router = APIRouter(
    prefix = "/auth",
    tags=["Authentication"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/register")
def registerUser(payload : RegistrationRequest, db : Session = Depends(get_db)):
    return register_user(db, payload)


@router.post("/login", response_model=LoginResponse)
def loginUser(payload: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, payload)

@router.get("/validate-token")
def validateToken(token : str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        return TokenValidationResponse(
            valid = True,
            user_id=payload.get("sub")
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")