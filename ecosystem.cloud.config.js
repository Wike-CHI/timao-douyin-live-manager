// PM2 配置文件 - 提猫直播助手云端服务
// 功能：用户系统、订阅系统、支付系统、积分系统
// 部署：服务器云端运行（必须联网）
module.exports = {
  apps: [
    {
      // 应用名称
      name: 'timao-cloud',
      
      // 启动脚本（云端服务入口）
      script: 'python',
      args: '-m uvicorn server.cloud.main:app --host 0.0.0.0 --port 15000 --workers 1',
      
      // 工作目录
      cwd: '/www/wwwroot/wwwroot/timao-douyin-live-manager',
      
      // 解释器（使用系统Python）
      interpreter: 'none',
      
      // 环境变量
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/www/wwwroot/wwwroot/timao-douyin-live-manager',
        DEBUG: 'false',
        
        // ========== 云端服务配置 ==========
        CLOUD_PORT: '15000',
        SERVICE_TYPE: 'cloud',
        
        // ========== 数据库配置 ==========
        DB_TYPE: 'mysql',
        MYSQL_HOST: 'rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com',
        MYSQL_PORT: '3306',
        MYSQL_USER: 'timao',
        MYSQL_PASSWORD: 'timao20251102Xjys',
        MYSQL_DATABASE: 'timao',
        
        // 数据库连接池配置
        DB_POOL_SIZE: '20',
        DB_MAX_OVERFLOW: '10',
        DB_POOL_TIMEOUT: '30',
        DB_POOL_RECYCLE: '3600',
        
        // ========== 安全配置 ==========
        SECRET_KEY: 'khDmKFNDdoga4MwDMfATn_IMemtQJtbDDY2rllTelK01sRQNhNSCbBLNXzdHg3XKB1uj16qNQXCzZJehtxaPiQ',
        ENCRYPTION_KEY: 'XbgQ1IS8ySyrZm-Y7BXCDyDopLJQI_RXe74X9vcE6VM',
        JWT_ALGORITHM: 'HS256',
        ACCESS_TOKEN_EXPIRE_MINUTES: '30',
        REFRESH_TOKEN_EXPIRE_DAYS: '7',
        
        // ========== AI配置（用于积分消耗统计）==========
        QWEN_API_KEY: 'sk-bc399748091f47d5bc40f8318464daa1',
        QWEN_BASE_URL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        QWEN_MODEL: 'qwen3-max',
        
        GEMINI_API_KEY: 'sk-yZyfgpg5rgF9JL8k818cBe9e62364213904139E91c2fD7Fa',
        AIHUBMIX_BASE_URL: 'https://aihubmix.com/v1',
        GEMINI_MODEL: 'gemini-2.5-flash-preview-09-2025',
        
        XUNFEI_API_KEY: 'vSVKxhHtIqoQhSruqkeQ:iyfRXCotDrEIDtwdrBuU',
        XUNFEI_BASE_URL: 'https://spark-api-open.xf-yun.com/v1',
        XUNFEI_MODEL: 'lite',
        
        // ========== Redis配置（可选，用于缓存和会话）==========
        REDIS_ENABLED: 'True',
        REDIS_HOST: 'localhost',
        REDIS_PORT: '6379',
        REDIS_PASSWORD: '',
        REDIS_DB: '0',
        REDIS_MAX_CONNECTIONS: '20',
        REDIS_CACHE_TTL: '3600',
        
        // ========== 支付配置 ==========
        // 支付宝配置（待域名备案后配置）
        ALIPAY_APP_ID: '',
        ALIPAY_PRIVATE_KEY: '',
        ALIPAY_PUBLIC_KEY: '',
        ALIPAY_NOTIFY_URL: '',
        ALIPAY_RETURN_URL: '',
        
        // 微信支付配置（待域名备案后配置）
        WECHAT_APP_ID: '',
        WECHAT_MCH_ID: '',
        WECHAT_API_KEY: '',
        WECHAT_NOTIFY_URL: '',
        
        // ========== 订阅配置 ==========
        DEFAULT_FREE_QUOTA: '100',          // 免费用户默认积分
        DEFAULT_TRIAL_DAYS: '7',            // 试用期天数
        SUBSCRIPTION_CHECK_INTERVAL: '3600', // 订阅状态检查间隔（秒）
        
        // ========== CORS配置 ==========
        CORS_ORIGINS: '*',  // 生产环境改为具体域名
        
        // ========== 日志配置 ==========
        LOG_LEVEL: 'INFO',
        LOG_FORMAT: 'json',
        LOG_FILE: './logs/cloud-service.log',
        
        // ========== 性能监控 ==========
        MONITOR_ENABLED: '1',
        MONITOR_INTERVAL: '30.0',
        MYSQL_CONN_WARNING: '15',           // MySQL连接池告警阈值
        PROCESS_MEMORY_WARNING_MB: '512'    // 内存告警阈值（云端目标<512MB）
      },
      
      // 实例数量（云端服务轻量级，单实例足够）
      instances: 1,
      exec_mode: 'fork',
      
      // 自动重启
      autorestart: true,
      watch: false,  // 不监听文件变化（生产环境）
      
      // 最大内存限制（云端轻量级服务）
      max_memory_restart: '600M',
      
      // 日志
      error_file: './logs/cloud-error.log',
      out_file: './logs/cloud-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      
      // 重启策略
      min_uptime: '30s',
      max_restarts: 10,
      restart_delay: 5000,
      
      // 优雅退出
      kill_timeout: 5000,
      wait_ready: true,
      listen_timeout: 10000
    }
  ]
};

