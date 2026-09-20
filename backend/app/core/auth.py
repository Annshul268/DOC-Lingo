import os
import json
import time
import uuid
import hmac
import hashlib
import base64
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.app.core.config import settings
from backend.app.schemas.auth import User

logger = logging.getLogger(__name__)

# Reusable security scheme for OpenAPI docs
security_scheme = HTTPBearer(auto_error=False)

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _base64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding < 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data.encode('utf-8'))

def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a standard HMAC-SHA256 signed JWT token."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_bytes = json.dumps(header, separators=(',', ':')).encode('utf-8')
    header_b64 = _base64url_encode(header_bytes)

    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.TOKEN_EXPIRE_HOURS))
    payload = {
        "sub": user.id,
        "username": user.username,
        "is_guest": user.is_guest,
        "exp": int(expire.timestamp())
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = _base64url_encode(payload_bytes)

    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(settings.JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Dict[str, Any]:
    """Verify and decode HMAC-SHA256 JWT token."""
    parts = token.strip().split('.')
    if len(parts) != 3:
        raise ValueError("Malformed token format")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    expected_sig = hmac.new(settings.JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    
    try:
        actual_sig = _base64url_decode(sig_b64)
    except Exception:
        raise ValueError("Invalid signature encoding")

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")

    try:
        payload_json = _base64url_decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
    except Exception:
        raise ValueError("Invalid token payload")

    exp = payload.get("exp")
    if exp is not None and time.time() > exp:
        raise ValueError("Token has expired")

    return payload

def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode('utf-8')).hexdigest()

class UserManager:
    _instance = None

    def __init__(self):
        self.registry_file = settings.USER_DATA_FILE
        self.users: Dict[str, Dict[str, Any]] = {}
        self.username_index: Dict[str, str] = {}
        self._load()

    @classmethod
    def get_instance(cls) -> "UserManager":
        if cls._instance is None:
            cls._instance = UserManager()
        return cls._instance

    def _load(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.users = data.get("users", {})
                    self.username_index = data.get("username_index", {})
            except Exception as e:
                logger.error(f"Failed to load users registry: {e}")
                self.users = {}
                self.username_index = {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "users": self.users,
                    "username_index": self.username_index
                }, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save users registry: {e}")

    def create_guest_user(self, nickname: Optional[str] = None) -> User:
        user_id = str(uuid.uuid4())[:12]
        clean_name = nickname.strip() if nickname and nickname.strip() else f"guest_{user_id[:6]}"
        
        user_record = {
            "id": user_id,
            "username": clean_name,
            "email": None,
            "is_guest": True,
            "password_hash": "",
            "salt": "",
            "created_at": datetime.utcnow().isoformat()
        }
        self.users[user_id] = user_record
        self._save()
        return User(id=user_id, username=clean_name, email=None, is_guest=True)

    def register_user(self, username: str, password: str, email: Optional[str] = None) -> User:
        clean_user = username.strip()
        lower_user = clean_user.lower()
        if lower_user in self.username_index:
            raise ValueError(f"Username '{clean_user}' is already registered")

        user_id = str(uuid.uuid4())[:12]
        salt = uuid.uuid4().hex
        pwd_hash = _hash_password(password, salt)

        user_record = {
            "id": user_id,
            "username": clean_user,
            "email": email.strip() if email else None,
            "is_guest": False,
            "password_hash": pwd_hash,
            "salt": salt,
            "created_at": datetime.utcnow().isoformat()
        }
        self.users[user_id] = user_record
        self.username_index[lower_user] = user_id
        self._save()
        return User(id=user_id, username=clean_user, email=user_record["email"], is_guest=False)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        clean_user = username.strip().lower()
        user_id = self.username_index.get(clean_user)
        if not user_id:
            return None

        record = self.users.get(user_id)
        if not record:
            return None

        salt = record.get("salt", "")
        expected_hash = record.get("password_hash", "")
        actual_hash = _hash_password(password, salt)

        if hmac.compare_digest(expected_hash, actual_hash):
            return User(
                id=record["id"],
                username=record["username"],
                email=record.get("email"),
                is_guest=record.get("is_guest", False)
            )
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        record = self.users.get(user_id)
        if not record:
            return None
        return User(
            id=record["id"],
            username=record["username"],
            email=record.get("email"),
            is_guest=record.get("is_guest", False)
        )

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token")
) -> User:
    """
    FastAPI dependency that extracts and verifies the authenticated User.
    Supports Bearer tokens in Authorization header or X-Session-Token header.
    """
    token = None
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    elif x_session_token:
        token = x_session_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Include Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_mgr = UserManager.get_instance()
    user = user_mgr.get_user_by_id(user_id)
    if not user:
        # If user record was created in this session token but not found in disk registry,
        # construct user from validated signed token payload
        user = User(
            id=user_id,
            username=payload.get("username", f"user_{user_id[:6]}"),
            is_guest=payload.get("is_guest", False)
        )

    return user
