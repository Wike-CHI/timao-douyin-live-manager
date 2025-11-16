# -*- coding: utf-8 -*-
"""
Python模型下载器 - 用于本地服务按需下载SenseVoice模型
简化版本，支持断点续传和SHA256校验
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Callable
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)


class ModelDownloader:
    """模型下载器（Python版本）"""
    
    # SenseVoiceSmall模型配置
    SENSEVOICE_SMALL = {
        "name": "SenseVoiceSmall",
        "url": "https://www.modelscope.cn/api/v1/models/iic/SenseVoiceSmall/repo?Revision=master&FilePath=model.pt",
        "size": 1_700_000_000,  # 约1.7GB
        "sha256": None,  # 可选校验
        "model_id": "iic/SenseVoiceSmall"
    }
    
    def __init__(self, model_config: dict, target_dir: Path):
        """
        Args:
            model_config: 模型配置字典（包含url, size, name等）
            target_dir: 模型保存目录
        """
        self.config = model_config
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_name = model_config["name"]
        self.url = model_config["url"]
        self.expected_size = model_config.get("size", 0)
        self.sha256 = model_config.get("sha256")
        
        self.chunk_size = 10 * 1024 * 1024  # 10MB分片
        self.timeout = 30
        
    def download(
        self,
        on_progress: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        下载模型文件
        
        Args:
            on_progress: 进度回调函数 (downloaded_bytes, total_bytes)
            
        Returns:
            bool: 下载是否成功
        """
        target_file = self.target_dir / f"{self.model_name}.pt"
        temp_file = self.target_dir / f"{self.model_name}.pt.part"
        
        try:
            # 检查已下载大小
            downloaded = 0
            if temp_file.exists():
                downloaded = temp_file.stat().st_size
                logger.info(f"发现未完成的下载，已下载: {downloaded}/{self.expected_size}")
            
            # 发起HTTP Range请求
            req = Request(self.url)
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
    检查SenseVoice模型是否存在
    
    Returns:
        Path: 模型目录路径，不存在则返回None
    """
    model_dir = models_dir / "models" / "iic" / "SenseVoiceSmall"
    if model_dir.exists() and (model_dir / "model.pt").exists():
        return model_dir
    return None
