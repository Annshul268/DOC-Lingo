from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.schemas.auth import (
    User,
    UserResponse,
    AuthTokenResponse,
    LoginRequest,
    RegisterRequest,
    SessionRequest
)
from backend.app.core.auth import (
    UserManager,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/session", response_model=AuthTokenResponse)
async def create_guest_session(req: SessionRequest = None):
    """
    Creates an isolated guest user session and returns a Bearer access token.
    Enables immediate out-of-the-box usage without requiring registration upfront.
    """
    user_mgr = UserManager.get_instance()
    nickname = req.username if req else None
    user = user_mgr.create_guest_user(nickname=nickname)
    token = create_access_token(user)
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_guest=user.is_guest
        )
    )

@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """Register a new user account with isolated document workspace."""
    user_mgr = UserManager.get_instance()
    try:
        user = user_mgr.register_user(
            username=req.username,
            password=req.password,
            email=req.email
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token = create_access_token(user)
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_guest=user.is_guest
        )
    )

@router.post("/login", response_model=AuthTokenResponse)
async def login(req: LoginRequest):
    """Authenticate with username and password to access the user's workspace."""
    user_mgr = UserManager.get_instance()
    user = user_mgr.authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(user)
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_guest=user.is_guest
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve details for the currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_guest=current_user.is_guest
    )
