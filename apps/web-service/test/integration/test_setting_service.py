import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.setting import Setting
from app.model.setting_group import SettingGroup
from app.schemas.setting import SettingUpdateItem
from app.service.setting_service import SettingService, SETTINGS_DTO


class TestInitialize:
    @pytest.mark.smoke
    async def test_first_initialize_creates_data(self, db_session: AsyncSession):
        svc = SettingService(db_session)
        result = await svc.initialize()

        assert result["groups_created"] == len(SETTINGS_DTO)
        expected_settings_count = sum(len(g.settings) for g in SETTINGS_DTO)
        assert result["settings_created"] == expected_settings_count
        assert result["groups_deleted"] == 0
        assert result["settings_deleted"] == 0

    async def test_reinitialize_is_idempotent(self, db_session: AsyncSession):
        svc = SettingService(db_session)
        await svc.initialize()
        result = await svc.initialize()

        assert result["groups_created"] == 0
        assert result["settings_created"] == 0
        assert result["groups_deleted"] == 0
        assert result["settings_deleted"] == 0


class TestGetAll:
    async def test_empty_before_initialize(self, db_session: AsyncSession):
        svc = SettingService(db_session)
        result = await svc.get_all()
        assert result == []

    async def test_returns_groups_after_initialize(self, db_session: AsyncSession):
        svc = SettingService(db_session)
        await svc.initialize()
        result = await svc.get_all()

        assert len(result) == len(SETTINGS_DTO)
        group = result[0]
        assert group.key == SETTINGS_DTO[0].key
        assert group.display_name == SETTINGS_DTO[0].display_name
        assert len(group.settings) == len(SETTINGS_DTO[0].settings)


class TestUpdateSettings:
    async def _init_and_get_svc(self, db_session: AsyncSession) -> SettingService:
        svc = SettingService(db_session)
        await svc.initialize()
        return svc

    @pytest.mark.smoke
    async def test_update_single_key(self, db_session: AsyncSession):
        svc = await self._init_and_get_svc(db_session)

        result = await svc.update_settings(
            [
                SettingUpdateItem(
                    group_key="aliyun_oss",
                    key="oss_endpoint",
                    value="https://new.example.com",
                )
            ]
        )
        assert len(result) == 1
        assert result[0].key == "oss_endpoint"
        assert result[0].value == "https://new.example.com"

    async def test_update_multiple_keys(self, db_session: AsyncSession):
        svc = await self._init_and_get_svc(db_session)

        result = await svc.update_settings(
            [
                SettingUpdateItem(
                    group_key="aliyun_oss", key="oss_endpoint", value="v1"
                ),
                SettingUpdateItem(
                    group_key="aliyun_oss", key="oss_bucket_name", value="my-bucket"
                ),
            ]
        )
        assert len(result) == 2
        values = {r.key: r.value for r in result}
        assert values["oss_endpoint"] == "v1"
        assert values["oss_bucket_name"] == "my-bucket"

    async def test_update_no_matching_group_returns_empty(
        self, db_session: AsyncSession
    ):
        svc = await self._init_and_get_svc(db_session)

        result = await svc.update_settings(
            [
                SettingUpdateItem(
                    group_key="nonexistent_group", key="oss_endpoint", value="x"
                )
            ]
        )
        assert result == []

    async def test_update_no_matching_key_returns_empty(
        self, db_session: AsyncSession
    ):
        svc = await self._init_and_get_svc(db_session)

        result = await svc.update_settings(
            [
                SettingUpdateItem(
                    group_key="aliyun_oss", key="nonexistent_key", value="x"
                )
            ]
        )
        assert result == []

    async def test_update_empty_value(self, db_session: AsyncSession):
        svc = await self._init_and_get_svc(db_session)

        result = await svc.update_settings(
            [SettingUpdateItem(group_key="aliyun_oss", key="oss_endpoint", value="")]
        )
        assert len(result) == 1
        assert result[0].value == ""

    async def test_update_only_targets_specified_group(self, db_session: AsyncSession):
        svc = await self._init_and_get_svc(db_session)

        # 手动创建第二个分组，且包含与 aliyun_oss 同名的 key
        other_group = SettingGroup(
            key="other_group", display_name="其他分组", description="用于测试隔离"
        )
        db_session.add(other_group)
        await db_session.flush()
        db_session.add(
            Setting(
                key="oss_endpoint",
                value="other-value",
                display_name="",
                description="",
                group_id=other_group.id,
            )
        )
        await db_session.flush()

        result = await svc.update_settings(
            [
                SettingUpdateItem(
                    group_key="aliyun_oss", key="oss_endpoint", value="target-value"
                )
            ]
        )
        assert len(result) == 1
        assert result[0].value == "target-value"

        # 另一个分组下的同名 key 不应被影响
        other_setting = await db_session.scalar(
            select(Setting).where(
                Setting.group_id == other_group.id, Setting.key == "oss_endpoint"
            )
        )
        assert other_setting is not None
        assert other_setting.value == "other-value"
