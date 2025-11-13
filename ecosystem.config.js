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
        DISABLE_SSL_VERIFY: '1'
      },
      
      // 实例数量（Python建议单实例，使用uvicorn的workers）
      instances: 1,
      exec_mode: 'fork',
      
      // 自动重启
      autorestart: true,
      watch: false,  // 不监听文件变化（生产环境）
      
      // 最大内存限制（超过后自动重启）
      max_memory_restart: '2G',
      
      // 日志
      error_file: './logs/pm2-error.log',
      out_file: './logs/pm2-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      
      // 重启策略
      min_uptime: '10s',  // 最小运行时间（避免频繁重启）
      max_restarts: 10,   // 最大重启次数
      restart_delay: 4000, // 重启延迟（毫秒）
      
      // 优雅退出
      kill_timeout: 5000,  // 退出超时
      wait_ready: true,    // 等待应用就绪信号
      listen_timeout: 10000 // 监听超时
    }
  ]
};

