"""
Cross-platform helpers for launching subprocesses inside asyncio contexts.

On Windows the default ``ProactorEventLoop`` used by uvicorn does not implement
``create_subprocess_exec``.  This module provides a lightweight adapter that
falls back to ``subprocess.Popen`` and bridges stdout/stderr into asyncio
StreamReaders so the rest of the code can continue to await on pipes.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from typing import Iterable, Optional


async def create_subprocess_exec(
    *cmd: str,
    stdout: Optional[int] = None,
    stderr: Optional[int] = None,
) -> "AsyncProcess":
    """
    Wrapper around ``asyncio.create_subprocess_exec`` that transparently falls
    back to a thread/selector based adapter on Windows Proactor loops.
    """
    if os.name == "nt":
        # On Windows, always use our custom implementation to avoid NotImplementedError
        loop = asyncio.get_running_loop()
        return await _create_windows_process(cmd, stdout=stdout, stderr=stderr, loop=loop)

    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=stdout, stderr=stderr)
        return AsyncProcess(proc=proc)
    except NotImplementedError:
        # Fallback for any platform that doesn't support subprocess transport
        loop = asyncio.get_running_loop()
        return await _create_windows_process(cmd, stdout=stdout, stderr=stderr, loop=loop)


class AsyncProcess:
    """
    Adapter exposing a minimal subset of the ``asyncio.subprocess.Process`` API.

    The implementation works for both the native asyncio subprocess objects as
    well as the custom Windows fallback.
    """

    def __init__(self, *, proc, stdout_reader=None, stderr_reader=None, wait_hook=None) -> None:
        self._proc = proc
        self.pid = getattr(proc, "pid", None)
        self.stdin = getattr(proc, "stdin", None)
        self.stdout = stdout_reader or getattr(proc, "stdout", None)
        self.stderr = stderr_reader or getattr(proc, "stderr", None)
        self._wait_hook = wait_hook

    @property
    def returncode(self):
        return getattr(self._proc, "returncode", None)

    def send_signal(self, sig: int) -> None:
        self._proc.send_signal(sig)

    def kill(self) -> None:
        self._proc.kill()

    async def wait(self) -> int:
        if self._wait_hook:
            return await self._wait_hook()
        return await self._proc.wait()


async def _create_windows_process(
    cmd: Iterable[str],
    *,
    stdout: Optional[int],
    stderr: Optional[int],
    loop: asyncio.AbstractEventLoop,
) -> AsyncProcess:
    popen_kwargs = {
        "stdout": subprocess.PIPE if stdout == asyncio.subprocess.PIPE else None,
        "stderr": subprocess.PIPE if stderr == asyncio.subprocess.PIPE else None,
        "stdin": None,
        "bufsize": 0,
        "creationflags": subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
    }

    proc = await asyncio.to_thread(subprocess.Popen, cmd, **popen_kwargs)

    stdout_reader = asyncio.StreamReader() if popen_kwargs["stdout"] else None
    stderr_reader = asyncio.StreamReader() if popen_kwargs["stderr"] else None

    if stdout_reader and proc.stdout:
        loop.run_in_executor(None, _pipe_pump, proc.stdout, stdout_reader, loop)
    if stderr_reader and proc.stderr:
        loop.run_in_executor(None, _pipe_pump, proc.stderr, stderr_reader, loop)

    async def _wait() -> int:
        return await asyncio.to_thread(proc.wait)

    return AsyncProcess(proc=proc, stdout_reader=stdout_reader, stderr_reader=stderr_reader, wait_hook=_wait)


def _pipe_pump(pipe, reader: asyncio.StreamReader, loop: asyncio.AbstractEventLoop) -> None:
    """Continuously read from a blocking pipe and feed the reader inside the event loop."""
    try:
        while True:
            chunk = pipe.read(4096)
            if not chunk:
                break
            loop.call_soon_threadsafe(reader.feed_data, chunk)
    except Exception as exc:  # pragma: no cover - defensive logging
        loop.call_soon_threadsafe(reader.set_exception, exc)
    finally:
        loop.call_soon_threadsafe(reader.feed_eof)
