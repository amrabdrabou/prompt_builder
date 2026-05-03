import logging
import warnings

from authlib.deprecate import AuthlibDeprecationWarning
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

warnings.filterwarnings(
    "ignore",
    message="authlib.jose module is deprecated, please use joserfc instead.",
    category=AuthlibDeprecationWarning,
    module="authlib._joserfc_helpers",
)

from authlib.integrations.starlette_client import OAuth, OAuthError
from sqlalchemy.ext.asyncio import AsyncSession


from config import settings
from database import get_db

from memory import get_or_create_google_user, get_user_by_id
from schemas import UserResponse
from security import create_access_token, decode_access_token, get_token_from_request


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()


def is_placeholder_config(value: str | None) -> bool:
    if value is None:
        return False

    normalized = value.strip().lower()

    return (
        normalized.startswith("your_")
        or normalized.startswith("change_this")
        or normalized in {"placeholder", "changeme", "replace_me"}
    )


def validate_google_oauth_config() -> None:
    missing_values = []
    placeholder_values = []

    if not settings.GOOGLE_CLIENT_ID:
        missing_values.append("GOOGLE_CLIENT_ID")
    elif is_placeholder_config(settings.GOOGLE_CLIENT_ID):
        placeholder_values.append("GOOGLE_CLIENT_ID")

    if not settings.GOOGLE_CLIENT_SECRET:
        missing_values.append("GOOGLE_CLIENT_SECRET")
    elif is_placeholder_config(settings.GOOGLE_CLIENT_SECRET):
        placeholder_values.append("GOOGLE_CLIENT_SECRET")

    if not settings.SESSION_SECRET_KEY:
        missing_values.append("SESSION_SECRET_KEY")
    elif is_placeholder_config(settings.SESSION_SECRET_KEY):
        placeholder_values.append("SESSION_SECRET_KEY")

    if not settings.JWT_SECRET_KEY:
        missing_values.append("JWT_SECRET_KEY")
    elif is_placeholder_config(settings.JWT_SECRET_KEY):
        placeholder_values.append("JWT_SECRET_KEY")

    if missing_values:
        logger.error("Auth configuration is incomplete: missing %s", ", ".join(missing_values))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth service is unavailable. Contact the administrator.",
        )

    if placeholder_values:
        logger.error(
            "Auth configuration contains placeholder values: %s",
            ", ".join(placeholder_values),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth service is unavailable. Contact the administrator.",
        )


if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url=settings.GOOGLE_SERVER_METADATA_URL,
        client_kwargs={
            "scope": "openid email profile",
        },
    )

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    token = get_token_from_request(request)
    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user = await get_user_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user was not found.",
        )

    return user


@router.get("/me", response_model=UserResponse)
async def auth_me(
    current_user=Depends(get_current_user),
):
    return current_user


@router.post("/logout")
async def logout():
    response = Response(
        content='{"message":"Logged out successfully."}',
        media_type="application/json",
    )

    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )

    return response

@router.get("/google/login")
async def google_login(request: Request):
    validate_google_oauth_config()

    redirect_uri = settings.GOOGLE_REDIRECT_URI

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
    )


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    validate_google_oauth_config()

    try:
        token = await oauth.google.authorize_access_token(request)

    except OAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed.",
        ) from error

    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not read Google user information.",
        )

    google_sub = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name")
    picture_url = user_info.get("picture")

    if not google_sub or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account did not provide required profile information.",
        )

    user = await get_or_create_google_user(
        db=db,
        google_sub=google_sub,
        email=email,
        name=name,
        picture_url=picture_url,
    )

    await db.commit()

    access_token = create_access_token(user_id=user.id)

    response = RedirectResponse(url=settings.FRONTEND_URL)

    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )

    return response
