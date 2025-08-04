# Aime多智能体框架原型 - Actor工厂
from typing import Dict, List, Any
from utils import LLMClient, generate_agent_id, logger
from config import config

class SimpleActorFactory:
    """简化的Actor工厂
    
    负责：
    1. 根据任务选择合适的智能体类型
    2. 配置智能体的人格和工具
    3. 创建智能体实例
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.agent_templates = self._init_agent_templates()
        self.created_agents = {}  # 缓存已创建的智能体
    
    def create_actor(self, task_description: str, task_type: str = None) -> 'SimpleActor':
        """创建智能体
        
        Args:
            task_description: 任务描述
            task_type: 任务类型（可选）
            
        Returns:
            SimpleActor实例
        """
        logger.info(f"创建智能体用于任务: {task_description[:100]}...")
        
        # 选择智能体类型
        agent_type = self._select_agent_type(task_description, task_type)
        
        # 获取模板
        template = self.agent_templates[agent_type]
        
        # 生成智能体ID
        agent_id = generate_agent_id(agent_type, hash(task_description))
        
        # 检查是否已创建相同的智能体
        if agent_id in self.created_agents:
            logger.info(f"复用已创建的智能体: {agent_id}")
            return self.created_agents[agent_id]
        
        # 导入SimpleActor类（避免循环导入）
        from actor import SimpleActor
        
        # 创建智能体实例
        actor = SimpleActor(
            agent_id=agent_id,
            agent_type=agent_type,
            persona=template["persona"],
            tools=template["tools"].copy(),
            llm_client=self.llm,
            capabilities=template["capabilities"].copy()
        )
        
        # 缓存智能体
        self.created_agents[agent_id] = actor
        
        logger.info(f"成功创建智能体: {agent_id} (类型: {agent_type})")
        return actor
    
    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体信息"""
        if agent_id in self.created_agents:
            agent = self.created_agents[agent_id]
            return {
                "agent_id": agent.agent_id,
                "agent_type": agent.agent_type,
                "status": agent.status,
                "created_time": agent.created_time,
                "total_tasks": len(agent.execution_history)
            }
        return {}
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有已创建的智能体"""
        return [self.get_agent_info(agent_id) for agent_id in self.created_agents.keys()]
    
    def remove_agent(self, agent_id: str) -> bool:
        """移除智能体"""
        if agent_id in self.created_agents:
            del self.created_agents[agent_id]
            logger.info(f"智能体 {agent_id} 已移除")
            return True
        return False
    
    def clear_agents(self):
        """清空所有智能体"""
        self.created_agents.clear()
        logger.info("所有智能体已清空")
    
    def _select_agent_type(self, task_description: str, task_type: str = None) -> str:
        """选择智能体类型"""
        if task_type and task_type in self.agent_templates:
            return task_type
        
        # 基于关键词匹配选择类型
        desc_lower = task_description.lower()
        
        # 分析师关键词
        analyst_keywords = [
            "分析", "计算", "推理", "统计", "评估", "比较", "研究",
            "analysis", "calculate", "reasoning", "statistics", "evaluate"
        ]
        
        # 执行者关键词
        executor_keywords = [
            "执行", "操作", "运行", "处理", "生成", "创建", "构建", "实施",
            "execute", "operate", "run", "process", "generate", "create", "build"
        ]
        
        # 研究员关键词
        researcher_keywords = [
            "搜索", "查找", "收集", "整理", "总结", "调研", "探索",
            "search", "find", "collect", "organize", "summarize", "research"
        ]
        
        # 优先级判断
        analyst_score = sum(1 for kw in analyst_keywords if kw in desc_lower)
        executor_score = sum(1 for kw in executor_keywords if kw in desc_lower)
        researcher_score = sum(1 for kw in researcher_keywords if kw in desc_lower)
        
        # 选择得分最高的类型
        if analyst_score >= executor_score and analyst_score >= researcher_score:
            return "analyst"
        elif executor_score >= researcher_score:
            return "executor"
        else:
            return "researcher"  # 默认类型
    
    def _init_agent_templates(self) -> Dict[str, Dict[str, Any]]:
        """初始化智能体模板"""
        return {
            "analyst": {
                "persona": """你是一个专业的数据分析专家，擅长：
