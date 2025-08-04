# Aime多智能体框架原型 - 进度管理模块
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils import logger, save_json_file, load_json_file, generate_task_id
from config import config

class SimpleProgressManager:
    """简化的进度管理模块
    
    负责：
    1. 任务生命周期管理
    2. 智能体状态跟踪
    3. 系统状态监控
    4. 执行历史记录
    """
    
    def __init__(self, state_file: str = None):
        self.state_file = state_file or config.STATE_FILE
        self.tasks = {}  # 任务状态字典
        self.agents = {}  # 智能体状态字典
        self.system_stats = {
            "created_time": datetime.now().isoformat(),
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_agents": 0
        }
        
        # 尝试加载已有状态
        self._load_state()
        
        logger.info("进度管理模块初始化完成")
    
    def create_task(self, description: str, task_type: str = "general", 
                   subtasks: List[str] = None, priority: str = "normal") -> str:
        """创建新任务
        
        Args:
            description: 任务描述
            task_type: 任务类型
            subtasks: 子任务列表
            priority: 优先级 (high, normal, low)
            
        Returns:
            任务ID
        """
        task_id = generate_task_id()
        
        task = {
            "id": task_id,
            "description": description,
            "type": task_type,
            "status": "pending",  # pending, running, completed, failed, cancelled
            "priority": priority,
            "subtasks": subtasks or [],
            "assigned_agent": None,
            "progress": 0.0,
            "start_time": None,
            "end_time": None,
            "result": None,
            "error_message": None,
            "created_time": datetime.now().isoformat(),
            "updated_time": datetime.now().isoformat()
        }
        
        self.tasks[task_id] = task
        self.system_stats["total_tasks"] += 1
        self._save_state()
        
        logger.info(f"创建任务: {task_id} - {description[:100]}...")
        return task_id
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """分配任务给智能体"""
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        if task["status"] != "pending":
            logger.warning(f"任务状态不允许分配: {task['status']}")
            return False
        
        task["assigned_agent"] = agent_id
        task["status"] = "running"
        task["start_time"] = datetime.now().isoformat()
        task["updated_time"] = datetime.now().isoformat()
        
        # 更新智能体状态
        if agent_id not in self.agents:
            self.agents[agent_id] = {
                "agent_id": agent_id,
                "status": "active",
                "current_task": task_id,
                "assigned_tasks": [],
                "completed_tasks": [],
                "failed_tasks": [],
                "created_time": datetime.now().isoformat()
            }
            self.system_stats["active_agents"] += 1
        
        agent = self.agents[agent_id]
        agent["current_task"] = task_id
        agent["status"] = "working"
        agent["assigned_tasks"].append(task_id)
        agent["updated_time"] = datetime.now().isoformat()
        
        self._save_state()
        
        logger.info(f"任务 {task_id} 已分配给智能体 {agent_id}")
        return True
    
    def update_progress(self, task_id: str, progress: float = None, 
                       status: str = None, result: str = None, 
                       error_message: str = None) -> bool:
        """更新任务进度"""
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        updated = False
        
        if progress is not None:
            task["progress"] = max(0.0, min(100.0, progress))
            updated = True
        
        if status is not None:
            old_status = task["status"]
            task["status"] = status
            updated = True
            
            # 处理状态变化
            if status in ["completed", "failed", "cancelled"] and task["end_time"] is None:
                task["end_time"] = datetime.now().isoformat()
                
                # 更新系统统计
                if status == "completed":
                    self.system_stats["completed_tasks"] += 1
                elif status == "failed":
                    self.system_stats["failed_tasks"] += 1
                
                # 更新智能体状态
                agent_id = task.get("assigned_agent")
                if agent_id and agent_id in self.agents:
                    agent = self.agents[agent_id]
                    agent["current_task"] = None
                    agent["status"] = "idle"
                    
                    if status == "completed":
                        agent["completed_tasks"].append(task_id)
                    elif status == "failed":
                        agent["failed_tasks"].append(task_id)
        
        if result is not None:
            task["result"] = result
            updated = True
        
        if error_message is not None:
            task["error_message"] = error_message
            updated = True
        
        if updated:
            task["updated_time"] = datetime.now().isoformat()
            self._save_state()
            
            logger.debug(f"任务 {task_id} 进度更新: {task['status']} ({task['progress']:.1f}%)")
        
        return updated
    
    def complete_task(self, task_id: str, result: str) -> bool:
        """完成任务"""
        return self.update_progress(task_id, progress=100.0, status="completed", result=result)
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """标记任务失败"""
        return self.update_progress(task_id, status="failed", error_message=error_message)
    
    def cancel_task(self, task_id: str, reason: str = None) -> bool:
        """取消任务"""
        error_msg = f"任务已取消: {reason}" if reason else "任务已取消"
        return self.update_progress(task_id, status="cancelled", error_message=error_msg)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id in self.tasks:
            return self.tasks[task_id].copy()
        return {}
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体状态"""
        if agent_id in self.agents:
            return self.agents[agent_id].copy()
        return {}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统整体状态"""
        # 实时统计
        total_tasks = len(self.tasks)
        pending_tasks = len([t for t in self.tasks.values() if t["status"] == "pending"])
        running_tasks = len([t for t in self.tasks.values() if t["status"] == "running"])
        completed_tasks = len([t for t in self.tasks.values() if t["status"] == "completed"])
        failed_tasks = len([t for t in self.tasks.values() if t["status"] == "failed"])
        
        active_agents = len([a for a in self.agents.values() if a["status"] in ["working", "idle"]])
        
        return {
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "running_tasks": running_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0.0,
            "failure_rate": failed_tasks / total_tasks if total_tasks > 0 else 0.0,
            "active_agents": active_agents,
            "created_time": self.system_stats["created_time"],
            "last_updated": datetime.now().isoformat()
        }
    
    def list_tasks(self, status: str = None, agent_id: str = None) -> List[Dict[str, Any]]:
        """列出任务"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        
        if agent_id:
            tasks = [t for t in tasks if t["assigned_agent"] == agent_id]
        
        # 按创建时间排序
        tasks.sort(key=lambda x: x["created_time"], reverse=True)
        
        return tasks
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        agents = list(self.agents.values())
        agents.sort(key=lambda x: x["created_time"], reverse=True)
        return agents
    
    def get_task_tree(self, task_id: str) -> Dict[str, Any]:
        """获取任务树结构（简化版）"""
        if task_id not in self.tasks:
            return {}
        
        task = self.tasks[task_id].copy()
        
        # 添加子任务信息（如果有）
        if task.get("subtasks"):
            subtask_info = []
            for subtask_desc in task["subtasks"]:
                # 查找相关的子任务
                related_tasks = [
                    t for t in self.tasks.values() 
                    if subtask_desc in t["description"]
                ]
                if related_tasks:
                    subtask_info.extend(related_tasks)
            
            task["subtask_details"] = subtask_info
        
        return task
    
    def generate_report(self) -> str:
        """生成系统报告"""
        status = self.get_system_status()
        
        report = f"""
