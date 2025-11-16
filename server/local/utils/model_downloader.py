# -*- coding: utf-8 -*-
"""
Python模型下载器 - 用于本地服务按需下载SenseVoice模型
支持：断点续传、SHA256校验、磁盘空间检查、备用源切换
"""

import os
import hashlib
import logging
import shutil
import platform
from pathlib import Path
from typing import Optional, Callable, List
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)


class ModelDownloader:
    """模型下载器（Python版本）"""
    
    # SenseVoiceSmall模型配置（支持多个下载源）
    SENSEVOICE_SMALL = {
        "name": "SenseVoiceSmall",
        "urls": [
            # 主源：ModelScope
            "https://www.modelscope.cn/api/v1/models/iic/SenseVoiceSmall/repo?Revision=master&FilePath=model.pt",
            # 备用源（可添加其他镜像源）
        ],
        "size": 1_700_000_000,  # 约1.7GB
        "sha256": None,  # 可选校验（暂不启用，避免下载失败）
        "model_id": "iic/SenseVoiceSmall"
    }
    
    def __init__(self, model_config: dict, target_dir: Path):
        """
        Args:
            model_config: 模型配置字典（包含urls, size, name等）
            target_dir: 模型保存目录
        """
        self.config = model_config
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_name = model_config["name"]
        # 支持多个下载源
        urls = model_config.get("urls", [model_config.get("url", "")])
        self.urls: List[str] = urls if isinstance(urls, list) else [urls]
        self.expected_size = model_config.get("size", 0)
        self.sha256 = model_config.get("sha256")
        
        self.chunk_size = 10 * 1024 * 1024  # 10MB分片
        self.timeout = 30
        
    def check_disk_space(self) -> bool:
        """
        检查磁盘可用空间是否足够
        
        Returns:
            bool: 空间是否足够
        """
        try:
            stat = shutil.disk_usage(self.target_dir)
            available_gb = stat.free / (1024**3)
            required_gb = self.expected_size / (1024**3)
            
            # 预留额外空间（1.5倍）
            if stat.free < self.expected_size * 1.5:
                logger.error(
                    f"❌ 磁盘空间不足: 可用{available_gb:.2f}GB, "
                    f"需要{required_gb:.2f}GB (建议预留{required_gb*1.5:.2f}GB)"
                )
                return False
            
            logger.info(f"✅ 磁盘空间充足: 可用{available_gb:.2f}GB")
            return True
        except Exception as e:
            logger.warning(f"无法检查磁盘空间: {e}")
            return True  # 检查失败不阻止下载
    
    def download(
        self,
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        下载模型文件（支持多源切换和断点续传）
        
        Args:
            on_progress: 进度回调函数 (downloaded_bytes, total_bytes)
            
        Returns:
            bool: 下载是否成功
        """
        # 检查磁盘空间
        if not self.check_disk_space():
            return False
        
        target_file = self.target_dir / f"{self.model_name}.pt"
        temp_file = self.target_dir / f"{self.model_name}.pt.part"
        
        # 尝试所有下载源
        for idx, url in enumerate(self.urls):
            try:
                logger.info(f"尝试下载源 [{idx+1}/{len(self.urls)}]: {url[:80]}...")
                if self._download_from_url(url, temp_file, target_file, on_progress):
                    return True
            except Exception as e:
                logger.warning(f"下载源 [{idx+1}] 失败: {e}")
                if idx < len(self.urls) - 1:
                    logger.info(f"切换到备用源 [{idx+2}]...")
                continue
        
        logger.error("❌ 所有下载源均失败")
        return False
    
    def _download_from_url(
        self,
        url: str,
        temp_file: Path,
        target_file: Path,
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """从指定URL下载文件"""
        try:
            # 检查已下载大小
            downloaded = 0
            if temp_file.exists():
                downloaded = temp_file.stat().st_size
                logger.info(f"发现未完成的下载，已下载: {downloaded}/{self.expected_size}")
            
            # 发起HTTP Range请求
            req = Request(url)
            if downloaded > 0:
                req.add_header("Range", f"bytes={downloaded}-")
            
            logger.info(f"开始下载模型: {self.model_name}")
            
            with urlopen(req, timeout=self.timeout) as response:
                # 获取总大小
                content_length = response.headers.get('Content-Length')
                if content_length:
                    total_size = int(content_length) + downloaded
                else:
                    total_size = self.expected_size
                
                logger.info(f"总大小: {total_size / (1024**3):.2f}GB")
                
                # 下载数据
                with open(temp_file, 'ab') as f:
                    chunk_num = 0
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        chunk_num += 1
                        
                        # 每100个chunk更新一次进度（避免频繁回调）
                        if chunk_num % 100 == 0:
                            progress = downloaded / total_size * 100 if total_size > 0 else 0
                            logger.info(f"下载进度: {downloaded / (1024**3):.2f}GB / {total_size / (1024**3):.2f}GB ({progress:.1f}%)")
                            
                            if on_progress:
                                on_progress(downloaded, total_size)
            
            # 校验文件大小
            if self.expected_size > 0 and downloaded != self.expected_size:
                logger.warning(f"文件大小不匹配: {downloaded} != {self.expected_size}")
            
            # SHA256校验（可选）
            if self.sha256:
                logger.info("校验文件SHA256...")
                if not self._verify_sha256(temp_file, self.sha256):
                    raise ValueError("SHA256校验失败")
            
            # 移动到最终位置
            temp_file.rename(target_file)
            logger.info(f"✅ 模型下载完成: {target_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"模型下载失败: {e}")
            return False
    
    def _verify_sha256(self, file_path: Path, expected: str) -> bool:
        """验证文件SHA256"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        
        actual = sha256.hexdigest()
        return actual == expected
    
    @classmethod
    def download_sensevoice_small(
        cls,
        models_dir: Path,
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> Optional[Path]:
        """
        便捷方法：下载SenseVoiceSmall模型
        
        Args:
            models_dir: 模型根目录（例如 /path/to/models）
            on_progress: 进度回调
            
        Returns:
            Path: 模型文件路径，失败则返回None
        """
        target_dir = models_dir / "models" / "iic" / "SenseVoiceSmall"
        downloader = cls(cls.SENSEVOICE_SMALL, target_dir)
        
        model_file = target_dir / "model.pt"
        if model_file.exists():
            logger.info(f"模型已存在: {model_file}")
            return target_dir
        
        success = downloader.download(on_progress)
        return target_dir if success else None


def check_sensevoice_model(models_dir: Path) -> Optional[Path]:
    """
    检查SenseVoice模型是否存在（优先检查本地，再检查ModelScope缓存）
    
    Returns:
        Path: 模型目录路径，不存在则返回None
    """
    # 1. 检查项目本地模型
    model_dir = models_dir / "models" / "iic" / "SenseVoiceSmall"
    if model_dir.exists() and (model_dir / "model.pt").exists():
        logger.info(f"✅ 发现本地模型: {model_dir}")
        return model_dir
    
    # 2. 检查 ModelScope 缓存（FunASR 自动下载位置）
    modelscope_cache = _get_modelscope_cache_path("iic/SenseVoiceSmall")
    if modelscope_cache and modelscope_cache.exists() and (modelscope_cache / "model.pt").exists():
        logger.info(f"✅ 发现 ModelScope 缓存模型: {modelscope_cache}")
        return modelscope_cache
    
    return None


def _get_modelscope_cache_path(model_id: str) -> Optional[Path]:
    """
    获取 ModelScope 缓存路径（跨平台）
    
    Args:
        model_id: 模型ID，例如 "iic/SenseVoiceSmall"
        
    Returns:
        Path: ModelScope 缓存路径，失败则返回None
    """
    try:
        home = Path.home()
        
        # Windows: C:\Users\<User>\.cache\modelscope\hub\models\iic\SenseVoiceSmall
        # Linux/macOS: ~/.cache/modelscope/hub/models/iic/SenseVoiceSmall
        if platform.system() == "Windows":
            cache_root = home / ".cache" / "modelscope" / "hub" / "models"
        else:
            cache_root = home / ".cache" / "modelscope" / "hub" / "models"
        
        # 将 "iic/SenseVoiceSmall" 转换为路径
        model_path = cache_root / model_id.replace("/", os.sep)
        return model_path
    except Exception as e:
        logger.warning(f"无法获取 ModelScope 缓存路径: {e}")
        return None


async def ensure_sensevoice_model(
    models_dir: Path,
    on_progress: Optional[Callable[[int, int], None]] = None,
    use_funasr_auto: bool = True
) -> str:
    """
    确保SenseVoice模型可用（优先使用已下载模型，避免重复下载）
    
    检查顺序：
    1. 项目本地模型（server/models/models/iic/SenseVoiceSmall）
    2. ModelScope 缓存（~/.cache/modelscope/hub/models/iic/SenseVoiceSmall）
    3. FunASR 自动下载（推荐）
    4. 手动下载（备用）
    
    Args:
        models_dir: 模型根目录
        on_progress: 下载进度回调
        use_funasr_auto: 是否优先使用FunASR自动下载机制（推荐）
        
    Returns:
        str: 模型路径或ModelScope ID
        
    Raises:
        RuntimeError: 下载失败且无法回退
    """
    # 1. 检查本地模型（包括项目本地和 ModelScope 缓存）
    local_model = check_sensevoice_model(models_dir)
    if local_model:
        logger.info(f"✅ 使用已下载的模型: {local_model}")
        return str(local_model)
    
    # 2. 如果启用FunASR自动下载，直接返回ModelScope ID
    if use_funasr_auto:
        logger.info("使用FunASR自动下载机制（ModelScope）")
        logger.info("模型将在首次使用时自动下载到 ~/.cache/modelscope/")
        return "iic/SenseVoiceSmall"
    
    # 3. 手动下载模型
    logger.info("开始手动下载SenseVoice模型...")
    downloader = ModelDownloader(
        ModelDownloader.SENSEVOICE_SMALL,
        models_dir / "models" / "iic" / "SenseVoiceSmall"
    )
    
    success = downloader.download(on_progress)
    if success:
        model_path = models_dir / "models" / "iic" / "SenseVoiceSmall"
        logger.info(f"✅ 模型下载成功: {model_path}")
        return str(model_path)
    else:
        # 下载失败，回退到FunASR自动下载
        logger.warning("⚠️ 手动下载失败，回退到FunASR自动下载")
        return "iic/SenseVoiceSmall"
