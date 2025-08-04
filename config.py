# Aime多智能体框架原型 - 配置文件
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """系统配置类"""
    
    # API配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")  # 自定义API基础URL
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4")
    
    # 系统参数
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "15"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))
    
    # 文件路径
    STATE_FILE = os.getenv("STATE_FILE", "aime_state.json")
    LOG_FILE = os.getenv("LOG_FILE", "aime.log")
    
    # 调试模式
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    VERBOSE = os.getenv("VERBOSE", "False").lower() == "true"
    
    @classmethod
    def validate(cls):
        """验证配置是否正确"""
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            raise ValueError("至少需要设置OPENAI_API_KEY或ANTHROPIC_API_KEY")
        
        if cls.MAX_ITERATIONS <= 0:
            raise ValueError("MAX_ITERATIONS必须大于0")
        
        return True

# 全局配置实例
config = Config()

if __name__ == "__main__":
    try:
        config.validate()
        print("✅ 配置验证通过")
    except ValueError as e:
        print(f"❌ 配置错误: {e}")