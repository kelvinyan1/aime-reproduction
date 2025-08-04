# Aime多智能体框架原型 - 主程序入口
import sys
import time
from typing import Dict, Any, Optional
from utils import LLMClient, logger, Timer
from config import config
from planner import SimpleDynamicPlanner
from factory import SimpleActorFactory
from progress import SimpleProgressManager

class AimeSystem:
    """Aime多智能体系统主类
    
    整合动态规划器、Actor工厂、进度管理等核心组件，
    提供完整的多智能体任务执行能力。
    """
    
    def __init__(self, model: str = None, state_file: str = None):
        """初始化系统
        
        Args:
            model: LLM模型名称
            state_file: 状态文件路径
        """
        logger.info("🤖 Aime多智能体系统启动中...")
        
        try:
            # 验证配置
            config.validate()
            
            # 初始化核心组件
            self.llm_client = LLMClient(model)
            self.planner = SimpleDynamicPlanner(self.llm_client)
            self.factory = SimpleActorFactory(self.llm_client)
            self.progress_manager = SimpleProgressManager(state_file)
            
            # 系统状态
            self.system_info = {
                "version": "0.1.0",
                "model": self.llm_client.model,
                "initialized": True,
                "start_time": time.time()
            }
            
            logger.info("✅ Aime多智能体系统初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}")
            raise
    
    def execute_task(self, goal: str, context: Dict[str, Any] = None) -> str:
        """执行单个任务
        
        Args:
            goal: 任务目标描述
            context: 上下文信息
            
        Returns:
            执行结果
        """
        logger.info(f"📋 开始执行任务: {goal[:100]}...")
        
        with Timer() as timer:
            try:
                # 1. 任务规划
                logger.info("🔍 第一阶段: 任务规划")
                plan = self.planner.plan(goal)
                
                if not plan.get("tasks"):
                    return "规划失败：无法生成有效的子任务"
                
                # 2. 创建总任务记录
                main_task_id = self.progress_manager.create_task(
                    description=goal,
                    task_type="main",
                    subtasks=[task["description"] for task in plan["tasks"]],
                    priority="normal"
                )
                
                logger.info(f"📝 生成了 {len(plan['tasks'])} 个子任务")
                
                # 3. 执行子任务
                logger.info("⚙️ 第二阶段: 任务执行")
                results = []
                
                for i, task in enumerate(plan["tasks"]):
                    logger.info(f"🔄 执行子任务 {i+1}/{len(plan['tasks'])}: {task['description'][:60]}...")
                    
                    # 创建子任务记录
                    subtask_id = self.progress_manager.create_task(
                        description=task["description"],
                        task_type=task.get("tool_type", "general"),
                        priority=task.get("priority", "normal")
                    )
                    
                    # 创建智能体
                    agent = self.factory.create_actor(
                        task_description=task["description"],
                        task_type=task.get("tool_type")
                    )
                    
                    # 分配任务
                    self.progress_manager.assign_task(subtask_id, agent.agent_id)
                    
                    # 执行任务
                    try:
                        result = agent.execute(task["description"], context)
                        results.append({
                            "task": task["description"],
                            "result": result,
                            "agent": agent.agent_id,
                            "success": True
                        })
                        
                        # 更新任务状态
                        self.progress_manager.complete_task(subtask_id, result)
                        
                    except Exception as e:
                        error_msg = f"子任务执行失败: {str(e)}"
                        results.append({
                            "task": task["description"],
                            "result": error_msg,
                            "agent": agent.agent_id,
                            "success": False
                        })
                        
                        # 更新任务状态
                        self.progress_manager.fail_task(subtask_id, error_msg)
                        logger.warning(f"子任务失败: {error_msg}")
                
                # 4. 生成最终结果
                logger.info("📊 第三阶段: 结果整合")
                final_result = self._integrate_results(goal, results)
                
                # 更新主任务状态
                success_count = sum(1 for r in results if r["success"])
                if success_count == len(results):
                    self.progress_manager.complete_task(main_task_id, final_result)
                elif success_count > 0:
                    self.progress_manager.update_progress(
                        main_task_id, 
                        progress=100.0 * success_count / len(results),
                        status="completed", 
                        result=final_result
                    )
                else:
                    self.progress_manager.fail_task(main_task_id, "所有子任务都失败")
                
                logger.info(f"✅ 任务执行完成，耗时: {timer.elapsed():.2f}秒")
                return final_result
                
            except Exception as e:
                error_msg = f"任务执行失败: {str(e)}"
                logger.error(error_msg)
                return error_msg
    
    def execute_multi_agent_task(self, goal: str, context: Dict[str, Any] = None) -> str:
        """执行多智能体协作任务
        
        Args:
            goal: 任务目标描述
            context: 上下文信息
            
        Returns:
            执行结果
        """
        logger.info(f"🤝 开始多智能体协作任务: {goal[:100]}...")
        
        # 规划阶段
        plan = self.planner.plan(goal, current_state="多智能体协作模式")
        
        if not plan.get("tasks"):
            return "协作规划失败：无法生成有效的协作计划"
        
        # 创建智能体团队
        team = {}
        for task in plan["tasks"]:
            agent = self.factory.create_actor(task["description"], task.get("tool_type"))
            team[agent.agent_id] = {
                "agent": agent,
                "task": task,
                "status": "ready"
            }
        
        logger.info(f"🎭 组建了 {len(team)} 个智能体的协作团队")
        
        # 并行执行（简化版）
        results = []
        shared_context = context or {}
        
        for agent_id, member in team.items():
            agent = member["agent"]
            task = member["task"]
            
            try:
                # 传递共享上下文
                result = agent.execute(task["description"], shared_context)
                
                # 更新共享上下文
                shared_context[f"result_from_{agent.agent_type}"] = result
                
                results.append({
                    "agent": agent_id,
                    "task": task["description"],
                    "result": result,
                    "success": True
                })
                
                member["status"] = "completed"
                
            except Exception as e:
                error_msg = f"智能体 {agent_id} 执行失败: {str(e)}"
                results.append({
                    "agent": agent_id,
                    "task": task["description"],
                    "result": error_msg,
                    "success": False
                })
                
                member["status"] = "failed"
                logger.warning(error_msg)
        
        # 整合协作结果
        return self._integrate_collaboration_results(goal, results, team)
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        system_status = self.progress_manager.get_system_status()
        
        return {
            "system_info": self.system_info,
            "tasks": system_status,
            "agents": {
                "total_created": len(self.factory.created_agents),
                "active_agents": system_status["active_agents"],
                "available_types": self.factory.get_available_types()
            },
            "uptime": time.time() - self.system_info["start_time"]
        }
    
    def generate_report(self) -> str:
        """生成系统报告"""
        return self.progress_manager.generate_report()
    
    def _integrate_results(self, goal: str, results: list) -> str:
        """整合任务结果"""
        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)
        
        report = f"任务: {goal}\n"
        report += f"执行结果: {success_count}/{total_count} 个子任务成功完成\n\n"
        
        # 成功的任务结果
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            report += "✅ 成功完成的任务:\n"
            for i, result in enumerate(successful_results, 1):
                report += f"{i}. {result['task'][:80]}...\n"
                report += f"   结果: {result['result'][:200]}...\n\n"
        
        # 失败的任务
        failed_results = [r for r in results if not r["success"]]
        if failed_results:
            report += "❌ 失败的任务:\n"
            for i, result in enumerate(failed_results, 1):
                report += f"{i}. {result['task'][:80]}...\n"
                report += f"   错误: {result['result'][:200]}...\n\n"
        
        # 总结
        if success_count == total_count:
            report += "🎉 所有子任务都成功完成！"
        elif success_count > total_count // 2:
            report += f"✨ 大部分任务完成，成功率: {success_count/total_count:.1%}"
        else:
            report += f"⚠️ 任务完成情况不理想，成功率: {success_count/total_count:.1%}"
        
        return report
    
    def _integrate_collaboration_results(self, goal: str, results: list, team: dict) -> str:
        """整合协作结果"""
        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)
        
        report = f"多智能体协作任务: {goal}\n"
        report += f"团队规模: {len(team)} 个智能体\n"
        report += f"协作成果: {success_count}/{total_count} 个智能体成功完成任务\n\n"
        
        # 按智能体类型整理结果
        by_type = {}
        for result in results:
            agent_id = result["agent"]
            agent_type = team[agent_id]["agent"].agent_type
            
            if agent_type not in by_type:
                by_type[agent_type] = []
            by_type[agent_type].append(result)
        
        # 展示各类智能体的贡献
        for agent_type, type_results in by_type.items():
            report += f"🤖 {agent_type.upper()} 智能体贡献:\n"
            for result in type_results:
                status = "✅" if result["success"] else "❌"
                report += f"  {status} {result['result'][:150]}...\n"
            report += "\n"
        
        # 协作总结
        if success_count == total_count:
            report += "🎊 多智能体协作圆满成功！所有智能体都出色完成了任务。"
        elif success_count > 0:
            report += f"🤝 协作基本成功，{success_count}/{total_count} 个智能体贡献了有效结果。"
        else:
            report += "😞 协作遇到困难，所有智能体都未能完成任务。"
        
        return report

