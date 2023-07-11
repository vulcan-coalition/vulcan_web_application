from fastapi import Depends, HTTPException, status, Form, Header, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
import jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
from .configuration import get_config
from .services import *


# to get a string like this run:
# openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60
REFRESH_TOKEN_EXPIRE_MINUTES = 24 * 60 * 5


def create_access_token(data: dict, expires_delta: Optional[timedelta] = timedelta(minutes=15)):
    SECRET_KEY = get_config("secret_key")
    expire = datetime.utcnow() + expires_delta
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = timedelta(minutes=30)):
    return create_access_token(data=data, expires_delta=expires_delta)


def create_tokens(userdata: dict):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=userdata, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data=userdata, expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


class User(BaseModel):
    email: str
    disability: int


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"Authorization": "Bearer"},
)


def decode_token(token: str):
    SECRET_KEY = get_config("secret_key")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        exp = payload.get("exp")
        disability = payload.get("disability")
        expired = datetime.now() > datetime.fromtimestamp(exp)
        if expired:
            raise jwt.ExpiredSignatureError()
        if email is None:
            raise credentials_exception
    except jwt.DecodeError:
        raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return email, disability


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


def initialize(app, security_prefix=""):

    router = APIRouter(prefix=security_prefix, tags=[security_prefix[1:] if security_prefix.startswith("/") else security_prefix])

    @router.post("/exchange", response_model=Token)
    async def exchange_access_token(token: str = Form(...)):
        bypass_security = get_config("test")
        if bypass_security:
            userdata = {'email': "testuser@vulcan", 'disability': 0}
        else:
            result, userdata = await login(token)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return create_tokens(userdata)

    @router.post('/refresh', response_model=Token)
    async def refresh_token(refresher: str = Form(...)):

        email, disability = decode_token(refresher)

        return create_tokens({"email": email, "disability": disability})

    @router.post("/token", response_model=Token)
    async def login_for_admin_token(form_data: OAuth2PasswordRequestForm = Depends()):
        bypass_security = get_config("test")
        if bypass_security:
            userdata = {'email': "testuser@vulcan", 'data': True}
        else:
            result, userdata = await admin_login(form_data.username, form_data.password)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            userdata["data"] = True

        return create_tokens(userdata)

    app.include_router(router)

    async def get_active_current_user(Authorization: str = Header(None)):
        bypass_security = get_config("test")
        if Authorization is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = Authorization[len("Bearer "):]

        if bypass_security:
            return User(email="testuser@vulcan", disability=0)

        email, disability = decode_token(token)

        user = User(email=email, disability=disability)
        return user

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl=security_prefix + "/token")

    async def check_is_admin(token: str = Depends(oauth2_scheme)):
        SECRET_KEY = get_config("secret_key")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("email")
            exp = payload.get("exp")
            data = payload.get("data")
            expired = datetime.now() > datetime.fromtimestamp(exp)
            if email is None or expired or data is None:
                raise credentials_exception
        except jwt.DecodeError:
            raise credentials_exception

        return True

    return get_active_current_user, check_is_admin
