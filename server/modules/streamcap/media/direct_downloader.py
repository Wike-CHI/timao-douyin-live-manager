import asyncio
import os
import time
from typing import Optional

import httpx
import logging

# 使用标准 logging
logger = logging.getLogger(__name__)


class DirectStreamDownloader:
    """
    Directly download the live stream using HTTP requests, used to handle FLV streams that ffmpeg cannot handle normally
    """

    def __init__(self,
                 record_url: str,
                 save_path: str,
                 headers: Optional[dict[str, str]] = None,
                 proxy: Optional[str] = None,
                 chunk_size: int = 1024 * 16):  # 16KB chunks
        self.record_url = record_url
        self.save_path = save_path
        self.headers = headers or {}
        self.proxy = proxy or None
        self.chunk_size = chunk_size
        self.stop_event = asyncio.Event()
        self.process = None
        self.download_task = None
        self.total_bytes = 0
        self.start_time = None

    async def start_download(self) -> bool:
        self.start_time = time.time()
        self.download_task = asyncio.create_task(self._download_stream())
        return True

    async def stop_download(self) -> None:
        if not self.stop_event.is_set():
            self.stop_event.set()
            if self.download_task:
                try:
                    await asyncio.wait_for(self.download_task, timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Download Timeout: {self.record_url}")
                except Exception as e:
                    logger.error(f"Download Error: {e}")

    async def _download_stream(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            # Prepare default headers for Douyin/CDN compatibility
            default_headers = dict(self.headers)
            if "douyin" in (self.record_url or ""):
                default_headers.setdefault(
                    "User-Agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36",
                )
                default_headers.setdefault("Referer", "https://live.douyin.com/")
                if ".m3u8" in self.record_url:
                    default_headers.setdefault("Accept", "application/vnd.apple.mpegurl")

            async with httpx.AsyncClient(headers=default_headers, proxy=self.proxy, timeout=None, follow_redirects=True) as client:
                async with client.stream("GET", self.record_url) as response:
                    if response.status_code != 200:
                        logger.error(f"Request Stream Failed, Status Code: {response.status_code}")
                        return

                    with open(self.save_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(self.chunk_size):
                            if self.stop_event.is_set():
                                break

                            f.write(chunk)
                            self.total_bytes += len(chunk)

                            # Please don't remove this comment code
                            # elapsed = time.time() - self.start_time
                            # if int(elapsed) % 10 == 0:
                            #     mb_downloaded = self.total_bytes / (1024 * 1024)
                            #     mb_per_sec = mb_downloaded / elapsed if elapsed > 0 else 0
                            #     logger.info(f"Downloaded {mb_downloaded:.2f} MB, Speed: {mb_per_sec:.2f} MB/s")

            logger.success(f"Download Completed: {self.save_path}")

        except asyncio.CancelledError:
            logger.info(f"Download Task Canceled: {self.record_url}")
        except Exception as e:
            logger.error(f"Download Error: {e}")