def main():
    """主函数"""
    print("🤖 Aime多智能体框架原型")
    print("=" * 50)
    
    try:
        # 初始化系统
        aime = AimeSystem()
        
        # 显示系统信息
        status = aime.get_status()
        print(f"模型: {status['system_info']['model']}")
        print(f"可用智能体类型: {', '.join(status['agents']['available_types'])}")
        print()
        
        # 交互式使用
        if len(sys.argv) > 1:
            # 命令行模式
            goal = " ".join(sys.argv[1:])
            print(f"📋 执行任务: {goal}")
            result = aime.execute_task(goal)
            print(f"\n📊 执行结果:\n{result}")
        else:
            # 交互模式
            print("输入 'quit' 退出，'help' 查看帮助")
            
            while True:
                try:
                    goal = input("\n🎯 请输入任务目标: ").strip()
                    
                    if goal.lower() in ['quit', 'exit', 'q']:
                        break
                    elif goal.lower() == 'help':
                        print_help()
                        continue
                    elif goal.lower() == 'status':
                        print(aime.generate_report())
                        continue
                    elif goal.lower().startswith('multi:'):
                        # 多智能体协作模式
                        goal = goal[6:].strip()
                        result = aime.execute_multi_agent_task(goal)
                        print(f"\n🤝 协作结果:\n{result}")
                    elif goal:
                        # 普通任务
                        result = aime.execute_task(goal)
                        print(f"\n📊 执行结果:\n{result}")
                    
                except KeyboardInterrupt:
                    print("\n\n👋 再见！")
                    break
                except Exception as e:
                    print(f"\n❌ 执行错误: {e}")
        
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        print("💡 请检查API配置和网络连接")
        return 1
    
    return 0

def print_help():
    """打印帮助信息"""
    help_text = """
🤖 Aime多智能体框架 - 使用帮助

基本命令:
  <任务描述>      - 执行单智能体任务
  multi:<任务>    - 执行多智能体协作任务
  status          - 查看系统状态
  help            - 显示此帮助
  quit/exit/q     - 退出系统

示例:
  分析这段文本的情感倾向
  计算 123 + 456 的结果
  multi:研究人工智能在教育领域的应用
  status

💡 提示:
- 系统会自动选择合适的智能体类型
- 支持数学计算、文本分析、信息搜索等任务
- 多智能体模式适合复杂的综合性任务
"""
    print(help_text)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)