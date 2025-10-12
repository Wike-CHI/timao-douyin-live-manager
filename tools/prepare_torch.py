"""Ensure the correct torch build (CPU/GPU) is installed for the current environment."""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from typing import Optional

CUDA_SUFFIX_DEFAULT = "cu121"  # default for RTX 40 series
CPU_SUFFIX = "cpu"
TORCH_PACKAGES = ("torch", "torchvision", "torchaudio")
TORCH_INDEX_TEMPLATE = "https://download.pytorch.org/whl/{suffix}"


def run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("pip 不可用，请先安装 pip: python -m ensurepip --upgrade") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"命令执行失败: {' '.join(cmd)}") from exc


def torch_version() -> Optional[str]:
    try:
        import torch  # type: ignore
        return torch.__version__
    except Exception:
        return None


def has_cuda() -> bool:
    try:
        import torch  # type: ignore
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def install_torch(suffix: str) -> None:
    index_url = TORCH_INDEX_TEMPLATE.format(suffix=suffix)
    pip_bootstrap = os.environ.get("PYTHONENSUREPIP", "0")
    if pip_bootstrap == "1":
        try:
            run([sys.executable, "-m", "ensurepip", "--upgrade"])
        except RuntimeError as err:
            print(f"[prepare_torch] ensurepip 失败: {err}")
    try:
        run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except RuntimeError as err:
        print(f"[prepare_torch] pip 不可用: {err}")
        raise
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--index-url",
        index_url,
        *TORCH_PACKAGES,
    ]
    run(cmd)


def ensure_torch() -> None:
    force = os.environ.get("FORCE_TORCH_MODE", "auto").lower()
    suffix_override = os.environ.get("TORCH_CUDA_SUFFIX")

    version = torch_version()
    if force == "cpu":
        if version and not has_cuda():
            return
        install_torch(CPU_SUFFIX)
        return

    if version:
        if has_cuda():
            return
        if force != "cpu":
            install_torch(suffix_override or CUDA_SUFFIX_DEFAULT)
            return

    if force == "cpu":
        install_torch(CPU_SUFFIX)
    else:
        try:
            install_torch(suffix_override or CUDA_SUFFIX_DEFAULT)
        except subprocess.CalledProcessError:
            install_torch(CPU_SUFFIX)


def main() -> None:
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    if py_ver not in {"3.10", "3.11", "3.12"}:
        print(f"[prepare_torch] Unsupported Python version: {py_ver}")
        return
    if platform.system().lower() == "windows":
        os.environ.setdefault("CUDA_SUFFIX", CUDA_SUFFIX_DEFAULT)
    ensure_torch()


if __name__ == "__main__":
    main()
