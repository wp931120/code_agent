import os

class Config:
    """简化的配置类"""
    
    # API配置
    API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    API_KEY = "7671bfc8aa1c48168fa6c728debdec22.GKQ556m7QwWZgTjm"
    MODEL_NAME = "glm-4.5"
    
    # 基本配置
    MAX_ITERATIONS = 10
    
    # 工作空间配置
    WORKSPACE_PATH = os.path.join(os.path.dirname(__file__), "workspace")