# Aime多智能体框架原型 - 工具函数
import json
import re
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
from config import config

# 配置日志
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class LLMClient:
    """简化的LLM客户端"""
    
    def __init__(self, model: str = None):
        self.model = model or config.DEFAULT_MODEL
        self._setup_client()
    
    def _setup_client(self):
        """设置LLM客户端"""
        try:
            if "gpt" in self.model.lower():
                import openai
                # 支持自定义base_url
                client_kwargs = {"api_key": config.OPENAI_API_KEY}
                if config.OPENAI_API_BASE:
                    client_kwargs["base_url"] = config.OPENAI_API_BASE
                self.client = openai.OpenAI(**client_kwargs)
                self.client_type = "openai"
            elif "claude" in self.model.lower():
                import anthropic
                self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                self.client_type = "anthropic"
            else:
                raise ValueError(f"不支持的模型: {self.model}")
        except ImportError as e:
            logger.error(f"导入错误: {e}")
            raise
        except Exception as e:
            logger.error(f"客户端设置失败: {e}")
            raise
    
    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """生成文本"""
        for attempt in range(config.MAX_RETRIES):
            try:
                if self.client_type == "openai":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        temperature=0.1
                    )
                    return response.choices[0].message.content
                
                elif self.client_type == "anthropic":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
                    
            except Exception as e:
                logger.warning(f"LLM调用失败 (尝试 {attempt+1}/{config.MAX_RETRIES}): {e}")
                if attempt == config.MAX_RETRIES - 1:
                    return f"LLM调用失败: {str(e)}"
                time.sleep(2 ** attempt)  # 指数退避

def safe_json_parse(text: str) -> Dict[str, Any]:
    """安全的JSON解析"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取JSON片段
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # 降级处理
        return {
            "error": "JSON解析失败",
            "raw_text": text,
            "timestamp": datetime.now().isoformat()
        }

def parse_response(response: str) -> tuple[str, str]:
    """解析ReAct格式的响应"""
    lines = response.split('\n')
    thought = ""
    action = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith("思考:") or line.startswith("Thought:"):
            thought = line.split(":", 1)[1].strip()
        elif line.startswith("行动:") or line.startswith("Action:"):
            action = line.split(":", 1)[1].strip()
    
    return thought, action

def generate_task_id() -> str:
    """生成任务ID"""
    timestamp = int(time.time() * 1000)
    return f"task_{timestamp}"

def generate_agent_id(agent_type: str, task_hash: int) -> str:
    """生成智能体ID"""
    return f"{agent_type}_{abs(task_hash) % 1000}"

def format_execution_history(history: list) -> str:
    """格式化执行历史"""
    if not history:
        return "无执行历史"
    
    formatted = []
    for i, step in enumerate(history[-3:], 1):  # 只显示最近3步
        if isinstance(step, dict):
            thought = step.get("thought", "")
            action = step.get("action", "")
            result = step.get("result", "")
            formatted.append(f"步骤{i}: 思考={thought[:50]}... 行动={action[:50]}... 结果={result[:50]}...")
        else:
            formatted.append(f"步骤{i}: {str(step)[:100]}...")
    
    return "\n".join(formatted)

def load_json_file(filepath: str) -> Dict[str, Any]:
    """加载JSON文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info(f"文件不存在: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON文件格式错误 {filepath}: {e}")
        return {}

def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """保存JSON文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"保存文件失败 {filepath}: {e}")
        return False

class Timer:
    """简单的计时器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        self.start_time = time.time()
        return self
    
    def stop(self):
        self.end_time = time.time()
        return self
    
    def elapsed(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

if __name__ == "__main__":
    # 测试工具函数
    print("🧪 测试工具函数...")
    
    # 测试JSON解析
    test_json = '{"test": "value"}'
    result = safe_json_parse(test_json)
    print(f"JSON解析测试: {result}")
    
    # 测试响应解析
    test_response = "思考: 我需要分析这个问题\n行动: 使用搜索工具"
    thought, action = parse_response(test_response)
    print(f"响应解析测试: 思考={thought}, 行动={action}")
    
    # 测试计时器
    with Timer() as timer:
        time.sleep(0.1)
    print(f"计时器测试: {timer.elapsed():.2f}秒")
    
    print("✅ 工具函数测试完成")