🤖 Aime多智能体系统状态报告
==========================================

📊 总体统计:
- 总任务数: {status['total_tasks']}
- 待执行: {status['pending_tasks']}
- 执行中: {status['running_tasks']}
- 已完成: {status['completed_tasks']}
- 失败: {status['failed_tasks']}
- 完成率: {status['completion_rate']:.1%}
- 失败率: {status['failure_rate']:.1%}

🤖 智能体状态:
- 活跃智能体: {status['active_agents']}

🕒 时间信息:
- 系统创建时间: {status['created_time']}
- 最后更新时间: {status['last_updated']}

📋 最近任务:
"""
        
        # 添加最近任务信息
        recent_tasks = self.list_tasks()[:5]  # 最近5个任务
        for task in recent_tasks:
            status_emoji = {
                "pending": "⏳",
                "running": "🔄", 
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫"
            }.get(task["status"], "❓")
            
            report += f"  {status_emoji} {task['description'][:60]}... ({task['status']})\n"
        
        return report
    
    def clear_completed_tasks(self) -> int:
        """清理已完成的任务"""
        completed_tasks = [tid for tid, task in self.tasks.items() if task["status"] == "completed"]
        
        for task_id in completed_tasks:
            del self.tasks[task_id]
        
        self._save_state()
        
        logger.info(f"清理了 {len(completed_tasks)} 个已完成任务")
        return len(completed_tasks)
    
    def _save_state(self):
        """保存状态到文件"""
        state_data = {
            "tasks": self.tasks,
            "agents": self.agents,
            "system_stats": self.system_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        if not save_json_file(state_data, self.state_file):
            logger.warning("状态保存失败")
    
    def _load_state(self):
        """从文件加载状态"""
        state_data = load_json_file(self.state_file)
        
        if state_data:
            self.tasks = state_data.get("tasks", {})
            self.agents = state_data.get("agents", {})
            self.system_stats.update(state_data.get("system_stats", {}))
            
            logger.info(f"已加载状态: {len(self.tasks)}个任务, {len(self.agents)}个智能体")
        else:
            logger.info("未找到历史状态，使用默认状态")
    
    def backup_state(self, backup_file: str = None) -> bool:
        """备份状态"""
        if backup_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"aime_backup_{timestamp}.json"
        
        state_data = {
            "tasks": self.tasks,
            "agents": self.agents,
            "system_stats": self.system_stats,
            "backup_time": datetime.now().isoformat()
        }
        
        if save_json_file(state_data, backup_file):
            logger.info(f"状态已备份到: {backup_file}")
            return True
        else:
            logger.error(f"备份失败: {backup_file}")
            return False

if __name__ == "__main__":
    # 测试进度管理模块
    print("🧪 测试进度管理模块...")
    
    try:
        # 创建进度管理器
        pm = SimpleProgressManager()
        
        # 创建测试任务
        task1_id = pm.create_task("分析销售数据", "analysis", priority="high")
        task2_id = pm.create_task("生成报告", "report", priority="normal")
        
        print(f"创建任务: {task1_id}, {task2_id}")
        
        # 分配任务
        pm.assign_task(task1_id, "analyst_001")
        pm.assign_task(task2_id, "executor_001")
        
        # 更新进度
        pm.update_progress(task1_id, progress=50.0)
        pm.update_progress(task2_id, progress=100.0, status="completed", result="报告已生成")
        
        # 生成报告
        report = pm.generate_report()
        print(f"\n系统报告:\n{report}")
        
        # 显示系统状态
        status = pm.get_system_status()
        print(f"系统状态: 完成率 {status['completion_rate']:.1%}")
        
        print("\n✅ 进度管理模块测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()