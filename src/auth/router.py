from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from pydantic import EmailStr

from auth.analytics_service import AnalyticsService
from auth.dependencies import (
    CurrentAdmin,
    CurrentUser,
    get_analytics_service,
    get_user_service,
)
from auth.exceptions import (
    AlreadyConfirmedException,
    AlreadyRegisteredException,
    AlreadyRegisteredHTTPException,
    BadRequestException,
    BadRequestHTTPException,
    ErrorCallingFileService,
    ErrorCallingFileServiceHTTPException,
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
    Event,
    EventName,
    KafkaTopic,
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
from auth.utils import decrypt_user_id, verify_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    try:
        email = email.lower().strip()
        user_data = UserCreate(username=username, email=email, password=password)
        user = await service.register_user(user_data)
        event = Event(
            event_name=EventName.REGISTRATION.value,
            model_type="UserResponse",
            model_data=user.model_dump(),
            entity_id=str(user.id),
        )
        await analytics.publish_event(KafkaTopic.MODELS_TOPIC.value, event)
        return user
    except AlreadyRegisteredException as e:
        raise AlreadyRegisteredHTTPException(str(e))
    except ServerErrorException as e:
        raise ServerErrorHTTPException(str(e))


@router.post("/users/token", response_model=TokensResponse, status_code=status.HTTP_200_OK)
async def get_token(
    email: EmailStr = Form(...),
    password: str = Form(...),
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    try:
        data = LoginRequest(email=email, password=password)
        tokens = await service.login_user(data)
        user = await service.uow.users.get_user_by_email(email)
        event = Event(
            event_name=EventName.LOGIN.value,
            entity_id=str(user.id),
        )
        await analytics.publish_event(KafkaTopic.EVENTS_TOPIC.value, event)
        return tokens
    except UnauthorizedException as e:
        raise UnauthorizedHTTPException(str(e))
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))


@router.post("/users/refresh", response_model=TokensResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    try:
        tokens = await service.refresh_access_token(request.refresh_token)
        user_id = verify_token(request.refresh_token)
        user = await service.uow.users.get_by_id(user_id)
        event = Event(
            event_name=EventName.REFRESH.value,
            entity_id=str(user.id),
        )
        await analytics.publish_event(KafkaTopic.EVENTS_TOPIC.value, event)
        return tokens
    except TokenExpiredException as e:
        raise UnauthorizedHTTPException(str(e))
    except InvalidTokenException as e:
        raise UnauthorizedHTTPException(str(e))


@router.get("/users/confirm", status_code=status.HTTP_200_OK)
async def confirm_email(
    code: str = Query(...),
    encrypted_user_id: str = Query(...),
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    try:
        user = await service.confirm_user(code, encrypted_user_id)
        event = Event(
            event_name=EventName.CONFIRM.value,
            entity_id=str(user.id),
        )
        await analytics.publish_event(KafkaTopic.EVENTS_TOPIC.value, event)
        return {"detail": "Email confirmed successfully.", "user": user}
    except UnauthorizedException as e:
        raise UnauthorizedHTTPException(str(e))


@router.post("/users/resend-confirmation", status_code=status.HTTP_200_OK)
async def resend_confirmation(
    email: EmailStr = Form(...),
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    try:
        email = email.lower().strip()
        result = await service.resend_confirmation_email(email)
        user = await service.uow.users.get_user_by_email(email)
        event = Event(
            event_name=EventName.RESEND.value,
            entity_id=str(user.id),
        )
        await analytics.publish_event(KafkaTopic.EVENTS_TOPIC.value, event)
        return result
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))
    except AlreadyConfirmedException as e:
        raise BadRequestHTTPException(str(e))


@router.post("/users/password-reset", status_code=status.HTTP_200_OK)
async def request_reset(
    email: EmailStr = Form(...),
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    try:
        email = email.lower().strip()
        result = await service.request_password_reset(email)
        user = await service.uow.users.get_user_by_email(email)
        event = Event(
            event_name=EventName.RESET_PASSWORD.value,
            entity_id=str(user.id),
        )
        await analytics.publish_event(KafkaTopic.EVENTS_TOPIC.value, event)
        return result
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))


