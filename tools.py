import os
import json
from typing import Dict, Any
from config import Config

# 工具定义结构版本
TOOLS_VERSION = "1.0.0"

# 标准化工具定义模板
class ToolDefinition:
    """工具定义的标准化结构"""
    def __init__(self, name: str, description: str, required_params: list, optional_params: dict = None):
        self.name = name
        self.description = description
        self.required_params = required_params
        self.optional_params = optional_params or {}
        self.all_params = {**{param: f"必需参数: {param}" for param in required_params}, **self.optional_params}
    
    def to_dict(self):
        return {
            "description": self.description,
            "required_parameters": self.required_params,
            "parameters": self.all_params
        }
    
    def to_prompt_format(self):
        """生成稳定的prompt格式"""
        lines = [f"- **{self.name}**: {self.description}"]
        
        if self.required_params:
            lines.append("  必需参数:")
            for param in self.required_params:
                param_desc = self.all_params.get(param, f"必需参数: {param}")
                lines.append(f"    - {param}: {param_desc}")
        
        if self.optional_params:
            lines.append("  可选参数:")
            for param, desc in self.optional_params.items():
                lines.append(f"    - {param}: {desc}")
        
        return "\n".join(lines)

# 使用标准化结构定义工具
_TOOL_DEFINITIONS = [
    ToolDefinition(
        name="write_file",
        description="将内容写入文件",
        required_params=["file_path", "content"],
        optional_params={
            "file_path": "文件路径（相对于工作区）",
            "content": "要写入的文件内容"
        }
    ),
    ToolDefinition(
        name="read_file",
        description="读取文件内容",
        required_params=["file_path"],
        optional_params={
            "file_path": "文件路径（相对于工作区）"
        }
    ),
    ToolDefinition(
        name="list_files",
        description="列出目录中的文件",
        required_params=[],
        optional_params={
            "directory": "目录路径（可选，默认为工作区根目录）"
        }
    ),
    ToolDefinition(
        name="execute_code",
        description="执行Python代码",
        required_params=["code"],
        optional_params={
            "code": "要执行的Python代码"
        }
    ),
    ToolDefinition(
        name="final_answer",
        description="提供最终答案并结束任务",
        required_params=["answer"],
        optional_params={
            "answer": "最终答案内容"
        }
    ),
    ToolDefinition(
        name="create_echarts_visualization",
        description="根据输入数据和图表类型快速创建ECharts可视化HTML文件",
        required_params=["data", "chart_type", "output_filename"],
        optional_params={
            "data": "图表数据，支持多种格式：列表、字典、JSON字符串等",
            "chart_type": "图表类型：bar(柱状图)、line(折线图)、pie(饼图)、scatter(散点图)、radar(雷达图)、funnel(漏斗图)等",
            "output_filename": "输出HTML文件名（相对于工作区）",
            "title": "图表标题（可选）",
            "x_axis_name": "X轴名称（可选）",
            "y_axis_name": "Y轴名称（可选）",
            "theme": "图表主题：light、dark、vintage、roma、shine、infographic等（可选，默认light）"
        }
    )
]

# 生成向后兼容的TOOLS字典
TOOLS = {tool_def.name: tool_def.to_dict() for tool_def in _TOOL_DEFINITIONS}

def get_workspace_path(file_path: str) -> str:
    """获取工作空间内的文件路径"""
    return os.path.join(Config.WORKSPACE_PATH, file_path)

