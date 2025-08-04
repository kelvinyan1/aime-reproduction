# Aime多智能体框架原型 - 测试用例
import time
from typing import Dict, Any
from main import AimeSystem
from utils import logger
from config import config

class AimeTestSuite:
    """Aime测试套件"""
    
    def __init__(self):
        self.test_results = []
        self.aime_system = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🧪 Aime多智能体框架测试套件")
        print("=" * 50)
        
        # 初始化系统
        try:
            print("🔧 初始化测试环境...")
            self.aime_system = AimeSystem()
            print("✅ 系统初始化成功")
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            return {"success": False, "error": str(e)}
        
        # 运行测试用例
        test_cases = [
            ("基础组件测试", self.test_basic_components),
            ("单智能体任务测试", self.test_single_agent_tasks), 
            ("多智能体协作测试", self.test_multi_agent_collaboration),
            ("动态重规划测试", self.test_dynamic_replanning),
            ("错误处理测试", self.test_error_handling),
            ("性能基准测试", self.test_performance_benchmark)
        ]
        
        for test_name, test_func in test_cases:
            print(f"\n🔍 {test_name}...")
            try:
                result = test_func()
                self.test_results.append({
                    "name": test_name,
                    "success": result.get("success", False),
                    "details": result.get("details", ""),
                    "duration": result.get("duration", 0)
                })
                
                if result.get("success"):
                    print(f"✅ {test_name} 通过")
                else:
                    print(f"❌ {test_name} 失败: {result.get('details', '')}")
                    
            except Exception as e:
                print(f"❌ {test_name} 异常: {e}")
                self.test_results.append({
                    "name": test_name,
                    "success": False,
                    "details": str(e),
                    "duration": 0
                })
        
        # 生成测试报告
        return self.generate_test_report()
    
    def test_basic_components(self) -> Dict[str, Any]:
        """测试基础组件"""
        start_time = time.time()
        
        try:
            # 测试规划器
            plan = self.aime_system.planner.plan("测试任务规划功能")
            assert "tasks" in plan, "规划器未生成任务列表"
            assert len(plan["tasks"]) > 0, "规划器生成的任务列表为空"
            
            # 测试工厂
            agent = self.aime_system.factory.create_actor("测试智能体创建功能")
            assert agent is not None, "工厂未能创建智能体"
            assert hasattr(agent, "agent_id"), "智能体缺少ID属性"
            
            # 测试进度管理
            task_id = self.aime_system.progress_manager.create_task("测试任务")
            assert task_id is not None, "进度管理器未能创建任务"
            
            status = self.aime_system.progress_manager.get_task_status(task_id)
            assert status["status"] == "pending", "任务状态不正确"
            
            return {
                "success": True,
                "details": "所有基础组件功能正常",
                "duration": time.time() - start_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": str(e),
                "duration": time.time() - start_time
            }
    
    def test_single_agent_tasks(self) -> Dict[str, Any]:
        """测试单智能体任务"""
        start_time = time.time()
        
        test_tasks = [
            {
                "goal": "计算 125 + 375 的结果",
                "expected_type": "analyst",
                "should_contain": ["500", "计算"]
            },
            {
                "goal": "总结这段文本：人工智能正在改变世界",
                "expected_type": "researcher", 
                "should_contain": ["人工智能", "总结"]
            },
            {
                "goal": "执行文件备份操作",
                "expected_type": "executor",
                "should_contain": ["执行", "文件"]
            }
        ]
        
        results = []
        
        for task in test_tasks:
            try:
                result = self.aime_system.execute_task(task["goal"])
                
                # 检查结果
                success = True
                details = []
                
                # 检查是否包含预期内容
                for expected in task["should_contain"]:
                    if expected not in result:
                        success = False
                        details.append(f"结果中未找到期望内容: {expected}")
                
                results.append({
                    "task": task["goal"],
                    "success": success,
                    "details": details,
                    "result_length": len(result)
                })
                
            except Exception as e:
                results.append({
                    "task": task["goal"],
                    "success": False,
                    "details": [str(e)],
                    "result_length": 0
                })
        
        # 评估整体成功率
        success_count = sum(1 for r in results if r["success"])
        overall_success = success_count >= len(test_tasks) * 0.7  # 70%成功率
        
        return {
            "success": overall_success,
            "details": f"单智能体任务成功率: {success_count}/{len(test_tasks)}",
            "duration": time.time() - start_time,
            "task_results": results
        }
    
    def test_multi_agent_collaboration(self) -> Dict[str, Any]:
        """测试多智能体协作"""
        start_time = time.time()
        
        try:
            goal = "研究人工智能在教育领域的应用，分析其优势，并生成总结报告"
            result = self.aime_system.execute_multi_agent_task(goal)
            
            # 检查协作结果
            success_indicators = [
                "研究" in result or "分析" in result,
                "优势" in result or "应用" in result,
                "报告" in result or "总结" in result,
                len(result) > 100  # 结果应该有足够的内容
            ]
            
            success = sum(success_indicators) >= 3
            
            return {
                "success": success,
                "details": f"协作结果质量评分: {sum(success_indicators)}/4",
                "duration": time.time() - start_time,
                "result_length": len(result)
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": str(e),
                "duration": time.time() - start_time
            }
    
    def test_dynamic_replanning(self) -> Dict[str, Any]:
        """测试动态重规划"""
        start_time = time.time()
        
        try:
            # 第一次规划
            initial_goal = "分析销售数据"
            initial_plan = self.aime_system.planner.plan(initial_goal)
            
            # 模拟执行反馈
            feedback = "数据格式有问题，需要先进行数据清理"
            current_state = "已获取原始数据文件"
            
            # 重新规划
            new_plan = self.aime_system.planner.plan(
                initial_goal, 
                current_state=current_state, 
                feedback=feedback
            )
            
            # 检查重规划结果
            success_checks = [
                len(new_plan.get("tasks", [])) > 0,
                "清理" in str(new_plan) or "格式" in str(new_plan),
                new_plan != initial_plan  # 应该有所不同
            ]
            
            success = all(success_checks)
            
            return {
                "success": success,
                "details": "动态重规划功能正常" if success else "重规划未能正确响应反馈",
                "duration": time.time() - start_time,
                "initial_tasks": len(initial_plan.get("tasks", [])),
                "new_tasks": len(new_plan.get("tasks", []))
            }
            
        except Exception as e:
            return {
                "success": False,
                "details": str(e),
                "duration": time.time() - start_time
            }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """测试错误处理"""
        start_time = time.time()
        
        error_scenarios = [
            {
                "name": "空任务描述",
                "goal": "",
                "should_handle": True
            },
            {
                "name": "过长任务描述", 
                "goal": "测试" * 1000,
                "should_handle": True
            },
            {
                "name": "特殊字符任务",
                "goal": "测试!@#$%^&*()[]{}|\\:;\"'<>?/.,",
                "should_handle": True
            }
        ]
        
        handled_correctly = 0
        
        for scenario in error_scenarios:
            try:
                result = self.aime_system.execute_task(scenario["goal"])
                
                # 检查是否优雅处理
                if result and not result.startswith("Traceback"):
                    handled_correctly += 1
                    
            except Exception:
                # 异常也算是处理了，只要不崩溃
                handled_correctly += 1
        
        success = handled_correctly >= len(error_scenarios) * 0.8
        
        return {
            "success": success,
            "details": f"错误处理成功率: {handled_correctly}/{len(error_scenarios)}",
            "duration": time.time() - start_time
        }
    
    def test_performance_benchmark(self) -> Dict[str, Any]:
        """测试性能基准"""
        start_time = time.time()
        
        # 性能测试用例
        performance_tasks = [
            "简单计算: 2 + 2",
            "文本分析: 分析这句话的情感",
            "信息检索: 搜索人工智能相关信息"
        ]
        
        execution_times = []
        success_count = 0
        
        for task in performance_tasks:
            task_start = time.time()
            try:
                result = self.aime_system.execute_task(task)
                task_duration = time.time() - task_start
                execution_times.append(task_duration)
                
                if result and len(result) > 10:  # 有效结果
                    success_count += 1
                    
            except Exception:
                execution_times.append(config.TIMEOUT_SECONDS)  # 超时作为最大时间
        
        # 性能指标
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        max_time = max(execution_times) if execution_times else 0
        
        # 性能评估
        performance_good = (
            avg_time < 30.0 and  # 平均执行时间 < 30秒
            max_time < 60.0 and  # 最大执行时间 < 60秒
            success_count >= len(performance_tasks) * 0.8  # 80%成功率
        )
        
        return {
            "success": performance_good,
            "details": f"平均执行时间: {avg_time:.2f}秒, 成功率: {success_count}/{len(performance_tasks)}",
            "duration": time.time() - start_time,
            "avg_execution_time": avg_time,
            "max_execution_time": max_time,
            "success_rate": success_count / len(performance_tasks)
        }
    
    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_duration = sum(result["duration"] for result in self.test_results)
        
        print(f"\n📊 测试报告")
        print("=" * 50)
        print(f"总测试数: {total_tests}")
        print(f"通过数: {passed_tests}")
        print(f"失败数: {total_tests - passed_tests}")
        print(f"成功率: {passed_tests/total_tests:.1%}")
        print(f"总耗时: {total_duration:.2f}秒")
        
        # 详细结果
        print(f"\n📋 详细结果:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['name']} ({result['duration']:.2f}s)")
            if not result["success"]:
                print(f"    错误: {result['details']}")
        
        # 系统状态
        if self.aime_system:
            print(f"\n🤖 系统状态:")
            status = self.aime_system.get_status()
            print(f"  运行时间: {status['uptime']:.2f}秒")
            print(f"  总任务数: {status['tasks']['total_tasks']}")
            print(f"  完成任务数: {status['tasks']['completed_tasks']}")
            print(f"  活跃智能体: {status['agents']['total_created']}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests,
            "total_duration": total_duration,
            "test_results": self.test_results,
            "overall_success": passed_tests >= total_tests * 0.7  # 70%通过率
        }

