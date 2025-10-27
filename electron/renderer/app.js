/**
 * 提猫直播助手 - 前端主应用
 * 负责UI交互、数据展示和与后端通信
 */

class LiveAssistantApp {
    constructor() {
        this.serviceUrl = '';
        this.eventSource = null;
        this.isConnected = false;
        this.comments = [];
        this.hotWords = [];
        this.scripts = [];
        this.config = {
            autoScroll: true,
            soundEnabled: true,
            maxComments: 100,
            hotWordsLimit: 20,
            scriptInterval: 30000
        };
        this.intervals = {};
        this.charts = {};
        
        this.init();
    }

    /**
     * 初始化应用
     */
    async init() {
        try {
            // 显示加载指示器
            this.showLoading(true);
            
            // 获取服务URL
            this.serviceUrl = await window.electronAPI.getServiceUrl();
            
            // 初始化UI
            this.initUI();
            
            // 检查后端连接
            await this.checkConnection();
            
            // 启动数据获取
            this.startDataFetching();
            
            // 隐藏加载指示器
            this.showLoading(false);
            
            console.log('应用初始化完成');
        } catch (error) {
            console.error('应用初始化失败:', error);
            this.showNotification('应用初始化失败', 'error');
            this.showLoading(false);
        }
    }

    /**
     * 初始化UI事件监听
     */
    initUI() {
        // 状态显示
        this.updateAppVersion();
        
        // 按钮事件
        this.bindButtonEvents();
        
        // 模态框事件
        this.bindModalEvents();
        
        // 设置默认配置
        this.loadConfig();
        
        console.log('UI初始化完成');
    }

    /**
     * 绑定按钮事件
     */
    bindButtonEvents() {
        // 评论区控制
        document.getElementById('toggle-auto-scroll').addEventListener('click', () => {
            this.config.autoScroll = !this.config.autoScroll;
            this.updateAutoScrollButton();
            this.saveConfig();
        });

        document.getElementById('clear-comments').addEventListener('click', () => {
            this.clearComments();
        });

        // 热词区控制
        document.getElementById('refresh-hot-words').addEventListener('click', () => {
            this.fetchHotWords();
        });

        // AI话术控制
        document.getElementById('generate-script').addEventListener('click', () => {
            this.generateScript();
        });

        document.getElementById('copy-all-scripts').addEventListener('click', () => {
            this.copyAllScripts();
        });

        document.getElementById('export-scripts').addEventListener('click', () => {
            this.exportScripts();
        });

        // 底部控制
        document.getElementById('settings-btn').addEventListener('click', () => {
            this.showSettingsModal();
        });

        document.getElementById('help-btn').addEventListener('click', () => {
            this.showHelpModal();
        });
    }