@router.post("/users/password-reset/confirm", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(
    code: str = Query(...),
    encrypted_user_id: str = Query(...),
    new_password: str = Form(...),
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    try:
        result = await service.reset_password(code, new_password, encrypted_user_id)
        user_id = decrypt_user_id(encrypted_user_id)
        event = Event(
            event_name=EventName.CONFIRM_PASSWORD.value,
            entity_id=str(user_id),
        )
        await analytics.publish_event(KafkaTopic.EVENTS_TOPIC.value, event)
        return result
    except UnauthorizedException as e:
        raise UnauthorizedHTTPException(str(e))


@router.get("/users/me")
async def get_current_user(
    current_user: CurrentUser,
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> UserResponseWithRoleName:
    user_with_role = await service.get_me(current_user)
    event = Event(
        event_name=EventName.GET.value,
        model_type="UserResponseWithRoleName",
        model_data=user_with_role.model_dump(),
        entity_id=str(user_with_role.id),
    )
    await analytics.publish_event(KafkaTopic.MODELS_TOPIC.value, event)
    return user_with_role


@router.get("/users/admin", response_model=PaginatedUserResponse)
async def get_all_users(
    current_admin: CurrentAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query(None, regex="^(created_at|username|role)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    role: str = Query(None),
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> PaginatedUserResponse:
    try:
        result = await service.get_all_user(page, page_size, sort_by, order, role)
        event = Event(event_name=EventName.GET_ALL.value)
        await analytics.publish_event(KafkaTopic.MODELS_TOPIC.value, event)
        return result
    except PermissionDeniedException as e:
        raise PermissionDeniedHTTPException(str(e))
    except BadRequestException as e:
        raise BadRequestHTTPException(str(e))


@router.get("/admin/roles/")
async def get_all_roles(
    current_admin: CurrentAdmin,
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> list[RoleResponse]:
    roles = await service.uow.roles.get_all()
    event = Event(
        event_name=EventName.GET_ALL.value,
        model_type="RoleResponse",
    )
    await analytics.publish_event(KafkaTopic.MODELS_TOPIC.value, event)
    return roles


@router.post("/user/admin/role", response_model=UserResponse)
async def update_user_role(
    current_admin: CurrentAdmin,
    email: EmailStr = Form(...),
    role: str = Form(...),
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> UserResponse:
    try:
        user = await service.uow.users.update_user_role(email, role)
        event = Event(
            event_name=EventName.UPDATE.value,
            model_type="UserResponse",
            model_data=user.model_dump(),
            entity_id=str(user.id),
        )
        await analytics.publish_event(KafkaTopic.MODELS_TOPIC.value, event)
        return user
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
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> UserResponse:
    try:
        user = await service.update_user(user_update, user_id)
        event = Event(
            event_name=EventName.UPDATE.value,
            model_type="UserResponse",
            model_data=user.model_dump(),
            entity_id=str(user.id),
        )
        await analytics.publish_event(KafkaTopic.MODELS_TOPIC.value, event)
        return user
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))
    except AlreadyRegisteredException as e:
        raise AlreadyRegisteredHTTPException(str(e))


@router.delete("/users/{user_id}", response_model=UserResponse)
async def delete_user(
    current_user: CurrentUser,
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> UserResponse:
    try:
        user = await service.uow.users.delete(user_id)
        event = Event(
            event_name=EventName.DELETE.value,
            model_type="UserResponse",
            model_data=user.model_dump(),
            entity_id=str(user.id),
        )
        await analytics.publish_event(KafkaTopic.MODELS_TOPIC.value, event)
        return user
    except NotFoundException as e:
        raise NotFoundHTTPException(str(e))


@router.post("/users/avatar/{user_id}")
async def load_file(
    user_id: UUID, file: UploadFile = File(...), service: UserService = Depends(get_user_service)
):
    try:
        return await service.load_file(user_id, file)
    except ErrorCallingFileService:
        raise ErrorCallingFileServiceHTTPException