- 数据分析和统计推理
- 问题分解和逻辑思考  
- 量化评估和比较分析
- 趋势识别和模式发现

你的特点：
- 思维严谨，注重数据驱动
- 善于发现数据中的规律和异常
- 能够提供客观的分析结论
- 会使用适当的分析工具和方法""",
                
                "tools": [
                    "calculator",      # 计算器
                    "data_analysis",   # 数据分析工具
                    "statistics",      # 统计工具
                    "visualization",   # 可视化工具
                    "comparison"       # 比较分析工具
                ],
                
                "capabilities": [
                    "数值计算和统计分析",
                    "数据可视化和图表生成",
                    "趋势分析和预测",
                    "异常检测和模式识别",
                    "量化评估和风险分析"
                ]
            },
            
            "executor": {
                "persona": """你是一个高效的执行专家，擅长：
- 任务执行和操作实施
- 文件处理和系统操作
- 流程化工作和批量处理
- 结果生成和输出整理

你的特点：
- 执行力强，注重结果导向
- 善于将抽象需求转化为具体操作
- 能够高效完成重复性工作
- 注重输出质量和格式规范""",
                
                "tools": [
                    "file_ops",        # 文件操作
                    "api_calls",       # API调用
                    "text_processing", # 文本处理
                    "format_converter", # 格式转换
                    "batch_processor"  # 批量处理
                ],
                
                "capabilities": [
                    "文件读写和格式转换",
                    "批量数据处理",
                    "API接口调用",
                    "文档生成和格式化",
                    "自动化流程执行"
                ]
            },
            
            "researcher": {
                "persona": """你是一个专业的研究专家，擅长：
- 信息搜索和资料收集
- 知识整理和内容总结
- 多源信息综合分析
- 报告撰写和知识管理

你的特点：
- 知识面广，信息敏感度高
- 善于快速获取和筛选信息
- 能够从多个角度分析问题
- 注重信息的准确性和完整性""",
                
                "tools": [
                    "search",          # 搜索工具
                    "web_scraping",    # 网页抓取
                    "summarizer",      # 内容总结
                    "knowledge_base",  # 知识库
                    "citation_manager" # 引用管理
                ],
                
                "capabilities": [
                    "信息搜索和资料收集",
                    "内容总结和知识提取",
                    "多源信息整合",
                    "报告撰写和文档编制",
                    "知识库构建和管理"
                ]
            }
        }
    
    def get_available_types(self) -> List[str]:
        """获取可用的智能体类型"""
        return list(self.agent_templates.keys())
    
    def get_type_info(self, agent_type: str) -> Dict[str, Any]:
        """获取智能体类型信息"""
        if agent_type in self.agent_templates:
            template = self.agent_templates[agent_type]
            return {
                "type": agent_type,
                "description": template["persona"].split('\n')[0],
                "tools": template["tools"],
                "capabilities": template["capabilities"]
            }
        return {}

if __name__ == "__main__":
    # 测试Actor工厂
    print("🧪 测试Actor工厂...")
    
    try:
        from utils import LLMClient
        
        # 创建LLM客户端
        llm = LLMClient()
        factory = SimpleActorFactory(llm)
        
        # 测试智能体类型选择
        test_tasks = [
            "分析销售数据的趋势变化",
            "执行数据清理和格式转换",
            "搜索人工智能的最新研究进展"
        ]
        
        for task in test_tasks:
            agent_type = factory._select_agent_type(task)
            print(f"任务: {task}")
            print(f"选择类型: {agent_type}")
            print("---")
        
        # 显示可用类型
        print("\n📋 可用智能体类型:")
        for agent_type in factory.get_available_types():
            info = factory.get_type_info(agent_type)
            print(f"- {agent_type}: {info['description']}")
        
        print("\n✅ Actor工厂测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("💡 提示: 某些功能需要完整的依赖环境")