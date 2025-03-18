import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from auth.enums import RoleEnum


class TestRegister:
    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (None, status.HTTP_201_CREATED),
        ],
    )
    async def test_register_user_success(
        self, async_client: AsyncClient, role, expected_status, user_role
    ):
        response = await async_client.post(
            "/api/v1/auth/users",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "Testpass123!",
            },
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (None, status.HTTP_409_CONFLICT),
        ],
    )
    async def test_register_user_conflict_email(
        self,
        async_client: AsyncClient,
        session: AsyncSession,
        create_user_with_role,
        role,
        expected_status,
    ):
        user = await create_user_with_role(RoleEnum.USER)
        response = await async_client.post(
            "/api/v1/auth/users",
            data={
                "username": "otheruser",
                "email": user.email,
                "password": "Testpass123!",
            },
        )
        assert response.status_code == expected_status


class TestLogin:
    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (RoleEnum.USER, status.HTTP_200_OK),
            (RoleEnum.ADMIN, status.HTTP_200_OK),
        ],
    )
    async def test_login_success(
        self,
        async_client: AsyncClient,
        create_user_with_role,
        role,
        expected_status,
    ):
        user = await create_user_with_role(role)
        response = await async_client.post(
            "/api/v1/auth/users/token",
            data={"email": user.email, "password": "Password123!"},
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (RoleEnum.USER, status.HTTP_401_UNAUTHORIZED),
            (RoleEnum.ADMIN, status.HTTP_401_UNAUTHORIZED),
        ],
    )
    async def test_login_wrong_password(
        self, async_client: AsyncClient, create_user_with_role, role, expected_status
    ):
        user = await create_user_with_role(role)
        response = await async_client.post(
            "/api/v1/auth/users/token",
            data={"email": user.email, "password": "BadPassword!"},
        )
        assert response.status_code == expected_status


class TestPasswordReset:
    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (
                None,
                status.HTTP_200_OK,
            ),
        ],
    )
    async def test_request_password_reset(
        self, async_client: AsyncClient, create_user_with_role, role, expected_status
    ):
        user = await create_user_with_role(RoleEnum.USER)
        response = await async_client.post(
            "/api/v1/auth/users/password-reset",
            data={"email": user.email},
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (
                None,
                status.HTTP_401_UNAUTHORIZED,
            ),
        ],
    )
    async def test_confirm_wrong_password_reset(
        self,
        async_client: AsyncClient,
        session: AsyncSession,
        create_user_with_role,
        role,
        expected_status,
    ):
        await create_user_with_role(RoleEnum.USER)
        code = "123456"
        encrypted_user_id = "encrypted_id"
        response = await async_client.post(
            f"/api/v1/auth/users/password-reset/confirm?code={code}&encrypted_user_id={encrypted_user_id}",  # noqa
            data={"new_password": "NewSecret123!"},
        )
        assert response.status_code == expected_status


class TestConfirmEmail:
    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (
                None,
                status.HTTP_401_UNAUTHORIZED,
            ),
        ],
    )
    async def test_confirm_email_success(
        self,
        async_client: AsyncClient,
        session: AsyncSession,
        create_user_with_role,
        role,
        expected_status,
    ):
        await create_user_with_role(RoleEnum.USER)
        code = "123456"
        encrypted_user_id = "encrypted_id"
        response = await async_client.get(
            f"/api/v1/auth/users/confirm?code={code}&encrypted_user_id={encrypted_user_id}"
        )
        assert response.status_code == expected_status


class TestGetMe:
    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (RoleEnum.USER, status.HTTP_200_OK),
            (RoleEnum.ADMIN, status.HTTP_200_OK),
            (
                None,
                status.HTTP_403_FORBIDDEN,
            ),
        ],
    )
    async def test_get_current_user(
        self,
        async_client: AsyncClient,
        create_user_with_role,
        get_token_for_user,
        role,
        expected_status,
    ):
        if role:
            user = await create_user_with_role(role)
            token = await get_token_for_user(user)
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}
        response = await async_client.get("/api/v1/auth/users/me", headers=headers)
        assert response.status_code == expected_status


class TestAdminEndpoints:
    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (RoleEnum.ADMIN, status.HTTP_200_OK),
            (
                RoleEnum.USER,
                status.HTTP_403_FORBIDDEN,
            ),
            (
                None,
                status.HTTP_403_FORBIDDEN,
            ),
        ],
    )
    async def test_get_all_users(
        self,
        async_client: AsyncClient,
        create_user_with_role,
        get_token_for_user,
        role,
        expected_status,
    ):
        if role:
            user = await create_user_with_role(role)
            token = await get_token_for_user(user)
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}
        response = await async_client.get("/api/v1/auth/users/admin", headers=headers)
        assert response.status_code == expected_status


class TestDeleteUser:
    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (RoleEnum.ADMIN, status.HTTP_200_OK),
            (RoleEnum.USER, status.HTTP_200_OK),
            (
                None,
                status.HTTP_403_FORBIDDEN,
            ),
        ],
    )
    async def test_delete_user(
        self,
        async_client: AsyncClient,
        session: AsyncSession,
        create_user_with_role,
        get_token_for_user,
        role,
        expected_status,
    ):
        user_to_delete = await create_user_with_role(RoleEnum.USER)
        if role:
            admin_user = await create_user_with_role(role, True)
            token = await get_token_for_user(admin_user)
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}
        response = await async_client.delete(
            f"/api/v1/auth/users/{user_to_delete.id}", headers=headers
        )
        assert response.status_code == expected_status


class TestLoadAvatar:
    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (RoleEnum.ADMIN, status.HTTP_200_OK),
            (RoleEnum.USER, status.HTTP_403_FORBIDDEN),
            (
                None,
                status.HTTP_403_FORBIDDEN,
            ),
        ],
    )
    async def test_load_avatar(
        self,
        async_client: AsyncClient,
        create_user_with_role,
        get_token_for_user,
        role,
        expected_status,
    ):
        if role is None:
            user = await create_user_with_role(RoleEnum.USER)
            headers = {}
        else:
            user = await create_user_with_role(role)
            token = await get_token_for_user(user)
            headers = {"Authorization": f"Bearer {token}"}
        files = {"file": ("avatar.png", b"\x89PNG\r\n\x1a\n...", "image/png")}
        response = await async_client.post(
            f"/api/v1/auth/users/avatar/{user.id}", headers=headers, files=files
        )
        assert response.status_code == expected_status
