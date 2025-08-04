# Aime多智能体框架原型 - 动态规划器
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils import LLMClient, safe_json_parse, logger, Timer
from config import config

class SimpleDynamicPlanner:
    """简化的动态规划器
    
    负责：
    1. 任务分解为子任务
    2. 基于反馈的动态重规划
    3. 规划历史管理
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.planning_history = []
        self.planning_templates = {
            "basic": self._get_basic_planning_template(),
            "with_feedback": self._get_feedback_planning_template(),
            "replan": self._get_replanning_template()
        }
    
    def plan(self, goal: str, current_state: Optional[str] = None, feedback: Optional[str] = None) -> Dict[str, Any]:
        """生成任务规划
        
        Args:
            goal: 目标描述
            current_state: 当前状态
            feedback: 执行反馈
            
        Returns:
            规划结果
        """
        logger.info(f"开始规划任务: {goal[:100]}...")
        
        with Timer() as timer:
            # 选择合适的模板
            template_key = self._select_template(current_state, feedback)
            template = self.planning_templates[template_key]
            
            # 构建提示词
            prompt = self._build_prompt(template, goal, current_state, feedback)
            
            # 调用LLM生成规划
            response = self.llm.generate(prompt, max_tokens=1500)
            
            # 解析规划结果
            plan = self._parse_plan(response)
            
            # 记录规划历史
            self._save_planning_history(goal, plan, current_state, feedback, timer.elapsed())
        
        logger.info(f"规划完成，耗时: {timer.elapsed():.2f}秒")
        return plan
    
    def get_planning_history(self) -> List[Dict[str, Any]]:
        """获取规划历史"""
        return self.planning_history.copy()
    
    def clear_history(self):
        """清空规划历史"""
        self.planning_history.clear()
        logger.info("规划历史已清空")
    
    def _select_template(self, current_state: Optional[str], feedback: Optional[str]) -> str:
        """选择合适的规划模板"""
        if feedback:
            return "replan"
        elif current_state:
            return "with_feedback"
        else:
            return "basic"
    
    def _build_prompt(self, template: str, goal: str, current_state: Optional[str], feedback: Optional[str]) -> str:
        """构建规划提示词"""
        return template.format(
            goal=goal,
            current_state=current_state or "初始状态",
            feedback=feedback or "无",
            history=self._format_recent_history()
        )
    
    def _parse_plan(self, response: str) -> Dict[str, Any]:
        """解析规划结果"""
        # 尝试解析JSON
        parsed = safe_json_parse(response)
        
        if "error" in parsed:
            # JSON解析失败，尝试文本解析
            return self._fallback_parse(response)
        
        # 验证和补充规划结构
        return self._validate_and_enhance_plan(parsed)
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """降级文本解析"""
        logger.warning("JSON解析失败，使用文本解析")
        
        # 简单的文本分割
        lines = response.split('\n')
        tasks = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and len(line) > 10:
                # 尝试提取任务信息
                task = {
                    "id": f"task_{len(tasks) + 1}",
                    "description": line[:200],  # 限制长度
                    "tool_type": self._guess_tool_type(line),
                    "priority": "normal"
                }
                tasks.append(task)
        
        return {
            "tasks": tasks if tasks else [{"id": "task_1", "description": response[:200], "tool_type": "general", "priority": "normal"}],
            "strategy": "sequential",
            "estimated_time": len(tasks) * 30 if tasks else 30
        }
    
    def _guess_tool_type(self, description: str) -> str:
        """根据描述猜测工具类型"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["搜索", "查找", "检索", "search"]):
            return "search"
        elif any(word in desc_lower for word in ["计算", "数学", "统计", "calc"]):
            return "calculator"
        elif any(word in desc_lower for word in ["分析", "处理", "analysis"]):
            return "data_analysis"
        elif any(word in desc_lower for word in ["文件", "保存", "file"]):
            return "file_ops"
        else:
            return "general"
    
    def _validate_and_enhance_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """验证和增强规划结构"""
        # 确保必要字段存在
        if "tasks" not in plan:
            plan["tasks"] = []
        
        if "strategy" not in plan:
            plan["strategy"] = "sequential"
        
        if "estimated_time" not in plan:
            plan["estimated_time"] = len(plan["tasks"]) * 30
        
        # 验证和补充任务信息
        for i, task in enumerate(plan["tasks"]):
            if "id" not in task:
                task["id"] = f"task_{i + 1}"
            
            if "description" not in task:
                task["description"] = f"子任务 {i + 1}"
            
            if "tool_type" not in task:
                task["tool_type"] = self._guess_tool_type(task["description"])
            
            if "priority" not in task:
                task["priority"] = "normal"
        
        return plan
    
    def _format_recent_history(self) -> str:
        """格式化最近的规划历史"""
        if not self.planning_history:
            return "无历史规划"
        
        recent = self.planning_history[-2:]  # 最近2次规划
        formatted = []
        
        for entry in recent:
            formatted.append(f"目标: {entry['goal'][:50]}...")
            formatted.append(f"任务数: {len(entry['plan'].get('tasks', []))}")
            formatted.append(f"状态: {entry.get('current_state', '未知')}")
            formatted.append("---")
        
        return "\n".join(formatted)
    
    def _save_planning_history(self, goal: str, plan: Dict[str, Any], current_state: Optional[str], 
                              feedback: Optional[str], elapsed_time: float):
        """保存规划历史"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "goal": goal,
            "plan": plan,
            "current_state": current_state,
            "feedback": feedback,
            "elapsed_time": elapsed_time,
            "task_count": len(plan.get("tasks", []))
        }
        
        self.planning_history.append(entry)
        
        # 限制历史记录数量
        if len(self.planning_history) > 10:
            self.planning_history = self.planning_history[-10:]
    
    def _get_basic_planning_template(self) -> str:
        """基础规划模板"""
        return """你是一个专业的任务规划专家。请将以下目标分解为3-5个可执行的子任务。

