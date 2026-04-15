"""
工作流 (projectWorkFlow) 数据结构示例
======================================
演示项目工作流是如何组织和存储的
"""

import json

# ========== 第1步：简单的工作流结构 ==========
print("=" * 60)
print("示例1: 简单的工作流（一个项目包含多个任务）")
print("=" * 60)

simple_workflow = {
    "taskTree": [  # 任务树，包含多个任务节点
        {
            "id": "task_1",
            "name": "需求分析",
            "status": "Done",  # 状态：Done, In Progress, Not Started, Decline
            "children": []     # 子任务（可以是嵌套的）
        },
        {
            "id": "task_2",
            "name": "系统设计",
            "status": "In Progress",
            "children": []
        },
        {
            "id": "task_3",
            "name": "开发实现",
            "status": "Not Started",
            "children": []
        }
    ],
    "taskDetails": {  # 任务的详细信息
        "task_1": {
            "assignee": "张三",
            "startDate": "2024-01-01",
            "endDate": "2024-01-10",
            "description": "收集和分析用户需求"
        },
        "task_2": {
            "assignee": "李四",
            "startDate": "2024-01-11",
            "endDate": "2024-01-20",
            "description": "设计系统架构"
        }
    }
}

print("Python 字典格式:")
print(json.dumps(simple_workflow, indent=2, ensure_ascii=False))

# 存储到数据库时会转为 JSON 字符串
json_string = json.dumps(simple_workflow)
print(f"\n存储到数据库的 JSON 字符串（前100字符）:")
print(json_string[:100] + "...")

# ========== 第2步：复杂的工作流（嵌套子任务） ==========
print("\n" + "=" * 60)
print("示例2: 复杂的工作流（嵌套子任务）")
print("=" * 60)

complex_workflow = {
    "taskTree": [
        {
            "id": "phase_1",
            "name": "第一阶段：需求",
            "status": "Done",
            "children": [
                {
                    "id": "task_1_1",
                    "name": "用户调研",
                    "status": "Done",
                    "children": []
                },
                {
                    "id": "task_1_2",
                    "name": "需求文档",
                    "status": "Done",
                    "children": []
                }
            ]
        },
        {
            "id": "phase_2",
            "name": "第二阶段：开发",
            "status": "In Progress",
            "children": [
                {
                    "id": "task_2_1",
                    "name": "前端开发",
                    "status": "In Progress",
                    "children": [
                        {
                            "id": "task_2_1_1",
                            "name": "页面设计",
                            "status": "Done",
                            "children": []
                        },
                        {
                            "id": "task_2_1_2",
                            "name": "组件开发",
                            "status": "In Progress",
                            "children": []
                        }
                    ]
                },
                {
                    "id": "task_2_2",
                    "name": "后端开发",
                    "status": "Not Started",
                    "children": []
                }
            ]
        },
        {
            "id": "phase_3",
            "name": "第三阶段：测试",
            "status": "Not Started",
            "children": [
                {
                    "id": "task_3_1",
                    "name": "单元测试",
                    "status": "Not Started",
                    "children": []
                },
                {
                    "id": "task_3_2",
                    "name": "集成测试",
                    "status": "Not Started",
                    "children": []
                }
            ]
        }
    ],
    "taskDetails": {
        "phase_1": {"assignee": "产品经理", "priority": "High"},
        "phase_2": {"assignee": "开发团队", "priority": "High"},
        "task_2_1": {"assignee": "前端组", "priority": "Medium"},
        "task_2_2": {"assignee": "后端组", "priority": "Medium"}
    }
}

print("复杂工作流结构（树形）:")
print(json.dumps(complex_workflow, indent=2, ensure_ascii=False))

# ========== 第3步：计算进度 ==========
print("\n" + "=" * 60)
print("示例3: 计算项目进度")
print("=" * 60)

def count_tasks(task_tree):
    """递归统计任务数"""
    total = 0
    done = 0
    
    def dfs(node):
        nonlocal total, done
        total += 1
        if node.get("status") in ("Done", "Decline"):
            done += 1
        # 递归处理子任务
        for child in node.get("children", []):
            dfs(child)
    
    for root in task_tree:
        dfs(root)
    
    return total, done

total, done = count_tasks(complex_workflow["taskTree"])
progress = done / total if total > 0 else 0

print(f"总任务数: {total}")
print(f"已完成: {done}")
print(f"进度: {progress:.1%}")

# ========== 第4步：实际项目中的使用 ==========
print("\n" + "=" * 60)
print("示例4: 实际项目中的使用流程")
print("=" * 60)

# 1. 创建项目时设置工作流
print("\n1. 创建项目时设置工作流:")
new_project = {
    "projectName": "电商平台开发",
    "projectWorkFlow": json.dumps({
        "taskTree": [
            {"id": "1", "name": "需求分析", "status": "Done", "children": []},
            {"id": "2", "name": "系统设计", "status": "In Progress", "children": []},
            {"id": "3", "name": "编码开发", "status": "Not Started", "children": []},
            {"id": "4", "name": "测试上线", "status": "Not Started", "children": []}
        ],
        "taskDetails": {}
    })
}
print(f"工作流已存储（字符串长度: {len(new_project['projectWorkFlow'])} 字符）")

# 2. 从数据库读取后解析
print("\n2. 从数据库读取后解析:")
workflow_from_db = json.loads(new_project["projectWorkFlow"])
print(f"解析后的任务数: {len(workflow_from_db['taskTree'])}")
for task in workflow_from_db["taskTree"]:
    print(f"   - {task['name']}: {task['status']}")

# 3. 更新任务状态
print("\n3. 更新任务状态:")
workflow_from_db["taskTree"][1]["status"] = "Done"  # 系统设计完成
workflow_from_db["taskTree"][2]["status"] = "In Progress"  # 开始编码
print("更新后的状态:")
for task in workflow_from_db["taskTree"]:
    print(f"   - {task['name']}: {task['status']}")

# 4. 保存回数据库（转回 JSON 字符串）
updated_workflow_string = json.dumps(workflow_from_db)
print(f"\n4. 保存回数据库（字符串长度: {len(updated_workflow_string)} 字符）")

print("\n" + "=" * 60)
print("总结:")
print("=" * 60)
print("""
projectWorkFlow 是一个 JSON 字符串，存储在 Text 字段中，包含：

1. taskTree: 任务树结构（支持嵌套子任务）
   - id: 任务唯一标识
   - name: 任务名称
   - status: 任务状态（Done/In Progress/Not Started/Decline）
   - children: 子任务列表（实现树形结构）

2. taskDetails: 任务详细信息
   - assignee: 负责人
   - startDate/endDate: 起止日期
   - priority: 优先级
   - description: 描述

优点：
- 灵活：可以存储任意复杂的任务结构
- 可扩展：随时添加新字段
- 易计算：可以递归计算完成进度

缺点：
- 不能直接 SQL 查询内部字段
- 需要应用层解析 JSON
""")
