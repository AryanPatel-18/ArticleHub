from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from app.schemas.auth_schema import RegistrationRequest,  LoginRequest, LoginResponse, TokenValidationResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.auth_service import register_user, login_user
from app.core.security import decode_access_token

# This router handles all the endpoints related to user authentication, including registration, login, and token validation.
router = APIRouter(
    prefix = "/auth",
    tags=["Authentication"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Endpoint for user registration. It accepts a json payload with username, email, and password. It returns a success message upon successful registration or an error message if the registration fails.
@router.post("/register", status_code=201, summary="Register a new user")
def registerUser(
    payload: RegistrationRequest,
    db: Session = Depends(get_db),
):
    return register_user(db, payload)

# Endpoint for user login. It accepts a json payload with email and password. It returns an access token upon successful login or an error message if the login fails.

@router.post("/login", response_model=LoginResponse, summary="Login and receive an access token")
def loginUser(payload: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, payload)


# Endpoint to validate an access token. It accepts the token in the Authorization header and returns whether the token is valid and the user id associated with the token. If the token is invalid, it returns a 401 error.
@router.get("/validate-token", response_model=TokenValidationResponse, summary="Validate an access token")
def validateToken(token : str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        return TokenValidationResponse(
            valid = True,
            user_id=payload.get("sub")
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")