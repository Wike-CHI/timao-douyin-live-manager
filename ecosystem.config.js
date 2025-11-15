// PM2 配置文件 - 提猫直播助手后端服务
module.exports = {
  apps: [
    {
      // 应用名称
      name: 'timao-backend',
      
      // 启动脚本（使用Python的uvicorn运行FastAPI）
      script: 'python',
      args: '-m uvicorn server.app.main:app --host 0.0.0.0 --port 11111 --workers 1',
      
      // 工作目录
      cwd: '/www/wwwroot/wwwroot/timao-douyin-live-manager',
      
      // 解释器（使用系统Python或虚拟环境）
      interpreter: 'none',
      
      // 环境变量
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/www/wwwroot/wwwroot/timao-douyin-live-manager',
        DEBUG: 'false',
        BACKEND_PORT: '11111',
        DISABLE_SSL_VERIFY: '1',
        
        // ========== SenseVoice + VAD 模型配置 ==========
        // 模型根目录
        MODEL_ROOT: '/www/wwwroot/wwwroot/timao-douyin-live-manager/server/models/models/iic',
        
        // SenseVoice 模型路径
        SENSEVOICE_MODEL_PATH: '/www/wwwroot/wwwroot/timao-douyin-live-manager/server/models/models/iic/SenseVoiceSmall',
        
        // VAD 模型路径
        VAD_MODEL_PATH: '/www/wwwroot/wwwroot/timao-douyin-live-manager/server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch',
        
        // 模型加载配置
        ENABLE_MODEL_PRELOAD: '1',  // 启用模型预加载
        MODEL_CACHE_DIR: '/www/wwwroot/wwwroot/timao-douyin-live-manager/.cache/modelscope',
        
        // VAD 参数优化
        LIVE_VAD_CHUNK_SEC: '1.6',        // VAD 分块时长
        LIVE_VAD_MIN_SILENCE_SEC: '0.50',  // 最小静音时长
        LIVE_VAD_MIN_SPEECH_SEC: '0.30',   // 最小语音时长
        LIVE_VAD_HANGOVER_SEC: '0.40',     // 挂起时间
        LIVE_VAD_MIN_RMS: '0.015',         // RMS 阈值
        LIVE_VAD_MUSIC_DETECT: '1',        // 启用音乐检测
        
        // PyTorch 配置（优化CPU推理）
        OMP_NUM_THREADS: '4',              // OpenMP 线程数
        MKL_NUM_THREADS: '4',              // MKL 线程数
        PYTORCH_CPU_ALLOC_CONF: 'max_split_size_mb:512',  // PyTorch 内存分配
        
        // ModelScope 配置
        MODELSCOPE_CACHE: '/www/wwwroot/wwwroot/timao-douyin-live-manager/.cache/modelscope',
        MODELSCOPE_SDK_DEBUG: '0',
        
        // 日志配置
        LOG_LEVEL: 'INFO',
        ENABLE_MODEL_LOG: '1',  // 启用模型加载日志
        
        // ========== Redis 配置 ==========
        REDIS_ENABLED: 'True',
        REDIS_HOST: 'localhost',
        REDIS_PORT: '6379',
        REDIS_PASSWORD: '',
        REDIS_DB: '0',
        REDIS_MAX_CONNECTIONS: '50',
        REDIS_CACHE_TTL: '3600',
        
        // Redis 批量入库配置
        REDIS_BATCH_ENABLED: '1',
        REDIS_BATCH_SIZE: '100',
        REDIS_BATCH_INTERVAL: '10.0',
        
        // 弹幕批量入库配置
        DANMU_BATCH_SIZE: '500',
        DANMU_BATCH_INTERVAL: '5.0',
        
        // AI 分析缓存配置
        AI_CACHE_ENABLED: '1',
        AI_CACHE_TTL: '3600',
        
        // 性能监控配置
        MONITOR_ENABLED: '1',
        MONITOR_INTERVAL: '30.0',
        MYSQL_CONN_WARNING: '45',
        REDIS_MEMORY_WARNING_MB: '1800',
        PROCESS_MEMORY_WARNING_MB: '4000'
      },
      
      // 实例数量（Python建议单实例，使用uvicorn的workers）
      instances: 1,
      exec_mode: 'fork',
      
      // 自动重启
      autorestart: true,
      watch: false,  // 不监听文件变化（生产环境）
      
      // 最大内存限制（超过后自动重启）
      // SenseVoice Small (~2.3GB) + VAD (~140MB) + 运行内存
      // 提升到 4.5GB，为数据累积和峰值使用预留空间
      max_memory_restart: '4.5G',
      
      // 日志
      error_file: './logs/pm2-error.log',
      out_file: './logs/pm2-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      
      // 重启策略（优化参数，避免频繁重启）
      min_uptime: '30s',  // 最小运行时间（从10s增加到30s）
      max_restarts: 5,   // 最大重启次数（从10减少到5，防止异常循环）
      restart_delay: 10000, // 重启延迟（从4000ms增加到10000ms，给清理更多时间）
      
      // 优雅退出
      kill_timeout: 5000,  // 退出超时
      wait_ready: true,    // 等待应用就绪信号
      listen_timeout: 10000 // 监听超时
    }
  ]
};

