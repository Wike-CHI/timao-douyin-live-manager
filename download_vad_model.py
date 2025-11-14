#!/usr/bin/env python3
"""
下载 VAD 模型到 server/models 目录
"""
import os
from pathlib import Path
from modelscope.hub.snapshot_download import snapshot_download  # pyright: ignore[reportMissingImports]

# 设置路径
project_root = Path(__file__).parent
models_dir = project_root / "server" / "models"
cache_dir = models_dir / ".cache" / "modelscope" / "iic"
models_iic_dir = models_dir / "models" / "iic"

# VAD 模型信息
vad_model_id = "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
vad_model_name = "speech_fsmn_vad_zh-cn-16k-common-pytorch"

print("=" * 60)
print("开始下载 VAD 模型")
print("=" * 60)
print(f"模型ID: {vad_model_id}")
print(f"缓存目录: {cache_dir}")
print(f"链接目录: {models_iic_dir}")
print()

# 创建目录
cache_dir.mkdir(parents=True, exist_ok=True)
models_iic_dir.mkdir(parents=True, exist_ok=True)

try:
    # 设置环境变量指定缓存目录
    os.environ['MODELSCOPE_CACHE'] = str(models_dir / ".cache" / "modelscope")
    
    print("正在从 ModelScope 下载 VAD 模型...")
    print("(首次下载需要一些时间，请耐心等待)")
    print()
    
    # 下载模型
    model_path = snapshot_download(
        model_id=vad_model_id,
        cache_dir=str(cache_dir),
        revision='master'
    )
    
    print(f"✅ 模型下载成功！")
    print(f"模型位置: {model_path}")
    print()
    
    # 创建软链接
    link_path = models_iic_dir / vad_model_name
    if link_path.exists() or link_path.is_symlink():
        print(f"删除旧链接: {link_path}")
        link_path.unlink()
    
    # 获取实际模型路径
    actual_model_path = cache_dir / vad_model_name
    if not actual_model_path.exists():
        # 可能下载到了子目录
        actual_model_path = Path(model_path)
    
    print(f"创建软链接: {link_path} -> {actual_model_path}")
    link_path.symlink_to(actual_model_path)
    
    print()
    print("=" * 60)
    print("✅ VAD 模型安装完成！")
    print("=" * 60)
    print(f"模型路径: {link_path}")
    print(f"实际位置: {actual_model_path}")
    print()
    print("验证文件:")
    if link_path.exists():
        for file in link_path.iterdir():
            print(f"  - {file.name}")
    
except Exception as e:
    print(f"❌ 下载失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

