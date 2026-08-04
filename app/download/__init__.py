import asyncio
import hashlib
import hmac
import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Callable

from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import DownloadError, QueueError
from app.core.logging import get_logger
from app.database import database
from app.models import Download, DownloadStatus, QueueItem, QueueStatus
from app.repositories import DownloadRepository, QueueRepository

logger = get_logger(__name__)


class DownloadEvent(str, Enum):
    STARTED = "download_started"
    PROGRESS_UPDATED = "progress_updated"
    COMPLETED = "download_completed"
    FAILED = "download_failed"
    UPLOAD_STARTED = "upload_started"
    UPLOAD_COMPLETED = "upload_completed"
    QUEUE_UPDATED = "queue_updated"


class DownloadState(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadProgress:
    download_id: str
    total_size: int | None = None
    downloaded_size: int = 0
    percentage: float = 0.0
    current_speed: int | None = None
    average_speed: int | None = None
    eta: int | None = None
    state: DownloadState = DownloadState.PENDING
    error_message: str | None = None


@dataclass
class DownloadResult:
    download_id: str
    success: bool
    file_path: str | None = None
    file_size: int | None = None
    error_message: str | None = None


class DownloadManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._active_downloads: dict[str, asyncio.Task] = {}
        self._paused_downloads: set[str] = set()
        self._cancelled_downloads: set[str] = set()
        self._progress_callbacks: list[Callable[[DownloadProgress], Any]] = []
        self._temp_dir = Path(self.settings.temp_directory)
        self._download_dir = Path(self.settings.download_directory)
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        self._download_dir.mkdir(parents=True, exist_ok=True)

    def register_progress_callback(self, callback: Callable[[DownloadProgress], Any]) -> None:
        self._progress_callbacks.append(callback)

    def _notify_progress(self, progress: DownloadProgress) -> None:
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception:
                logger.exception("progress_callback_error")

    async def start_download(
        self,
        user_id: int,
        url: str,
        provider: str,
        quality: str | None = None,
        audio_format: str | None = None,
    ) -> DownloadResult:
        download_id = self._generate_download_id()

        async with database.session() as session:
            download_repo = DownloadRepository(session)
            queue_repo = QueueRepository(session)

            download = await download_repo.create(
                user_id=user_id,
                provider=provider,
                url=url,
                status=DownloadStatus.QUEUED,
                temp_path=str(self._temp_dir / download_id),
            )

            queue_item = await queue_repo.add_to_queue(
                user_id=user_id,
                download_id=download.id,
            )

        logger.info("download_queued", download_id=download_id, user_id=user_id, url=url)

        task = asyncio.create_task(self._process_download(download_id, download, queue_item))
        self._active_downloads[download_id] = task

        return DownloadResult(download_id=download_id, success=True)

    async def _process_download(
        self,
        download_id: str,
        download: Download,
        queue_item: QueueItem,
    ) -> None:
        try:
            progress = DownloadProgress(download_id=download_id)
            progress.state = DownloadState.DOWNLOADING
            self._notify_progress(progress)

            temp_path = (
                Path(download.temp_path) if download.temp_path else self._temp_dir / download_id
            )

            await self._execute_download(download, temp_path, progress)

            if download_id in self._cancelled_downloads:
                self._cancelled_downloads.discard(download_id)
                download.status = DownloadStatus.CANCELLED
                progress.state = DownloadState.CANCELLED
                self._notify_progress(progress)
                return

            final_path = self._download_dir / (download.filename or download_id)
            shutil.move(str(temp_path), str(final_path))

            download.status = DownloadStatus.COMPLETED
            download.file_size = final_path.stat().st_size if final_path.exists() else None
            progress.state = DownloadState.COMPLETED
            progress.downloaded_size = download.file_size or 0
            progress.percentage = 100.0
            self._notify_progress(progress)

            logger.info("download_completed", download_id=download_id, file_size=download.file_size)

        except asyncio.CancelledError:
            download.status = DownloadStatus.CANCELLED
            progress.state = DownloadState.CANCELLED
            self._notify_progress(progress)
            logger.info("download_cancelled", download_id=download_id)
            raise

        except Exception as e:
            download.status = DownloadStatus.FAILED
            download.error_message = str(e)
            progress.state = DownloadState.FAILED
            progress.error_message = str(e)
            self._notify_progress(progress)
            logger.error("download_failed", download_id=download_id, error=str(e))
            raise

        finally:
            async with database.session() as session:
                download_repo = DownloadRepository(session)
                await download_repo.update(
                    download.id, status=download.status, error_message=download.error_message
                )

            if download_id in self._active_downloads:
                del self._active_downloads[download_id]

    async def _execute_download(
        self,
        download: Download,
        temp_path: Path,
        progress: DownloadProgress,
    ) -> None:
        max_retries = 3

        for attempt in range(max_retries):
            try:
                await self._download_with_progress(download, temp_path, progress)
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        "download_retry",
                        download_id=download.id,
                        attempt=attempt + 1,
                        wait=wait_time,
                        error=str(e),
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise DownloadError(
                        f"Download failed after {max_retries} attempts: {str(e)}",
                        download_id=str(download.id),
                    )

    async def _download_with_progress(
        self,
        download: Download,
        temp_path: Path,
        progress: DownloadProgress,
    ) -> None:
        import httpx

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.get(download.url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            start_time = time.time()

            with open(temp_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    if download.id in self._cancelled_downloads:
                        raise asyncio.CancelledError()

                    f.write(chunk)
                    downloaded += len(chunk)

                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        progress.current_speed = int(downloaded / elapsed)
                        progress.average_speed = int(downloaded / elapsed)

                    if total_size > 0:
                        progress.percentage = round((downloaded / total_size) * 100, 2)
                        progress.total_size = total_size
                        progress.downloaded_size = downloaded

                        if progress.current_speed and progress.current_speed > 0:
                            remaining = total_size - downloaded
                            progress.eta = int(remaining / progress.current_speed)

                    self._notify_progress(progress)

    def _generate_download_id(self) -> str:
        return hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:16]

    async def pause_download(self, download_id: str) -> bool:
        if download_id in self._active_downloads:
            self._paused_downloads.add(download_id)
            task = self._active_downloads[download_id]
            task.cancel()
            return True
        return False

    async def resume_download(self, download_id: str) -> bool:
        if download_id in self._paused_downloads:
            self._paused_downloads.discard(download_id)
            return True
        return False

    async def cancel_download(self, download_id: str) -> bool:
        self._cancelled_downloads.add(download_id)
        if download_id in self._active_downloads:
            task = self._active_downloads[download_id]
            task.cancel()
            return True
        return False

    async def get_progress(self, download_id: str) -> DownloadProgress | None:
        for callback in self._progress_callbacks:
            pass
        return None

    async def get_active_count(self) -> int:
        return len(self._active_downloads)


class QueueManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._max_concurrent = self.settings.max_concurrent_downloads
        self._max_queue_size = self.settings.max_queue_size

    async def can_add_to_queue(self, user_id: int) -> bool:
        async with database.session() as session:
            queue_repo = QueueRepository(session)
            active_count = await queue_repo.count({"user_id": user_id, "status": "active"})
            waiting_count = await queue_repo.count({"user_id": user_id, "status": "waiting"})

            total = active_count + waiting_count
            if total >= self._max_queue_size:
                raise QueueError(f"Queue full for user {user_id}")

            return active_count < self._max_concurrent

    async def get_queue_status(self, user_id: int) -> dict[str, Any]:
        async with database.session() as session:
            queue_repo = QueueRepository(session)
            active = await queue_repo.get_user_queue(user_id, status="active")
            waiting = await queue_repo.get_user_queue(user_id, status="waiting")
            completed = await queue_repo.get_user_queue(user_id, status="completed")
            failed = await queue_repo.get_user_queue(user_id, status="failed")

            return {
                "active": len(active),
                "waiting": len(waiting),
                "completed": len(completed),
                "failed": len(failed),
                "max_concurrent": self._max_concurrent,
                "max_queue_size": self._max_queue_size,
            }


class CleanupService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._temp_dir = Path(self.settings.temp_directory)
        self._temp_file_ttl = self.settings.temp_file_ttl
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("cleanup_service_started", interval=self.settings.cleanup_interval)

        while self._running:
            try:
                await self._run_cleanup()
            except Exception:
                logger.exception("cleanup_error")

            await asyncio.sleep(self.settings.cleanup_interval)

    async def stop(self) -> None:
        self._running = False
        logger.info("cleanup_service_stopped")

    async def _run_cleanup(self) -> None:
        now = time.time()
        expired_threshold = now - self._temp_file_ttl

        expired_files = 0
        for file_path in self._temp_dir.rglob("*"):
            if file_path.is_file():
                mtime = file_path.stat().st_mtime
                if mtime < expired_threshold:
                    try:
                        file_path.unlink()
                        expired_files += 1
                    except OSError:
                        logger.warning("cleanup_file_delete_failed", path=str(file_path))

        logger.info("cleanup_completed", expired_files=expired_files)

    async def recover_orphaned_files(self) -> int:
        recovered = 0
        for file_path in self._temp_dir.rglob("*"):
            if file_path.is_file():
                try:
                    file_path.chmod(0o600)
                    recovered += 1
                except OSError:
                    logger.warning("cleanup_file_recover_failed", path=str(file_path))

        logger.info("orphaned_files_recovered", count=recovered)
        return recovered


class EventSystem:
    def __init__(self) -> None:
        self._handlers: dict[DownloadEvent, list[Callable]] = {}

    def subscribe(self, event: DownloadEvent, handler: Callable) -> None:
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    async def emit(self, event: DownloadEvent, data: dict[str, Any]) -> None:
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception:
                    logger.exception("event_handler_error", event=event)


download_manager = DownloadManager()
queue_manager = QueueManager()
cleanup_service = CleanupService()
event_system = EventSystem()