    /**
     * 绑定模态框事件
     */
    bindModalEvents() {
        const modal = document.getElementById('settings-modal');
        const closeBtn = modal.querySelector('.modal-close');
        const saveBtn = document.getElementById('save-settings');
        const cancelBtn = document.getElementById('cancel-settings');

        closeBtn.addEventListener('click', () => {
            this.hideSettingsModal();
        });

        cancelBtn.addEventListener('click', () => {
            this.hideSettingsModal();
        });

        saveBtn.addEventListener('click', () => {
            this.saveSettings();
        });

        // 点击背景关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideSettingsModal();
            }
        });
    }

    /**
     * 检查后端连接状态
     */
    async checkConnection() {
        try {
            const result = await window.electronAPI.checkServiceHealth();
            
            if (result.success) {
                this.isConnected = true;
                this.updateConnectionStatus('online', '已连接');
                console.log('后端连接正常:', result.data);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            this.isConnected = false;
            this.updateConnectionStatus('offline', '连接失败');
            console.error('后端连接失败:', error);
            throw error;
        }
    }

    /**
     * 更新连接状态显示
     */
    updateConnectionStatus(status, text) {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('status-text');
        
        statusDot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }

    /**
     * 启动数据获取
     */
    startDataFetching() {
        if (!this.isConnected) return;

        // 启动评论流
        this.startCommentStream();
        
        // 定期获取热词
        this.intervals.hotWords = setInterval(() => {
            this.fetchHotWords();
        }, 10000);
        
        // 定期获取AI话术
        this.intervals.scripts = setInterval(() => {
            this.fetchLatestScript();
        }, this.config.scriptInterval);
        
        // 立即获取一次数据
        this.fetchHotWords();
        this.fetchLatestScript();
    }

    /**
     * 启动评论流
     */
    startCommentStream() {
        if (this.eventSource) {
            this.eventSource.close();
        }

        const url = `${this.serviceUrl}/api/comments/stream`;
        this.eventSource = new EventSource(url);

        this.eventSource.onopen = () => {
            console.log('评论流连接已建立');
            this.updateConnectionStatus('online', '评论流已连接');
        };

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'comment') {
                    this.addComment(data.data);
                }
            } catch (error) {
                console.error('解析评论数据失败:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('评论流连接错误:', error);
            this.updateConnectionStatus('connecting', '重新连接中...');
            
            // 重连逻辑
            setTimeout(() => {
                if (this.eventSource.readyState === EventSource.CLOSED) {
                    this.startCommentStream();
                }
            }, 5000);
        };
    }

    /**
     * 添加评论到列表
     */
    addComment(comment) {
        // 添加到数组
        this.comments.unshift(comment);
        
        // 限制数量
        if (this.comments.length > this.config.maxComments) {
            this.comments = this.comments.slice(0, this.config.maxComments);
        }
        
        // 更新UI
        this.renderComments();
        this.updateCommentsStats();
        
        // 声音提示
        if (this.config.soundEnabled) {
            this.playNotificationSound();
        }
    }

    /**
     * 渲染评论列表
     */
    renderComments() {
        const container = document.getElementById('comments-list');
        
        if (this.comments.length === 0) {
            container.innerHTML = `
                <div class="no-comments">
                    <i class="fas fa-comment-slash"></i>
                    <p>暂无评论数据</p>
                    <small>等待直播间评论...</small>
                </div>
            `;
            return;
        }

        const html = this.comments.map(comment => `
            <div class="comment-item">
                <div class="comment-avatar">
                    ${comment.user.charAt(0).toUpperCase()}
                </div>
                <div class="comment-content">
                    <div class="comment-user">${this.escapeHtml(comment.user)}</div>
                    <div class="comment-text">${this.escapeHtml(comment.content)}</div>
                    <div class="comment-time">${window.utils.formatTime(comment.timestamp)}</div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
        
        // 自动滚动
        if (this.config.autoScroll) {
            container.scrollTop = 0;
        }
    }

    /**
     * 更新评论统计
     */
    updateCommentsStats() {
        const totalElement = document.getElementById('total-comments');
        const perMinuteElement = document.getElementById('comments-per-minute');
        
        totalElement.textContent = this.comments.length;
        
        // 计算每分钟评论数
        const oneMinuteAgo = Date.now() - 60000;
        const recentComments = this.comments.filter(c => c.timestamp > oneMinuteAgo);
        perMinuteElement.textContent = recentComments.length;
    }

    /**
     * 清空评论
     */
    clearComments() {
        this.comments = [];
        this.renderComments();
        this.updateCommentsStats();
        this.showNotification('评论已清空', 'info');
    }

    /**
     * 获取热词数据
     */
    async fetchHotWords() {
        try {
            const response = await fetch(`${this.serviceUrl}/api/analysis/hot-words?limit=${this.config.hotWordsLimit}`);
            const result = await response.json();
            
            if (result.success) {
                this.hotWords = result.data;
                this.renderHotWords();
                this.updateHotWordsChart();
            }
        } catch (error) {
            console.error('获取热词失败:', error);
        }
    }

    /**
     * 渲染热词列表
     */
    renderHotWords() {
        const container = document.getElementById('hot-words-list');
        
        if (this.hotWords.length === 0) {
            container.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-chart-bar"></i>
                    <p>暂无热词数据</p>
                    <small>需要更多评论数据进行分析</small>
                </div>
            `;
            return;
        }

        const html = this.hotWords.map((word, index) => `
            <div class="hot-word-item">
                <div class="hot-word-rank ${index < 3 ? 'top-3' : ''}">${index + 1}</div>
                <div class="hot-word-text">${this.escapeHtml(word.word)}</div>
                <div class="hot-word-count">${window.utils.formatNumber(word.count)}</div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    /**
     * 更新热词图表
     */
    updateHotWordsChart() {
        const canvas = document.getElementById('hot-words-chart');
        const ctx = canvas.getContext('2d');
        
        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (this.hotWords.length === 0) return;
        
        // 简单的柱状图
        const maxCount = Math.max(...this.hotWords.map(w => w.count));
        const barWidth = canvas.width / this.hotWords.length;
        const maxBarHeight = canvas.height - 40;
        
        this.hotWords.forEach((word, index) => {
            const barHeight = (word.count / maxCount) * maxBarHeight;
            const x = index * barWidth;
            const y = canvas.height - barHeight - 20;
            
            // 绘制柱子
            ctx.fillStyle = index < 3 ? '#f59e0b' : '#2563eb';
            ctx.fillRect(x + 2, y, barWidth - 4, barHeight);
            
            // 绘制文字
            ctx.fillStyle = '#64748b';
            ctx.font = '10px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(word.word.substring(0, 4), x + barWidth / 2, canvas.height - 5);
        });
    }

    /**
     * 获取最新AI话术
     */
    async fetchLatestScript() {
        try {
            const response = await fetch(`${this.serviceUrl}/api/ai/latest-script`);
            const result = await response.json();
            
            if (result.success && result.data) {
                // 检查是否是新话术
                const exists = this.scripts.find(s => s.id === result.data.id);
                if (!exists) {
                    this.scripts.unshift(result.data);
                    this.renderScripts();
                    this.showNotification('新话术已生成', 'success');
                }
            }
        } catch (error) {
            console.error('获取AI话术失败:', error);
        }
    }

    /**
     * 生成新话术
     */
    async generateScript() {
        try {
            const button = document.getElementById('generate-script');
            const originalHtml = button.innerHTML;
            
            // 显示加载状态
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            button.disabled = true;
            
            const response = await fetch(`${this.serviceUrl}/api/ai/generate-script`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    context: this.hotWords.slice(0, 5).map(w => w.word)
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.scripts.unshift(result.data);
                this.renderScripts();
                this.showNotification('话术生成成功', 'success');
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('生成话术失败:', error);
            this.showNotification('话术生成失败', 'error');
        } finally {
            // 恢复按钮状态
            const button = document.getElementById('generate-script');
            button.innerHTML = '<i class="fas fa-magic"></i>';
            button.disabled = false;
        }
    }

    /**
     * 渲染AI话术列表
     */
    renderScripts() {
        const container = document.getElementById('scripts-list');
        
        if (this.scripts.length === 0) {
            container.innerHTML = `
                <div class="no-scripts">
                    <i class="fas fa-lightbulb"></i>
                    <p>暂无AI话术</p>
                    <small>点击生成按钮创建话术</small>
                </div>
            `;
            return;
        }

        const html = this.scripts.map(script => `
            <div class="script-item ${script.used ? 'used' : ''}">
                <div class="script-header">
                    <span class="script-type">${script.type || '通用'}</span>
                    <div class="script-actions">
                        <button class="script-action" onclick="app.copyScript('${script.id}')" title="复制">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="script-action" onclick="app.markScriptUsed('${script.id}')" title="标记已使用">
                            <i class="fas fa-check"></i>
                        </button>
                    </div>
                </div>
                <div class="script-content">${this.escapeHtml(script.content)}</div>
                <div class="script-meta">
                    <span>生成时间: ${window.utils.formatTime(script.timestamp)}</span>
                    <span>热度: ${script.score || 0}</span>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    /**
     * 复制话术
     */
    async copyScript(scriptId) {
        const script = this.scripts.find(s => s.id === scriptId);
        if (!script) return;

        const success = await window.utils.copyToClipboard(script.content);
        if (success) {
            this.showNotification('话术已复制', 'success');
        } else {
            this.showNotification('复制失败', 'error');
        }
    }

    /**
     * 标记话术已使用
     */
    async markScriptUsed(scriptId) {
        try {
            const response = await fetch(`${this.serviceUrl}/api/ai/mark-used`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ script_id: scriptId })
            });

            const result = await response.json();
            
            if (result.success) {
                const script = this.scripts.find(s => s.id === scriptId);
                if (script) {
                    script.used = true;
                    this.renderScripts();
                    this.showNotification('已标记为使用', 'info');
                }
            }
        } catch (error) {
            console.error('标记话术失败:', error);
            this.showNotification('标记失败', 'error');
        }
    }

    /**
     * 复制所有话术
     */
    async copyAllScripts() {
        const content = this.scripts
            .filter(s => !s.used)
            .map(s => s.content)
            .join('\n\n---\n\n');

        if (!content) {
            this.showNotification('没有可复制的话术', 'warning');
            return;
        }

        const success = await window.utils.copyToClipboard(content);
        if (success) {
            this.showNotification('所有话术已复制', 'success');
        } else {
            this.showNotification('复制失败', 'error');
        }
    }

    /**
     * 导出话术
     */
    exportScripts() {
        const content = this.scripts.map(script => ({
            id: script.id,
            type: script.type,
            content: script.content,
            timestamp: script.timestamp,
            used: script.used,
            score: script.score
        }));

        const jsonContent = JSON.stringify(content, null, 2);
        const filename = `scripts_${new Date().toISOString().slice(0, 10)}.json`;
        
        window.utils.downloadFile(jsonContent, filename, 'application/json');
        this.showNotification('话术已导出', 'success');
    }

    /**
     * 显示设置模态框
     */
    showSettingsModal() {
        const modal = document.getElementById('settings-modal');
        
        // 填充当前设置
        document.getElementById('auto-scroll-setting').checked = this.config.autoScroll;
        document.getElementById('sound-enabled-setting').checked = this.config.soundEnabled;
        document.getElementById('max-comments-setting').value = this.config.maxComments;
        document.getElementById('hot-words-limit-setting').value = this.config.hotWordsLimit;
        document.getElementById('script-interval-setting').value = this.config.scriptInterval / 1000;
        
        modal.classList.add('show');
    }

    /**
     * 隐藏设置模态框
     */
    hideSettingsModal() {
        const modal = document.getElementById('settings-modal');
        modal.classList.remove('show');
    }

    /**
     * 保存设置
     */
    saveSettings() {
        this.config.autoScroll = document.getElementById('auto-scroll-setting').checked;
        this.config.soundEnabled = document.getElementById('sound-enabled-setting').checked;
        this.config.maxComments = parseInt(document.getElementById('max-comments-setting').value);
        this.config.hotWordsLimit = parseInt(document.getElementById('hot-words-limit-setting').value);
        this.config.scriptInterval = parseInt(document.getElementById('script-interval-setting').value) * 1000;
        
        this.saveConfig();
        this.updateAutoScrollButton();
        
        // 重启定时器
        this.restartIntervals();
        
        this.hideSettingsModal();
        this.showNotification('设置已保存', 'success');
    }

    /**
     * 显示帮助模态框
     */
    showHelpModal() {
        // 简单的帮助信息
        alert(`提猫直播助手 v${window.electronAPI.appVersion}

功能说明：
• 实时评论：显示直播间评论流
• 热词分析：分析评论中的热门词汇
• AI话术：基于热词生成互动话术

快捷键：
• Ctrl+R：刷新页面
• F12：开发者工具
• F11：全屏模式

更多帮助请访问项目文档。`);
    }

    /**
     * 重启定时器
     */
    restartIntervals() {
        // 清除旧定时器
        Object.values(this.intervals).forEach(interval => {
            clearInterval(interval);
        });
        
        // 重新启动
        if (this.isConnected) {
            this.intervals.hotWords = setInterval(() => {
                this.fetchHotWords();
            }, 10000);
            
            this.intervals.scripts = setInterval(() => {
                this.fetchLatestScript();
            }, this.config.scriptInterval);
        }
    }

    /**
     * 更新自动滚动按钮状态
     */
    updateAutoScrollButton() {
        const button = document.getElementById('toggle-auto-scroll');
        button.classList.toggle('active', this.config.autoScroll);
        button.title = this.config.autoScroll ? '关闭自动滚动' : '开启自动滚动';
    }

    /**
     * 更新应用版本显示
     */
    updateAppVersion() {
        document.getElementById('app-version').textContent = `v${window.electronAPI.appVersion}`;
        document.getElementById('last-update').textContent = `最后更新: ${new Date().toLocaleTimeString()}`;
    }

    /**
     * 加载配置
     */
    loadConfig() {
        const saved = localStorage.getItem('live-assistant-config');
        if (saved) {
            this.config = { ...this.config, ...JSON.parse(saved) };
        }
        this.updateAutoScrollButton();
    }

    /**
     * 保存配置
     */
    saveConfig() {
        localStorage.setItem('live-assistant-config', JSON.stringify(this.config));
    }

    /**
     * 显示/隐藏加载指示器
     */
    showLoading(show) {
        const indicator = document.getElementById('loading-indicator');
        indicator.classList.toggle('show', show);
    }

    /**
     * 显示通知
     */
    showNotification(message, type = 'info') {
        const container = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        // 自动移除
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    /**
     * 播放通知声音
     */
    playNotificationSound() {
        // 简单的音频提示
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 清理资源
     */
    destroy() {
        // 关闭事件源
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        // 清除定时器
        Object.values(this.intervals).forEach(interval => {
            clearInterval(interval);
        });
        
        console.log('应用资源已清理');
    }
}

// 全局应用实例
let app;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    app = new LiveAssistantApp();
});

// 页面卸载前清理
window.addEventListener('beforeunload', () => {
    if (app) {
        app.destroy();
    }
});