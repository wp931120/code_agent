class CodeAgentApp {
    constructor() {
        this.eventSource = null;
        this.isConnected = false;
        this.currentFileContent = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadWorkspaceFiles();
        this.checkServerStatus();
    }

    initializeElements() {
        // DOM元素引用
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.fileTree = document.getElementById('fileTree');
        this.refreshBtn = document.getElementById('refreshBtn');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.fileModal = document.getElementById('fileModal');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalBody = document.getElementById('modalBody');
        this.modalClose = document.getElementById('modalClose');
    }

    bindEvents() {
        // 发送按钮点击事件
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // 输入框事件
        this.chatInput.addEventListener('input', () => this.handleInputChange());
        this.chatInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // 刷新按钮
        this.refreshBtn.addEventListener('click', () => this.loadWorkspaceFiles());
        
        // 快速操作按钮
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-action')) {
                const message = e.target.getAttribute('data-message');
                this.chatInput.value = message;
                this.handleInputChange();
                this.sendMessage();
            }
        });
        
        // 模态框关闭
        this.modalClose.addEventListener('click', () => this.closeModal());
        this.fileModal.addEventListener('click', (e) => {
            if (e.target === this.fileModal) {
                this.closeModal();
            }
        });
        
        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.fileModal.classList.contains('show')) {
                this.closeModal();
            }
        });
    }

    async checkServerStatus() {
        try {
            const response = await fetch('/api/health');
            if (response.ok) {
                this.updateConnectionStatus(true, '已连接');
            } else {
                this.updateConnectionStatus(false, '服务器错误');
            }
        } catch (error) {
            this.updateConnectionStatus(false, '连接失败');
        }
    }

    updateConnectionStatus(connected, message) {
        this.isConnected = connected;
        this.statusDot.className = `status-dot ${connected ? 'connected' : ''}`;
        this.statusText.textContent = message;
    }

    async loadWorkspaceFiles() {
        try {
            this.fileTree.innerHTML = '<div class="loading">加载中...</div>';
            
            const response = await fetch('/api/workspace/files');
            const data = await response.json();
            
            if (data.success) {
                this.renderFileTree(data.files);
            } else {
                this.fileTree.innerHTML = `<div class="loading">加载失败: ${data.error || data.message}</div>`;
            }
        } catch (error) {
            console.error('加载文件列表失败:', error);
            this.fileTree.innerHTML = '<div class="loading">加载失败</div>';
        }
    }

    renderFileTree(files) {
        if (!files || files.length === 0) {
            this.fileTree.innerHTML = '<div class="loading">工作空间为空</div>';
            return;
        }

        // 构建文件树结构
        const fileTree = this.buildFileTree(files);
        this.fileTree.innerHTML = '';
        this.renderTreeNode(fileTree, this.fileTree);
    }

    buildFileTree(files) {
        const tree = {};
        
        files.forEach(file => {
            const parts = file.split(/[\\/]/);
            let current = tree;
            
            parts.forEach((part, index) => {
                if (!current[part]) {
                    current[part] = {
                        name: part,
                        path: parts.slice(0, index + 1).join('/'),
                        isFile: index === parts.length - 1,
                        children: {}
                    };
                }
                current = current[part].children;
            });
        });
        
        return tree;
    }

    renderTreeNode(node, container, level = 0) {
        Object.values(node).forEach(item => {
            const element = document.createElement('div');
            element.className = 'file-item';
            element.style.paddingLeft = `${level * 20 + 12}px`;
            
            const icon = item.isFile ? 'fas fa-file' : 'fas fa-folder';
            const iconClass = item.isFile ? 'file-icon' : 'folder-icon';
            
            element.innerHTML = `
                <i class="${icon} ${iconClass}"></i>
                <span>${item.name}</span>
            `;
            
            if (item.isFile) {
                element.addEventListener('click', () => this.openFile(item.path));
            }
            
            container.appendChild(element);
            
            // 如果是文件夹且有子项，递归渲染
            if (!item.isFile && Object.keys(item.children).length > 0) {
                this.renderTreeNode(item.children, container, level + 1);
            }
        });
    }

    async openFile(filePath) {
        try {
            const response = await fetch(`/api/workspace/file/${encodeURIComponent(filePath)}`);
            const data = await response.json();
            
            if (data.success) {
                // 检查文件扩展名
                const fileExtension = data.filename.toLowerCase().split('.').pop();
                const isHtmlFile = fileExtension === 'html' || fileExtension === 'htm';
                
                this.showFileModal(data.filename, data.content, isHtmlFile);
            } else {
                alert(`打开文件失败: ${data.error}`);
            }
        } catch (error) {
            console.error('打开文件失败:', error);
            alert('打开文件失败');
        }
    }

    showFileModal(filename, content, isHtmlFile = false) {
        this.modalTitle.textContent = filename;
        this.modalBody.innerHTML = '';

        if (isHtmlFile) {
            // 为HTML文件创建iframe进行渲染
            
            // 创建iframe容器来支持16:9宽高比
            const iframeContainer = document.createElement('div');
            iframeContainer.className = 'iframe-container';
            
            const iframe = document.createElement('iframe');
            iframe.srcdoc = content;
            
            iframeContainer.appendChild(iframe);

            // 创建源代码视图
            const sourceContainer = document.createElement('div');
            sourceContainer.className = 'source-container';
            sourceContainer.style.display = 'none'; // 默认隐藏
            sourceContainer.innerHTML = `<pre><code>${this.escapeHtml(content)}</code></pre>`;

            this.modalBody.appendChild(iframeContainer);
            this.modalBody.appendChild(sourceContainer);
            
            // 添加切换按钮
            const toggleContainer = document.createElement('div');
            toggleContainer.className = 'toggle-view-container';
            
            const toggleBtn = document.createElement('button');
            toggleBtn.textContent = '查看源代码';
            toggleBtn.className = 'toggle-view-btn';
            
            let showingSource = false;
            toggleBtn.addEventListener('click', () => {
                showingSource = !showingSource;
                if (showingSource) {
                    iframeContainer.style.display = 'none';
                    sourceContainer.style.display = 'block';
                    toggleBtn.textContent = '查看渲染效果';
                } else {
                    iframeContainer.style.display = 'block';
                    sourceContainer.style.display = 'none';
                    toggleBtn.textContent = '查看源代码';
                }
            });
            
            toggleContainer.appendChild(toggleBtn);
            this.modalBody.appendChild(toggleContainer);
            
        } else {
            // 非HTML文件，显示源代码
            this.modalBody.innerHTML = `<pre><code>${this.escapeHtml(content)}</code></pre>`;
        }
        
        this.fileModal.classList.add('show');
    }

    closeModal() {
        this.fileModal.classList.remove('show');
        this.modalBody.innerHTML = '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    handleInputChange() {
        const hasContent = this.chatInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasContent;
        
        // 自动调整输入框高度
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.chatInput.value.trim()) {
                this.sendMessage();
            }
        }
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || !this.isConnected) return;

        // 禁用输入和发送按钮
        this.chatInput.disabled = true;
        this.sendBtn.disabled = true;
        this.sendBtn.textContent = '发送中...';

        // 清空输入框
        this.chatInput.value = '';
        this.handleInputChange();

        // 隐藏欢迎消息
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }

        // 添加用户消息
        this.addMessage('user', message);

        try {
            // 发送消息到后端
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // 处理SSE流式响应
            await this.handleStreamResponse(response);

        } catch (error) {
            console.error('发送消息失败:', error);
            this.addMessage('assistant', '抱歉，发送消息时出现错误，请稍后重试。');
            
            // 重新启用输入
            this.chatInput.disabled = false;
            this.sendBtn.disabled = false;
            this.sendBtn.textContent = '发送';
        }
    }

    async handleStreamResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessageId = null;
        let currentContent = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        
                        if (data === '[DONE]') {
                            return;
                        }

                        try {
                            const parsed = JSON.parse(data);
                            
                            if (parsed.heartbeat) {
                                continue;
                            }

                            if (parsed.error) {
                                this.addMessage('assistant', `错误: ${parsed.error}`);
                                return;
                            }

                            // 处理不同类型的消息
                            if (parsed.type === 'thinking_start') {
                                // 开始思考，创建思考消息
                                if (!assistantMessageId) {
                                    assistantMessageId = this.addMessage('assistant', '', true); // 标记为思考消息
                                    currentContent = '';
                                }
                            } else if (parsed.type === 'thinking_stream') {
                                // 实时显示思考过程
                                if (!assistantMessageId) {
                                    assistantMessageId = this.addMessage('assistant', '', true); // 标记为思考消息
                                    currentContent = '';
                                }
                                
                                currentContent += parsed.content || '';
                                this.updateMessage(assistantMessageId, currentContent, true); // 启用打字机效果
                            } else if (parsed.type === 'thinking_complete') {
                                // 思考完成，移除打字机效果
                                if (assistantMessageId && currentContent) {
                                    this.updateMessage(assistantMessageId, currentContent, false); // 禁用打字机效果
                                    // 移除思考样式
                                    const messageElement = document.querySelector(`[data-message-id="${assistantMessageId}"]`);
                                    if (messageElement) {
                                        messageElement.classList.remove('thinking');
                                    }
                                }
                            } else if (parsed.type === 'response') {
                                if (!assistantMessageId) {
                                    assistantMessageId = this.addMessage('assistant', '');
                                }
                                
                                currentContent += parsed.content || '';
                                this.updateMessage(assistantMessageId, currentContent);
                            } else if (parsed.type === 'tool_call') {
                                // 显示工具调用信息
                                this.addToolMessage('tool_call', parsed.content || '🔧 调用工具...');
                            } else if (parsed.type === 'tool_result') {
                                // 显示工具执行结果
                                this.addToolMessage('tool_result', parsed.content || '✅ 工具执行完成');
                            } else if (parsed.type === 'final_answer') {
                                // 显示最终答案并结束对话
                                this.addMessage('assistant', parsed.content || '任务完成');
                                
                                // 标记最后一个工具容器为完成状态
                                this.markToolContainerCompleted();
                                
                                // 任务完成，重新启用输入
                                this.chatInput.disabled = false;
                                this.sendBtn.disabled = false;
                                this.sendBtn.textContent = '发送';
                                return;
                            } else if (parsed.type === 'done') {
                                // 对话结束，重新启用输入
                                this.chatInput.disabled = false;
                                this.sendBtn.disabled = false;
                                this.sendBtn.textContent = '发送';
                                
                                // 标记最后一个工具容器为完成状态
                                this.markToolContainerCompleted();
                                return;
                            }
                        } catch (parseError) {
                            console.error('解析SSE数据失败:', parseError, 'Data:', data);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('读取流式响应失败:', error);
            if (!assistantMessageId) {
                this.addMessage('assistant', '抱歉，接收响应时出现错误。');
            }
        }
    }

    // 处理换行符转换为HTML
    formatContentWithLineBreaks(content) {
        // 将\n\n转换为<br><br>，\n转换为<br>
        return content.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
    }

    addMessage(sender, content, isThinking = false) {
        const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.setAttribute('data-message-id', messageId);
        messageDiv.id = messageId;
        
        // 如果是思考消息，添加thinking类
        if (isThinking && sender === 'assistant') {
            messageDiv.classList.add('thinking');
        }
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        if (sender === 'user') {
            avatar.innerHTML = '<i class="fas fa-user"></i>';
        } else if (sender === 'system') {
            avatar.innerHTML = '<i class="fas fa-cog"></i>';
        } else {
            avatar.innerHTML = '<i class="fas fa-robot"></i>';
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = this.formatContentWithLineBreaks(content);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageId;
    }

    addToolMessage(type, content) {
        const messageId = 'tool_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        // 查找或创建工具执行容器
        let toolContainer = document.querySelector('.tool-execution-container:last-child');
        
        if (!toolContainer || toolContainer.classList.contains('completed')) {
            // 创建新的工具执行容器
            toolContainer = document.createElement('div');
            toolContainer.className = 'message system tool-execution-container';
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.innerHTML = '<i class="fas fa-tools"></i>';
            
            const contentWrapper = document.createElement('div');
            contentWrapper.className = 'message-content';
            
            const header = document.createElement('div');
            header.className = 'tool-header';
            header.innerHTML = '<i class="fas fa-cogs"></i> 工具执行过程';
            
            const scrollContainer = document.createElement('div');
            scrollContainer.className = 'tool-scroll-container';
            
            const processContainer = document.createElement('div');
            processContainer.className = 'tool-process-container';
            
            scrollContainer.appendChild(processContainer);
            contentWrapper.appendChild(header);
            contentWrapper.appendChild(scrollContainer);
            
            toolContainer.appendChild(avatar);
            toolContainer.appendChild(contentWrapper);
            
            this.chatMessages.appendChild(toolContainer);
        }
        
        // 添加工具步骤
        const processContainer = toolContainer.querySelector('.tool-process-container');
        const stepDiv = document.createElement('div');
        stepDiv.className = `tool-step ${type}`;
        stepDiv.id = messageId;
        
        const stepIcon = document.createElement('div');
        stepIcon.className = 'tool-step-icon';
        if (type === 'tool_call') {
            stepIcon.innerHTML = '<i class="fas fa-play"></i>';
        } else {
            stepIcon.innerHTML = '<i class="fas fa-check"></i>';
        }
        
        const stepContent = document.createElement('div');
        stepContent.className = 'tool-step-content';
        stepContent.innerHTML = this.formatContentWithLineBreaks(content);
        
        stepDiv.appendChild(stepIcon);
        stepDiv.appendChild(stepContent);
        processContainer.appendChild(stepDiv);
        
        // 滚动到最新步骤
        const scrollContainer = toolContainer.querySelector('.tool-scroll-container');
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
        
        this.scrollToBottom();
        
        return messageId;
     }

    markToolContainerCompleted() {
        const lastToolContainer = document.querySelector('.tool-execution-container:last-child');
        if (lastToolContainer && !lastToolContainer.classList.contains('completed')) {
            lastToolContainer.classList.add('completed');
        }
    }

    updateMessage(messageId, content, showTypingCursor = false) {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            const contentDiv = messageElement.querySelector('.message-content');
            if (contentDiv) {
                contentDiv.innerHTML = this.formatContentWithLineBreaks(content);
                
                // 添加或移除打字机光标效果
                if (showTypingCursor) {
                    contentDiv.classList.add('typing-cursor');
                } else {
                    contentDiv.classList.remove('typing-cursor');
                }
                
                this.scrollToBottom();
            }
        }
    }

    addThinkingIndicator() {
        const thinkingId = 'thinking_' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.id = thinkingId;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        return thinkingId;
    }

    removeThinkingIndicator(thinkingId) {
        const element = document.getElementById(thinkingId);
        if (element) {
            element.remove();
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new CodeAgentApp();
});