目标: {goal}

请按照以下JSON格式输出规划结果：

{{
  "tasks": [
    {{
      "id": "task_1",
      "description": "具体的任务描述",
      "tool_type": "search|calculator|data_analysis|file_ops|general",
      "priority": "high|normal|low"
    }}
  ],
  "strategy": "sequential|parallel|mixed",
  "estimated_time": "预估总耗时(秒)"
}}

要求：
1. 任务描述要具体明确
2. 合理选择工具类型
3. 按重要性设置优先级
4. 考虑任务之间的依赖关系"""
    
    def _get_feedback_planning_template(self) -> str:
        """带反馈的规划模板"""
        return """你是一个专业的任务规划专家。基于当前状态调整任务规划。

目标: {goal}
当前状态: {current_state}
历史规划: {history}

请按照以下JSON格式输出调整后的规划：

{{
  "tasks": [
    {{
      "id": "task_1",
      "description": "具体的任务描述",
      "tool_type": "search|calculator|data_analysis|file_ops|general",
      "priority": "high|normal|low"
    }}
  ],
  "strategy": "sequential|parallel|mixed",
  "estimated_time": "预估总耗时(秒)",
  "adjustments": "相比历史规划的调整说明"
}}

要求：
1. 基于当前状态调整任务
2. 考虑已完成的工作
3. 优化任务顺序和优先级"""
    
    def _get_replanning_template(self) -> str:
        """重新规划模板"""
        return """你是一个专业的任务规划专家。基于执行反馈重新制定规划。

目标: {goal}
当前状态: {current_state}
执行反馈: {feedback}
历史规划: {history}

分析反馈信息，重新制定规划。输出JSON格式：

{{
  "tasks": [
    {{
      "id": "task_1",
      "description": "具体的任务描述",
      "tool_type": "search|calculator|data_analysis|file_ops|general",
      "priority": "high|normal|low"
    }}
  ],
  "strategy": "sequential|parallel|mixed",
  "estimated_time": "预估总耗时(秒)",
  "reason": "重新规划的原因",
  "changes": "主要变化说明"
}}

要求：
1. 分析反馈中的问题
2. 调整策略和方法
3. 确保目标可达成"""

if __name__ == "__main__":
    # 测试动态规划器
    print("🧪 测试动态规划器...")
    
    try:
        # 创建LLM客户端（需要API密钥）
        llm = LLMClient()
        planner = SimpleDynamicPlanner(llm)
        
        # 测试基础规划
        goal = "分析公司Q1销售数据并生成报告"
        plan = planner.plan(goal)
        
        print("📋 规划结果:")
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        
        # 测试重新规划
        feedback = "数据文件格式有问题，需要先清理数据"
        new_plan = planner.plan(goal, current_state="已获取原始数据", feedback=feedback)
        
        print("\n📋 重新规划结果:")
        print(json.dumps(new_plan, ensure_ascii=False, indent=2))
        
        print("\n✅ 动态规划器测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("💡 提示: 请确保设置了正确的API密钥")