def write_file(file_path: str, content: str) -> str:
    """写入文件"""
    try:
        abs_path = get_workspace_path(file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"成功写入文件: {file_path}"
    except Exception as e:
        return f"写入文件失败: {str(e)}"

def read_file(file_path: str) -> str:
    """读取文件"""
    try:
        abs_path = get_workspace_path(file_path)
        
        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {str(e)}"

def list_files(directory: str = "") -> str:
    """列出文件"""
    try:
        abs_path = get_workspace_path(directory)
        files = os.listdir(abs_path)
        return json.dumps(files, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"列出文件失败: {str(e)}"

def execute_code(code: str) -> str:
    """执行Python代码"""
    import sys
    from io import StringIO
    
    # 重定向输出
    old_stdout = sys.stdout
    captured_output = StringIO()
    
    try:
        sys.stdout = captured_output
        
        # 创建执行环境，包含工作区相关的辅助函数
        exec_globals = {
            '__builtins__': __builtins__,
            'WORKSPACE_PATH': Config.WORKSPACE_PATH,
            'get_workspace_file_path': lambda filename: os.path.join(Config.WORKSPACE_PATH, filename),
            'os': os,
            'json': json
        }
        
        # 执行代码
        exec(code, exec_globals)
        
        # 获取输出结果
        output = captured_output.getvalue()
        return output if output else "代码执行成功，无输出"
        
    except Exception as e:
        return f"代码执行错误: {str(e)}"
    finally:
        # 确保输出被恢复
        sys.stdout = old_stdout

def create_echarts_visualization(data, chart_type: str, output_filename: str, title: str = "", x_axis_name: str = "", y_axis_name: str = "", theme: str = "light") -> str:
    """根据输入数据和图表类型快速创建ECharts可视化HTML文件"""
    try:
        # 确保文件名以.html结尾
        if not output_filename.endswith('.html'):
            output_filename += '.html'
        
        # 获取输出文件的绝对路径
        abs_path = get_workspace_path(output_filename)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        # 数据预处理
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return "数据格式错误：无法解析JSON字符串"
        
        # 数据格式化
        chart_type = chart_type.lower()
        processed_data = _process_chart_data(data, chart_type)
        
        # 生成图表配置
        chart_option = _generate_chart_config(chart_type, processed_data, title, x_axis_name, y_axis_name)
        
        # 生成HTML
        html_content = _generate_html_template(chart_option, title, chart_type, theme)
        
        # 写入文件
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        result = f"成功创建{chart_type}图表: {output_filename}"
        if title:
            result += f"\n标题: {title}"
        result += f"\n文件路径: {abs_path}"
        return result
        
    except Exception as e:
        return f"图表创建失败: {str(e)}"


def _process_chart_data(data, chart_type):
    """处理不同图表类型的数据格式"""
    if chart_type in ['bar', 'line']:
        return _process_bar_line_data(data)
    elif chart_type == 'pie':
        return _process_pie_data(data)
    elif chart_type == 'scatter':
        return _process_scatter_data(data)
    else:
        return _process_bar_line_data(data)  # 默认处理为柱状图


def _process_bar_line_data(data):
    """处理柱状图和折线图数据"""
    if isinstance(data, dict):
        return list(data.keys()), list(data.values())
    elif isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict) and 'name' in data[0] and 'value' in data[0]:
            return [item['name'] for item in data], [item['value'] for item in data]
        else:
            return [f'项目{i+1}' for i in range(len(data))], data
    else:
        return ['A', 'B', 'C', 'D', 'E'], [20, 30, 40, 50, 60]


def _process_pie_data(data):
    """处理饼图数据"""
    if isinstance(data, dict):
        return [{'name': k, 'value': v} for k, v in data.items()]
    elif isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict) and 'name' in data[0] and 'value' in data[0]:
            return data
        else:
            return [{'name': f'类别{i+1}', 'value': data[i]} for i in range(len(data))]
    else:
        return [{'name': 'A', 'value': 20}, {'name': 'B', 'value': 30}, {'name': 'C', 'value': 40}, {'name': 'D', 'value': 50}]


def _process_scatter_data(data):
    """处理散点图数据"""
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], list) and len(data[0]) >= 2:
            return data
        elif isinstance(data[0], dict) and 'x' in data[0] and 'y' in data[0]:
            return [[item['x'], item['y']] for item in data]
        else:
            return [[i, data[i]] for i in range(len(data))]
    else:
        return [[10, 20], [15, 25], [20, 30], [25, 35], [30, 40]]


def _generate_chart_config(chart_type, processed_data, title, x_axis_name, y_axis_name):
    """生成ECharts配置"""
    # 基础配置
    option = {
        'title': {
            'text': title or f'{chart_type.capitalize()}图表',
            'left': 'center'
        },
        'tooltip': {'trigger': 'item' if chart_type == 'pie' else 'axis'}
    }
    
    if chart_type == 'bar':
        x_data, y_data = processed_data
        option.update({
            'xAxis': {'type': 'category', 'data': x_data, 'name': x_axis_name},
            'yAxis': {'type': 'value', 'name': y_axis_name},
            'series': [{'name': y_axis_name or '数值', 'type': 'bar', 'data': y_data}]
        })
    elif chart_type == 'line':
        x_data, y_data = processed_data
        option.update({
            'xAxis': {'type': 'category', 'data': x_data, 'name': x_axis_name},
            'yAxis': {'type': 'value', 'name': y_axis_name},
            'series': [{'name': y_axis_name or '数值', 'type': 'line', 'data': y_data}]
        })
    elif chart_type == 'pie':
        option.update({
            'legend': {'top': '10%'},
            'series': [{
                'name': '数据',
                'type': 'pie',
                'radius': '50%',
                'data': processed_data,
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 10,
                        'shadowOffsetX': 0,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }]
        })
    elif chart_type == 'scatter':
        option.update({
            'xAxis': {'type': 'value', 'name': x_axis_name},
            'yAxis': {'type': 'value', 'name': y_axis_name},
            'series': [{'name': y_axis_name or '数值', 'type': 'scatter', 'data': processed_data}]
        })
    else:
        # 默认柱状图
        option.update({
            'xAxis': {'type': 'category', 'data': ['A', 'B', 'C', 'D', 'E']},
            'yAxis': {'type': 'value'},
            'series': [{'name': '数值', 'type': 'bar', 'data': [20, 30, 40, 50, 60]}]
        })
    
    return option


