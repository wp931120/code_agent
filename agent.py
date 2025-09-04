import json
import re
from typing import List, Dict, Any
from openai import OpenAI
from tools import get_tools_description, execute_tool, validate_tools_consistency
from config import Config
from prompt import SYSTEM_PROMPT

class CodeAgent:
    """简化的智能代码助手"""
    
    def __init__(self):
        # 验证工具定义一致性
        is_valid, message = validate_tools_consistency()
        if not is_valid:
            raise RuntimeError(f"工具定义验证失败: {message}")
        
        self.client = OpenAI(
            base_url=Config.API_BASE_URL,
            api_key=Config.API_KEY
        )
        self.memory: List[Dict[str, Any]] = []
        self.system_prompt = self._build_system_prompt()
        self.original_task = ""  # 保存原始任务
        self.task_completed = False  # 任务完成标志
        
        print(f"✓ CodeAgent 初始化完成，工具定义验证通过: {message}")
    

    def run(self, task: str, response_queue=None) -> str:
        """运行任务"""
        try:
            self.original_task = task  # 保存原始任务
            self.task_completed = False
            self.memory = [{"role": "user", "content": task}]
            
            for i in range(Config.MAX_ITERATIONS):
                print(f"\n=== 第 {i+1} 轮 ===")
                
                # 获取模型响应
                print(f"思考: ", end="", flush=True)
                
                # 发送开始思考信号到前端
                if response_queue:
                    response_queue.put({
                        'type': 'thinking_start',
                        'content': '🤔 正在思考...'
                    })
                
                response, action, tool_result = self._get_response_with_action(response_queue)

                if not action:
                    # 如果没有解析到action，可能是模型认为任务已完成
                    final_answer = "任务已完成"
                    if response_queue:
                        response_queue.put({'type': 'final_answer', 'content': final_answer})
                        response_queue.put({'type': 'done'})
                    return final_answer
                
                tool_name = action["name"]
                arguments = action.get("arguments", {})
                
                # 处理final_answer
                if tool_name == "final_answer":
                    final_answer = arguments.get("answer", "任务完成")
                    # 先添加assistant的response到记忆
                    self.memory.append({"role": "assistant", "content": response})
                    
                    if response_queue:
                        response_queue.put({'type': 'final_answer', 'content': final_answer})
                        response_queue.put({'type': 'done'})
                    return final_answer
                
                # 处理其他工具的执行结果
                if tool_result is not None:
                    # 添加到记忆：先添加assistant的思考过程，再添加工具执行结果
                    self.memory.append({"role": "assistant", "content": response})
                    # 将工具执行结果作为assistant消息添加到记忆中
                    tool_result_message = f"工具执行结果: {tool_result}"
                    self.memory.append({"role": "assistant", "content": tool_result_message})
                    # 添加观察结果和任务提醒，将工具结果拼接到Observation后面
                    observation_with_reminder = f"提醒：你的原始任务是：{self.original_task}。请检查是否已完成此任务，如果已完成请使用final_answer结束。"
                    self.memory.append({"role": "user", "content": observation_with_reminder})
            
            # 达到最大迭代次数时的处理
            final_message = "达到最大迭代次数，任务可能未完全完成"
            if response_queue:
                response_queue.put({'type': 'final_answer', 'content': final_message})
                response_queue.put({'type': 'done'})
            return final_message
            
        except Exception as e:
            error_message = f"任务执行失败: {str(e)}"
            print(f"\n任务执行失败: {str(e)}")
            if response_queue:
                response_queue.put({'type': 'final_answer', 'content': error_message})
                response_queue.put({'type': 'done'})
            return error_message

    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
   
        tools_desc = get_tools_description()
        return SYSTEM_PROMPT.format(tools=tools_desc)
    
    def _get_response_with_action(self, response_queue=None) -> tuple[str, dict, str]:
        """获取模型响应、解析Action并执行工具，返回响应、action和工具结果"""
        try:
            # 构建消息列表
            messages = [{"role": "system", "content": self.system_prompt}] + self.memory
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=messages,
                temperature=0.1,
                stream=True
            )
            
            # 收集流式响应
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
                    # 实时发送思考过程到前端
                    if response_queue:
                        response_queue.put({
                            'type': 'thinking_stream',
                            'content': content
                        })
                    # 检查是否遇到Observation，如果是则停止生成
                    if "Observation:" in full_response:
                        break
            
            print()  # 换行
            
            # 发送思考完成信号
            if response_queue:
                response_queue.put({
                    'type': 'thinking_complete',
                    'content': full_response
                })
            
            # 解析Action
            action = self._extract_action(full_response)
            
            # 如果解析到了action，执行工具并返回结果
            tool_result = None
            if action:
                tool_name = action["name"]
                arguments = action.get("arguments", {})
                
                # 发送工具调用信息到前端
                if response_queue:
                    response_queue.put({
                        'type': 'tool_call', 
                        'content': f'🔧 调用工具: {tool_name}\n📝 参数: {arguments}'
                    })
                
                print(f"工具: {tool_name}")
                print(f"参数: {arguments}")
                
                # 执行工具
                if tool_name != "final_answer":
                    tool_result = execute_tool(tool_name, arguments)
                    # 发送工具执行结果到前端
                    if response_queue:
                        response_queue.put({'type': 'tool_result', 'content': f'✅ 执行结果:\n{str(tool_result)}'})
                        response_queue.put({'type': 'tool_end'})

                        response_queue.put({'type': 'thinking_stream', 'content': f':\n{str(tool_result)}\n\n'})
            
            return full_response, action, tool_result
            
        except Exception as e:
            print(f"\n获取响应失败: {str(e)}")
            if response_queue:
                response_queue.put({
                    'type': 'final_answer',
                    'content': f"获取响应失败: {str(e)}"
                })
                response_queue.put({'type': 'done'})
            return "", None, None
    
    def _extract_action(self, response: str) -> dict:
        """从响应中提取Action"""
        try:
            # 查找Action块的开始位置
            action_start = response.find('Action:')
            if action_start == -1:
                return None
            
            # 从Action:后开始查找JSON
            json_start = response.find('{', action_start)
            if json_start == -1:
                return None
            
            # 使用括号计数来找到完整的JSON
            brace_count = 0
            json_end = json_start
            
            for i in range(json_start, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if brace_count != 0:
                return None
            
            # 提取JSON字符串并解析
            action_str = response[json_start:json_end]
            action = json.loads(action_str)
            return action
            
        except Exception as e:
            print(f"解析Action失败: {str(e)}")
            return None


if __name__ == "__main__":
    agent = CodeAgent()
    result = agent.run("帮我写一个简单的HTML页面，包含一个输入框和按钮")
    print(f"\n最终结果: {result}")