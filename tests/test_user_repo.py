import pytest

from auth.enums import RoleEnum
from auth.exceptions import InvalidRoleException, NotFoundException


@pytest.mark.asyncio
async def test_get_user_by_email_found(user_repo, create_user_with_role):
    user = await create_user_with_role(RoleEnum.USER)
    result = await user_repo.get_user_by_email(user.email)
    assert result is not None
    assert result.email == user.email


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_repo):
    result = await user_repo.get_user_by_email("nonexistent@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_username_found(user_repo, create_user_with_role):
    user = await create_user_with_role(RoleEnum.USER)
    result = await user_repo.get_user_by_username(user.username)
    assert result is not None
    assert result.username == user.username


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(user_repo):
    result = await user_repo.get_user_by_username("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_update_user_role_user_not_found(user_repo):
    with pytest.raises(NotFoundException):
        await user_repo.update_user_role("nonexistent@example.com", RoleEnum.USER.value)


@pytest.mark.asyncio
async def test_update_user_role_invalid_role(user_repo, create_user_with_role):
    user = await create_user_with_role(RoleEnum.USER)
    with pytest.raises(InvalidRoleException):
        await user_repo.update_user_role(user.email, "INVALID_ROLE")


@pytest.mark.asyncio
async def test_update_user_role_success(user_repo, create_user_with_role, admin_role, role_repo):
    user = await create_user_with_role(RoleEnum.USER)
    updated = await user_repo.update_user_role(user.email, RoleEnum.ADMIN.value)
    role_obj = await role_repo.get_role_by_name(RoleEnum.ADMIN.value)
    assert updated is not None
    assert updated.role_id == role_obj.id


@pytest.mark.asyncio
async def test_set_false_email(user_repo, create_user_with_role):
    user = await create_user_with_role(RoleEnum.USER)
    updated = await user_repo.set_false_email(user.id)
    assert updated is not None
    assert updated.is_approved is False


@pytest.mark.asyncio
async def test_insert_slug(user_repo, create_user_with_role):
    user = await create_user_with_role(RoleEnum.USER)
    new_slug = "new_avatar_slug"
    updated = await user_repo.insert_slug(user.id, new_slug)
    assert updated is not None
    assert updated.avatar == new_slug


@pytest.mark.asyncio
async def test_check_avatar_exists(user_repo, create_user_with_role, session):
    user = await create_user_with_role(RoleEnum.USER)
    user.avatar = "existing_slug"
    await session.commit()
    avatar = await user_repo.check_avatar(user.id)
    assert avatar == "existing_slug"


@pytest.mark.asyncio
async def test_check_avatar_not_exists(user_repo, create_user_with_role, session):
    user = await create_user_with_role(RoleEnum.USER)
    user.avatar = None
    await session.commit()
    avatar = await user_repo.check_avatar(user.id)
    assert avatar is None
