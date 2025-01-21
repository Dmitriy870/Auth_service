from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, status
from pydantic import EmailStr

from auth.dependencies import CurrentAdmin, CurrentUser, get_user_service
from auth.exceptions import (
    AlreadyConfirmedException,
    AlreadyRegisteredException,
    AlreadyRegisteredHTTPException,
    BadRequestException,
    BadRequestHTTPException,
    InvalidTokenException,
    NotFoundException,
    NotFoundHTTPException,
    PermissionDeniedException,
    PermissionDeniedHTTPException,
    ServerErrorException,
    ServerErrorHTTPException,
    TokenExpiredException,
    UnauthorizedException,
    UnauthorizedHTTPException,
)
from auth.schemas import (
    LoginRequest,
    PaginatedUserResponse,
    RefreshTokenRequest,
    RoleResponse,
    TokensResponse,
    UserCreate,
    UserResponse,
    UserResponseWithRoleName,
    UserUpdate,
)
from auth.service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    service: UserService = Depends(get_user_service),
):
    try:
        email = email.lower().strip()
        user_data = UserCreate(username=username, email=email, password=password)
        return await service.register_user(user_data)
    except AlreadyRegisteredException as e:
        raise AlreadyRegisteredHTTPException(str(e))
    except ServerErrorException as e:
        raise ServerErrorHTTPException(str(e))


@router.post("/users/token", response_model=TokensResponse, status_code=status.HTTP_200_OK)
async def get_token(
    email: EmailStr = Form(...),
    password: str = Form(...),
    service: UserService = Depends(get_user_service),
):
    try:
        data = LoginRequest(email=email, password=password)
        return await service.login_user(data)
    except UnauthorizedException as e:
        raise UnauthorizedHTTPException(str(e))
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))


@router.post("/users/refresh", response_model=TokensResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    try:
        return await service.refresh_access_token(request.refresh_token)
    except TokenExpiredException as e:
        raise UnauthorizedHTTPException(str(e))
    except InvalidTokenException as e:
        raise UnauthorizedHTTPException(str(e))


@router.get("/users/confirm", status_code=status.HTTP_200_OK)
async def confirm_email(
    code: str = Query(...),
    encrypted_user_id: str = Query(...),
    service: UserService = Depends(get_user_service),
):
    try:
        user = await service.confirm_user(code, encrypted_user_id)
        return {"detail": "Email confirmed successfully.", "user": user}
    except UnauthorizedException as e:
        raise UnauthorizedHTTPException(str(e))


@router.post("/users/resend-confirmation", status_code=status.HTTP_200_OK)
async def resend_confirmation(
    email: EmailStr = Form(...),
    service: UserService = Depends(get_user_service),
):
    try:
        email = email.lower().strip()
        return await service.resend_confirmation_email(email)
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))
    except AlreadyConfirmedException as e:
        raise BadRequestHTTPException(str(e))


@router.post("/users/password-reset", status_code=status.HTTP_200_OK)
async def request_reset(
    email: EmailStr = Form(...),
    service: UserService = Depends(get_user_service),
):
    try:
        email = email.lower().strip()
        return await service.request_password_reset(email)
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))


@router.post("/users/password-reset/confirm", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(
    code: str = Query(...),
    encrypted_user_id: str = Query(...),
    new_password: str = Form(...),
    service: UserService = Depends(get_user_service),
):
    try:
        return await service.reset_password(code, new_password, encrypted_user_id)
    except UnauthorizedException as e:
        raise UnauthorizedHTTPException(str(e))


@router.get("/users/me")
async def get_current_user(
    current_user: CurrentUser,
    service: UserService = Depends(get_user_service),
) -> UserResponseWithRoleName:
    return await service.get_me(current_user)


@router.get("/users/admin/all", response_model=PaginatedUserResponse)
async def get_all_users(
    current_admin: CurrentAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query(None, regex="^(created_at|username|role)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    role: str = Query(None),
    service: UserService = Depends(get_user_service),
) -> PaginatedUserResponse:
    try:
        return await service.get_all_user(page, page_size, sort_by, order, role)
    except PermissionDeniedException as e:
        raise PermissionDeniedHTTPException(str(e))
    except BadRequestException as e:
        raise BadRequestHTTPException(str(e))


@router.get("/admin/roles/")
async def get_all_roles(
    current_admin: CurrentAdmin, service: UserService = Depends(get_user_service)
) -> list[RoleResponse]:
    return await service.uow.roles.get_all()


@router.post("/user/admin/role", response_model=UserResponse)
async def update_user_role(
    current_admin: CurrentAdmin,
    email: EmailStr = Form(...),
    role: str = Form(...),
    service: UserService = Depends(get_user_service),
) -> UserResponse | None:
    try:
        return await service.uow.users.update_user_role(email, role)
    except PermissionDeniedException as e:
        raise PermissionDeniedHTTPException(str(e))
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))
    except BadRequestException as e:
        raise BadRequestHTTPException(str(e))


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    current_user: CurrentUser,
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        return await service.update_user(user_update, user_id)
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))
    except AlreadyRegisteredException as e:
        raise AlreadyRegisteredHTTPException(str(e))


@router.delete("/users/{user_id}")
async def delete_user(
    current_user: CurrentUser,
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        return await service.uow.users.delete(user_id)
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))