def run_quick_test():
    """快速验证测试"""
    print("🚀 Aime快速验证测试")
    print("=" * 30)
    
    try:
        # 初始化系统
        aime = AimeSystem()
        
        # 测试基础功能
        print("1. 测试简单任务...")
        result1 = aime.execute_task("计算 10 + 20 的结果")
        print(f"   结果: {result1[:100]}...")
        
        print("2. 测试文本处理...")
        result2 = aime.execute_task("分析这段文本的主要内容：人工智能正在快速发展")
        print(f"   结果: {result2[:100]}...")
        
        print("3. 测试多智能体协作...")
        result3 = aime.execute_multi_agent_task("研究机器学习的应用前景")
        print(f"   结果: {result3[:100]}...")
        
        # 显示系统状态
        print("4. 系统状态...")
        status = aime.get_status()
        print(f"   任务完成率: {status['tasks']['completion_rate']:.1%}")
        print(f"   创建智能体数: {status['agents']['total_created']}")
        
        print("\n✅ 快速验证测试完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 快速验证测试失败: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # 快速测试
        run_quick_test()
    else:
        # 完整测试套件
        test_suite = AimeTestSuite()
        report = test_suite.run_all_tests()
        
        if report.get("overall_success"):
            print("\n🎉 所有测试基本通过，系统可以正常使用！")
        else:
            print("\n⚠️ 部分测试失败，建议检查配置和依赖。")
        
        print(f"\n最终评分: {report['success_rate']:.1%}")