def _generate_html_template(chart_option, title, chart_type, theme):
    """生成HTML模板"""
    # 主题样式
    theme_styles = {
        'light': 'background-color: #fff; color: #333;',
        'dark': 'background-color: #2c3e50; color: #ecf0f1;',
        'vintage': 'background-color: #fef8e8; color: #8b4513;',
        'roma': 'background-color: #f5f5dc; color: #8b0000;',
        'shine': 'background-color: #f0f8ff; color: #4682b4;',
        'infographic': 'background-color: #f8f9fa; color: #495057;'
    }
    
    body_style = theme_styles.get(theme, theme_styles['light'])
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title or f'{chart_type.capitalize()}图表'}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            {body_style}
        }}
        #chart {{
            width: 100%;
            height: 600px;
        }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        var chartDom = document.getElementById('chart');
        var myChart = echarts.init(chartDom);
        var option = {json.dumps(chart_option, ensure_ascii=False, indent=2)};
        myChart.setOption(option);
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
    </script>
</body>
</html>"""




def get_tools_description() -> str:
    """获取工具的详细描述，用于prompt - 使用标准化格式确保稳定性"""
    try:
        # 使用标准化的工具定义生成描述
        descriptions = []
        for tool_def in _TOOL_DEFINITIONS:
            descriptions.append(tool_def.to_prompt_format())
        
        # 添加版本信息和一致性检查
        header = f"# 可用工具 (版本: {TOOLS_VERSION})\n"
        footer = "\n\n注意：所有文件操作都相对于工作区目录进行。"
        
        return header + "\n\n".join(descriptions) + footer
    
    except Exception as e:
        # 降级到基础格式，确保系统稳定性
        return get_tools_description_fallback()

def get_tools_description_fallback() -> str:
    """降级版本的工具描述生成，确保系统稳定性"""
    descriptions = []
    for tool_name, tool_info in TOOLS.items():
        desc = f"- **{tool_name}**: {tool_info['description']}"
        if tool_info.get('parameters'):
            params = []
            for param_name, param_desc in tool_info['parameters'].items():
                params.append(f"    - {param_name}: {param_desc}")
            if params:
                desc += "\n" + "\n".join(params)
        descriptions.append(desc)
    return "\n\n".join(descriptions)

def validate_tools_consistency() -> tuple[bool, str]:
    """验证工具定义的一致性"""
    try:
        # 检查工具名称唯一性
        tool_names = [tool_def.name for tool_def in _TOOL_DEFINITIONS]
        if len(tool_names) != len(set(tool_names)):
            return False, "工具名称存在重复"
        
        # 检查每个工具定义的完整性
        for tool_def in _TOOL_DEFINITIONS:
            if not tool_def.name or not tool_def.description:
                return False, f"工具 {tool_def.name} 缺少必要信息"
            
            # 检查必需参数是否在参数列表中
            for param in tool_def.required_params:
                if param not in tool_def.all_params:
                    return False, f"工具 {tool_def.name} 的必需参数 {param} 未在参数列表中定义"
        
        return True, "工具定义一致性检查通过"
    
    except Exception as e:
        return False, f"一致性检查失败: {str(e)}"

def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> tuple[bool, str]:
    """验证工具参数"""
    if tool_name not in TOOLS:
        return False, f"未知工具: {tool_name}"
    
    tool_info = TOOLS[tool_name]
    required_params = tool_info.get('required_parameters', [])
    
    # 检查必需参数
    for param_name in required_params:
        if param_name not in arguments:
            return False, f"缺少必需参数: {param_name}"
    
    return True, "参数验证通过"

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """执行工具 - 增强版本，包含参数验证和错误处理"""
    # 验证参数
    is_valid, message = validate_tool_arguments(tool_name, arguments)
    if not is_valid:
        return f"参数验证失败: {message}"
    
    try:
        if tool_name == "write_file":
            return write_file(arguments.get("file_path", ""), arguments.get("content", ""))
        elif tool_name == "read_file":
            return read_file(arguments.get("file_path", ""))
        elif tool_name == "list_files":
            return list_files(arguments.get("directory", ""))
        elif tool_name == "execute_code":
             return execute_code(arguments.get("code", ""))
        elif tool_name == "final_answer":
            return f"任务完成: {arguments.get('answer', '')}"
        elif tool_name == "create_echarts_visualization":
            return create_echarts_visualization(
                arguments.get("data", {}),
                arguments.get("chart_type", "bar"),
                arguments.get("output_filename", ""),
                arguments.get("title", ""),
                arguments.get("x_axis_name", ""),
                arguments.get("y_axis_name", ""),
                arguments.get("theme", "light")
            )
        else:
            return f"未知工具: {tool_name}"
    except Exception as e:
        return f"工具执行错误 [{tool_name}]: {str(e)}"