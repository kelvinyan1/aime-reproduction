# Aime多智能体框架原型 - 动态Actor
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils import LLMClient, parse_response, format_execution_history, logger, Timer
from config import config

class SimpleActor:
    """简化的动态Actor
    
    基于ReAct范式的智能体执行引擎：
    1. Reasoning (推理): 分析当前情况
    2. Acting (行动): 选择和执行行动
    3. Observing (观察): 分析行动结果
    """
    
    def __init__(self, agent_id: str, agent_type: str, persona: str, 
                 tools: List[str], llm_client: LLMClient, capabilities: List[str] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.persona = persona
        self.available_tools = tools
        self.capabilities = capabilities or []
        self.llm = llm_client
        
        # 状态管理
        self.status = "idle"  # idle, working, completed, error
        self.current_task = None
        self.execution_history = []
        self.created_time = datetime.now().isoformat()
        
        # 简化的工具实现
        self.tool_implementations = self._init_tool_implementations()
        
        logger.info(f"智能体 {agent_id} ({agent_type}) 初始化完成")
    
    def execute(self, task_description: str, context: Dict[str, Any] = None) -> str:
        """执行任务
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            执行结果
        """
        logger.info(f"智能体 {self.agent_id} 开始执行任务: {task_description[:100]}...")
        
        self.status = "working"
        self.current_task = task_description
        context = context or {}
        
        with Timer() as timer:
            try:
                result = self._react_loop(task_description, context)
                self.status = "completed"
                
                # 记录成功执行
                self._log_execution_result(task_description, result, True, timer.elapsed())
                
                logger.info(f"任务执行完成，耗时: {timer.elapsed():.2f}秒")
                return result
                
            except Exception as e:
                self.status = "error"
                error_msg = f"任务执行失败: {str(e)}"
                
                # 记录失败执行
                self._log_execution_result(task_description, error_msg, False, timer.elapsed())
                
                logger.error(f"任务执行失败: {e}")
                return error_msg
            
            finally:
                self.current_task = None
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "current_task": self.current_task,
            "total_executions": len(self.execution_history),
            "available_tools": self.available_tools,
            "capabilities": self.capabilities,
            "created_time": self.created_time
        }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history.copy()
    
    def clear_history(self):
        """清空执行历史"""
        self.execution_history.clear()
        logger.info(f"智能体 {self.agent_id} 执行历史已清空")
    
    def _react_loop(self, task_description: str, context: Dict[str, Any]) -> str:
        """ReAct执行循环"""
        steps = []
        max_iterations = config.MAX_ITERATIONS
        
        for iteration in range(max_iterations):
            logger.debug(f"执行迭代 {iteration + 1}/{max_iterations}")
            
            # 构建当前状态的提示词
            prompt = self._build_react_prompt(task_description, context, steps, iteration)
            
            # 获取LLM响应
            response = self.llm.generate(prompt, max_tokens=800)
            
            # 检查是否任务完成
            if self._is_completion_response(response):
                final_result = self._extract_completion_result(response)
                steps.append({
                    "iteration": iteration + 1,
                    "type": "completion",
                    "response": response,
                    "result": final_result,
                    "timestamp": datetime.now().isoformat()
                })
                return final_result
            
            # 解析思考和行动
            thought, action = parse_response(response)
            
            # 执行行动
            action_result = self._execute_action(action)
            
            # 记录步骤
            step = {
                "iteration": iteration + 1,
                "thought": thought,
                "action": action,
                "result": action_result,
                "timestamp": datetime.now().isoformat()
            }
            steps.append(step)
            
            # 更新上下文
            context["last_action"] = action
            context["last_result"] = action_result
            
            # 检查是否应该继续
            if self._should_continue(action_result, iteration, max_iterations):
                continue
            else:
                # 生成总结
                return self._generate_summary(task_description, steps)
        
        # 超过最大迭代次数
        return self._generate_summary(task_description, steps, timeout=True)
    
    def _build_react_prompt(self, task_description: str, context: Dict[str, Any], 
                          steps: List[Dict[str, Any]], iteration: int) -> str:
        """构建ReAct提示词"""
        # 基础人格和任务
        prompt = f"""{self.persona}

当前任务: {task_description}

可用工具: {', '.join(self.available_tools)}

上下文信息: {self._format_context(context)}"""
        
        # 添加执行历史
        if steps:
            prompt += f"\n\n执行历史:\n{self._format_steps(steps)}"
        
        # 添加指令
        if iteration == 0:
            prompt += f"""

请按照以下格式思考和行动：

思考: [分析当前情况，确定下一步行动]
行动: [选择合适的工具或直接回答]

如果任务已完成，请以"完成:"开始你的回复，然后提供最终结果。

现在开始第{iteration + 1}步："""
        else:
            prompt += f"""

请继续执行任务，这是第{iteration + 1}步：
思考: [基于前面的结果，分析下一步需要做什么]
行动: [选择行动或提供最终答案]"""
        
        return prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文信息"""
        if not context:
            return "无额外上下文"
        
        formatted = []
        for key, value in context.items():
            if key.startswith("_"):  # 跳过内部变量
                continue
            value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            formatted.append(f"- {key}: {value_str}")
        
        return "\n".join(formatted) if formatted else "无额外上下文"
    
    def _format_steps(self, steps: List[Dict[str, Any]]) -> str:
        """格式化执行步骤"""
        formatted = []
        for step in steps[-3:]:  # 只显示最近3步
            thought = step.get("thought", "")[:100]
            action = step.get("action", "")[:100]
            result = step.get("result", "")[:100]
            formatted.append(f"步骤{step['iteration']}: 思考={thought} 行动={action} 结果={result}")
        
        return "\n".join(formatted)
    
    def _is_completion_response(self, response: str) -> bool:
        """检查是否为完成响应"""
        return response.strip().startswith("完成:") or response.strip().startswith("完成：")
    
    def _extract_completion_result(self, response: str) -> str:
        """提取完成结果"""
        if "完成:" in response:
            return response.split("完成:", 1)[1].strip()
        elif "完成：" in response:
            return response.split("完成：", 1)[1].strip()
        else:
            return response.strip()
    
    def _execute_action(self, action: str) -> str:
        """执行行动"""
        if not action:
            return "无效行动"
        
        # 解析工具调用
        tool_name, tool_input = self._parse_tool_call(action)
        
        if tool_name in self.tool_implementations:
            try:
                return self.tool_implementations[tool_name](tool_input)
            except Exception as e:
                return f"工具执行失败: {str(e)}"
        else:
            # 直接响应（非工具调用）
            return f"思考结果: {action}"
    
    def _parse_tool_call(self, action: str) -> tuple[str, str]:
        """解析工具调用"""
        action = action.strip()
        
        # 尝试解析 "工具名: 输入" 格式
        if ":" in action:
            parts = action.split(":", 1)
            tool_name = parts[0].strip().lower()
            tool_input = parts[1].strip()
            
            # 映射中文工具名
            tool_mapping = {
                "搜索": "search",
                "计算": "calculator", 
                "分析": "data_analysis",
                "文件": "file_ops",
                "总结": "summarizer"
            }
            
            if tool_name in tool_mapping:
                return tool_mapping[tool_name], tool_input
            elif tool_name in self.available_tools:
                return tool_name, tool_input
        
        # 基于关键词猜测工具
        action_lower = action.lower()
        if any(kw in action_lower for kw in ["搜索", "查找", "search"]):
            return "search", action
        elif any(kw in action_lower for kw in ["计算", "数学", "calc"]):
            return "calculator", action
        elif any(kw in action_lower for kw in ["分析", "analysis"]):
            return "data_analysis", action
        else:
            return "general", action
    
    def _should_continue(self, action_result: str, iteration: int, max_iterations: int) -> bool:
        """判断是否应该继续执行"""
        # 检查是否有明显的错误需要重试
        if "失败" in action_result or "错误" in action_result:
            return iteration < max_iterations - 2  # 保留最后两次机会
        
        # 检查是否有明确的完成信号
        if any(signal in action_result.lower() for signal in ["完成", "成功", "结束", "completed", "finished"]):
            return False
        
        # 继续执行
        return True
    
    def _generate_summary(self, task_description: str, steps: List[Dict[str, Any]], timeout: bool = False) -> str:
        """生成执行总结"""
        if not steps:
            return "无法完成任务，未执行任何步骤"
        
        if timeout:
            summary = f"任务执行超时（{len(steps)}步）: {task_description}\n\n"
        else:
            summary = f"任务执行完成（{len(steps)}步）: {task_description}\n\n"
        
        # 添加关键步骤
        summary += "执行过程:\n"
        for step in steps:
            if step.get("type") == "completion":
                summary += f"最终结果: {step.get('result', 'N/A')}\n"
            else:
                summary += f"- {step.get('thought', 'N/A')[:100]}\n"
        
        # 添加最终结果
        if steps:
            last_step = steps[-1]
            if last_step.get("type") == "completion":
                summary += f"\n最终输出: {last_step.get('result', 'N/A')}"
            else:
                summary += f"\n最新结果: {last_step.get('result', 'N/A')[:200]}"
        
        return summary
    
    def _log_execution_result(self, task: str, result: str, success: bool, elapsed_time: float):
        """记录执行结果"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task[:200],  # 限制长度
            "result": result[:500],  # 限制长度
            "success": success,
            "elapsed_time": elapsed_time,
            "agent_type": self.agent_type
        }
        
        self.execution_history.append(log_entry)
        
        # 限制历史记录数量
        if len(self.execution_history) > 20:
            self.execution_history = self.execution_history[-20:]
    
    def _init_tool_implementations(self) -> Dict[str, callable]:
        """初始化工具实现（简化版）"""
        return {
            "search": self._tool_search,
            "calculator": self._tool_calculator,
            "data_analysis": self._tool_data_analysis,
            "file_ops": self._tool_file_ops,
            "summarizer": self._tool_summarizer,
            "general": self._tool_general
        }
    
    # 简化的工具实现
    def _tool_search(self, query: str) -> str:
        """搜索工具（模拟）"""
        return f"搜索结果: 关于'{query}'的相关信息。[这是模拟结果，实际实现可集成真实搜索API]"
    
    def _tool_calculator(self, expression: str) -> str:
        """计算器工具"""
        try:
            # 简单的数学表达式计算（安全性有限，仅用于原型）
            # 实际实现应使用更安全的数学表达式解析器
            import re
            
            # 只允许数字、基本运算符和括号
            if re.match(r'^[0-9+\-*/().%\s]+$', expression):
                result = eval(expression)
                return f"计算结果: {expression} = {result}"
            else:
                return f"无效的数学表达式: {expression}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    def _tool_data_analysis(self, data_description: str) -> str:
        """数据分析工具（模拟）"""
        return f"数据分析结果: 对'{data_description}'进行了分析。[这是模拟结果，实际实现可集成数据分析库]"
    
    def _tool_file_ops(self, operation: str) -> str:
        """文件操作工具（模拟）"""
        return f"文件操作结果: 执行了'{operation}'操作。[这是模拟结果，实际实现可进行真实文件操作]"
    
    def _tool_summarizer(self, text: str) -> str:
        """文本总结工具（模拟）"""
        # 简单的文本截断作为总结
        if len(text) > 200:
            summary = text[:200] + "..."
        else:
            summary = text
        return f"总结结果: {summary}"
    
    def _tool_general(self, input_text: str) -> str:
        """通用工具"""
        return f"处理结果: 已处理输入'{input_text[:100]}...'"

if __name__ == "__main__":
    # 测试动态Actor
    print("🧪 测试动态Actor...")
    
    try:
        from utils import LLMClient
        
        # 创建LLM客户端
        llm = LLMClient()
        
        # 创建智能体
        actor = SimpleActor(
            agent_id="test_analyst_001",
            agent_type="analyst",
            persona="你是一个数据分析专家",
            tools=["calculator", "data_analysis"],
            llm_client=llm
        )
        
        # 测试执行任务
        task = "计算 125 + 875 的结果并分析这个数值"
        result = actor.execute(task)
        
        print(f"执行结果: {result}")
        
        # 显示状态
        status = actor.get_status()
        print(f"智能体状态: {status}")
        
        print("\n✅ 动态Actor测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("💡 提示: 需要正确的API配置")