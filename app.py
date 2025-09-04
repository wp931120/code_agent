from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import json
import threading
import queue
import os
from agent import CodeAgent
from config import Config

app = Flask(__name__, static_folder='frontend', template_folder='frontend')
CORS(app)

# 全局Agent实例
agent = CodeAgent()

@app.route('/')
def index():
    """提供前端页面"""
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """提供静态文件"""
    if filename.startswith('@vite/'):
        return '', 404
    response = send_from_directory('frontend', filename)
    # 对JavaScript和CSS文件禁用缓存
    if filename.endswith(('.js', '.css')):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': '缺少消息内容'}), 400
        
        user_message = data['message']
        response_queue = queue.Queue()
        
        def run_agent():
            """在新线程中运行Agent"""
            try:
                agent.run(user_message, response_queue)
            except Exception as e:
                response_queue.put({'type': 'error', 'content': str(e)})
        
        def generate_sse():
            """生成SSE格式的流式响应"""
            # 启动Agent线程
            agent_thread = threading.Thread(target=run_agent)
            agent_thread.daemon = True
            agent_thread.start()
            
            while True:
                try:
                    # 获取响应数据
                    response_data = response_queue.get(timeout=1)
                    
                    if response_data['type'] == 'done':
                        yield f"data: [DONE]\n\n"
                        break
                    elif response_data['type'] == 'error':
                        yield f"data: {json.dumps({'error': response_data['content']})}\n\n"
                        break
                    else:
                        # 发送所有类型的消息
                        yield f"data: {json.dumps(response_data)}\n\n"
                        
                except queue.Empty:
                    # 发送心跳
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
                    continue
        
        return Response(
            generate_sse(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workspace/files', methods=['GET'])
def get_workspace_files():
    """获取工作空间文件列表"""
    try:
        if not os.path.exists(Config.WORKSPACE_PATH):
            return jsonify({'success': False, 'files': [], 'message': 'Workspace not initialized'})
        
        files = []
        for root, dirs, filenames in os.walk(Config.WORKSPACE_PATH):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), Config.WORKSPACE_PATH)
                files.append(rel_path)
        
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/workspace/file/<path:filename>', methods=['GET'])
def get_workspace_file(filename):
    """获取工作空间文件内容"""
    try:
        full_path = os.path.join(Config.WORKSPACE_PATH, filename)
        
        # 安全检查：防止路径遍历攻击
        if not os.path.commonpath([full_path, Config.WORKSPACE_PATH]) == Config.WORKSPACE_PATH:
            return jsonify({'success': False, 'error': 'File path is outside workspace'}), 400
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'success': True, 'content': content, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({'status': 'ok', 'message': 'Agent服务正常运行'})

if __name__ == '__main__':
    print("🚀 启动 Code Agent 前端服务...")
    print("📍 访问地址: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)