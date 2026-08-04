from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Download, DownloadHistory, QueueItem, User, UserSettings
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_admins(self) -> list[User]:
        query = select(User).where(User.role == "admin")
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_banned_users(self) -> list[User]:
        query = select(User).where(User.is_banned == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class DownloadRepository(BaseRepository[Download]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Download)

    async def get_user_downloads(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> list[Download]:
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        return await self.get_all(
            offset=offset, limit=limit, filters=filters, order_by="created_at", order_desc=True
        )

    async def get_active_downloads(self, user_id: int) -> list[Download]:
        return await self.get_user_downloads(user_id, status="downloading")

    async def get_pending_downloads(self, user_id: int) -> list[Download]:
        return await self.get_user_downloads(user_id, status="pending")

    async def get_by_provider(self, provider: str) -> list[Download]:
        query = select(Download).where(Download.provider == provider)
        result = await self.session.execute(query)
        return list(result.scalars().all())


class DownloadHistoryRepository(BaseRepository[DownloadHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DownloadHistory)

    async def get_user_history(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> list[DownloadHistory]:
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        return await self.get_all(
            offset=offset, limit=limit, filters=filters, order_by="created_at", order_desc=True
        )

    async def search(
        self, user_id: int, query: str, *, offset: int = 0, limit: int = 100
    ) -> list[DownloadHistory]:
        from sqlalchemy import or_

        stmt = (
            select(DownloadHistory)
            .where(
                DownloadHistory.user_id == user_id,
                or_(
                    DownloadHistory.filename.ilike(f"%{query}%"),
                    DownloadHistory.url.ilike(f"%{query}%"),
                    DownloadHistory.provider.ilike(f"%{query}%"),
                ),
            )
            .order_by(DownloadHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class QueueRepository(BaseRepository[QueueItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, QueueItem)

    async def get_user_queue(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> list[QueueItem]:
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        return await self.get_all(
            offset=offset,
            limit=limit,
            filters=filters,
            order_by="position",
            order_desc=False,
        )

    async def get_waiting_queue(self, user_id: int) -> list[QueueItem]:
        return await self.get_user_queue(user_id, status="waiting")

    async def get_active_queue(self, user_id: int) -> list[QueueItem]:
        return await self.get_user_queue(user_id, status="active")

    async def get_next_waiting(self, user_id: int) -> QueueItem | None:
        query = (
            select(QueueItem)
            .where(QueueItem.user_id == user_id, QueueItem.status == "waiting")
            .order_by(QueueItem.priority.desc(), QueueItem.position.asc())
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_positions(self, user_id: int) -> None:
        items = await self.get_waiting_queue(user_id)
        for index, item in enumerate(items):
            item.position = index + 1
        await self.session.flush()

    async def add_to_queue(
        self, user_id: int, download_id: int | None = None, priority: int = 0
    ) -> QueueItem:
        max_pos_query = (
            select(QueueItem.position)
            .where(QueueItem.user_id == user_id)
            .order_by(QueueItem.position.desc())
        )
        result = await self.session.execute(max_pos_query)
        max_pos = result.scalar() or 0

        return await self.create(
            user_id=user_id,
            download_id=download_id,
            position=max_pos + 1,
            priority=priority,
            status="waiting",
        )


class UserSettingsRepository(BaseRepository[UserSettings]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserSettings)

    async def get_by_user_id(self, user_id: int) -> UserSettings | None:
        query = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_or_update(self, user_id: int, **kwargs: Any) -> UserSettings:
        settings = await self.get_by_user_id(user_id)
        if settings:
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            await self.session.flush()
            await self.session.refresh(settings)
            return settings
        return await self.create(user_id=user_id, **kwargs)