"""
PMS vs PUMA - 系统对比演示
==========================
解释为什么有了外部 PMS 还需要 PUMA 系统
"""

import json

print("=" * 80)
print("🤔 为什么有了 PMS 还需要 PUMA？")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PMS vs PUMA 定位对比                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────┐         ┌─────────────────────────────────────┐  │
│   │   外部 PMS 系统      │         │   PUMA 系统 (本项目)                 │  │
│   │   (Project Management│         │   (Project Unified Management App)  │  │
│   │    System)          │         │                                     │  │
│   ├─────────────────────┤         ├─────────────────────────────────────┤  │
│   │                     │         │                                     │  │
│   │ 📋 项目信息管理      │         │ 🔄 工作流执行引擎                    │  │
│   │    - 项目编号        │         │    - 任务分解与执行                  │  │
│   │    - 客户信息        │         │    - 状态跟踪 (Done/In Progress)    │  │
│   │    - 预算/时间       │         │    - 输入输出管理                    │  │
│   │    - 团队成员        │         │    - 自动化操作                      │  │
│   │                     │         │                                     │  │
│   │ 👥 人员管理         │         │ 🔐 细粒度权限控制                    │  │
│   │    - 谁参与项目      │         │    - Owner: 完全控制                │  │
│   │    - 角色分配        │         │    - Proxies: 可编辑                │  │
│   │                     │         │    - 其他: 无权限                    │  │
│   │                     │         │                                     │  │
│   │ 📊 项目状态报表      │         │ 📁 文件路径管理                      │  │
│   │    - 财务状态        │         │    - 云端路径映射                    │  │
│   │    - 进度概览        │         │    - 本地路径解析                    │  │
│   │                     │         │    - AlgoID 动态替换                 │  │
│   │                     │         │                                     │  │
│   │ 🌐 企业级系统        │         │ ⚡ 实时协作                          │  │
│   │    - 全公司项目      │         │    - SSE 实时推送                    │  │
│   │    - 只读/简单编辑   │         │    - 多人同时编辑                    │  │
│   │                     │         │    - 变更即时通知                    │  │
│   │                     │         │                                     │  │
│   └─────────────────────┘         └─────────────────────────────────────┘  │
│                                                                             │
│   💡 关系: PMS 是「项目信息源」 → PUMA 是「项目执行工作平台」                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 80)
print("📊 数据对比：PMS 原始数据 vs PUMA 扩展数据")
print("=" * 80)

# PMS 原始数据
pms_data = {
    "ProjectName": "Bosch智能工厂项目",
    "ProjectNo": "PRJ-2024-001",
    "Status": "Running",
    "Customer": "Bosch GmbH",
    "TeamMembers": [
        {"UID": "zhangsan", "Role": "PM"},
        {"UID": "lisi", "Role": "Engineer"}
    ],
    "StartDate": "2024-01-15",
    "EndDate": "2024-06-30",
    "Budget": 500000
}

print("\n" + "─" * 80)
print("📥 PMS 原始数据（从外部 API 获取）")
print("─" * 80)
print(json.dumps(pms_data, indent=2, ensure_ascii=False))

print("\n" + "─" * 80)
print("📤 PUMA 扩展后的完整数据")
print("─" * 80)

# PUMA 扩展后的数据
puma_data = {
    # ===== PMS 原始数据（保留）=====
    "id": 1,
    "projectName": "Bosch智能工厂项目",  # ← 来自 PMS
    "department": "研发部",  # ← 同步时指定
    
    # ===== PUMA 新增：权限系统 =====
    "username": "SYSTEM",  # 系统创建
    "owner": "",  # PMS项目无owner，需后续分配
    "proxies": "张三, 李四",  # ← 从 PMS.TeamMembers 映射
    "editors": [],
    
    # ===== PUMA 新增：动态表单系统 =====
    "projectInfo": {
        # 基础信息（来自PMS）
        "projectInfo": [
            [{"label": "项目编号", "value": "PRJ-2024-001", "type": "text"},
             {"label": "客户名称", "value": "Bosch GmbH", "type": "text"}],
            [{"label": "开始日期", "value": "2024-01-15", "type": "date"},
             {"label": "预计完成", "value": "2024-06-30", "type": "date"}],
            [{"label": "预算(元)", "value": "500000", "type": "number"}]
        ],
        # 权限块
        "owner": {"label": "Owner", "value": ""},
        "proxies": {"label": "Proxies", "value": "张三, 李四"},
        "uuid": {"label": "uuid", "value": "550e8400-e29b-41d4-a716-446655440000"}
    },
    
    # ===== PUMA 核心新增：工作流系统（PMS完全没有）=====
    "projectWorkFlow": {
        "taskTree": [
            {
                "id": "uuid-task-001",
                "taskName": "项目启动",
                "status": "Done",  # ← 可执行、可跟踪
                "children": [
                    {
                        "id": "uuid-task-002",
                        "taskName": "需求分析",
                        "status": "Done",
                        "children": [
                            {
                                "id": "uuid-task-003",
                                "taskName": "客户访谈",
                                "status": "Done",
                                "children": []
                            },
                            {
                                "id": "uuid-task-004",
                                "taskName": "需求文档",
                                "status": "Done",
                                "children": []
                            }
                        ]
                    },
                    {
                        "id": "uuid-task-005",
                        "taskName": "方案设计",
                        "status": "In Progress",  # ← 当前进行中
                        "children": [
                            {
                                "id": "uuid-task-006",
                                "taskName": "技术选型",
                                "status": "Done",
                                "children": []
                            },
                            {
                                "id": "uuid-task-007",
                                "taskName": "架构设计",
                                "status": "In Progress",
                                "children": []
                            },
                            {
                                "id": "uuid-task-008",
                                "taskName": "原型开发",
                                "status": "In Progress",
                                "children": []
                            }
                        ]
                    },
                    {
                        "id": "uuid-task-009",
                        "taskName": "开发实施",
                        "status": "In Progress",
                        "children": [
                            {
                                "id": "uuid-task-010",
                                "taskName": "编码",
                                "status": "In Progress",
                                "children": []
                            },
                            {
                                "id": "uuid-task-011",
                                "taskName": "测试",
                                "status": "In Progress",
                                "children": []
                            }
                        ]
                    },
                    {
                        "id": "uuid-task-012",
                        "taskName": "交付验收",
                        "status": "In Progress",
                        "children": []
                    }
                ]
            }
        ],
        # 任务详情（输入输出、操作配置）
        "taskDetails": {
            "uuid-task-003": {
                "inputs": [],
                "outputs": ["访谈记录.docx"],
                "operation": {"type": "manual", "description": "与客户进行需求访谈"},
                "description": "收集客户业务需求"
            },
            "uuid-task-004": {
                "inputs": ["访谈记录.docx"],
                "outputs": ["需求规格说明书.pdf"],
                "operation": {"type": "manual", "description": "编写需求文档"},
                "description": "整理并输出需求文档"
            },
            "uuid-task-006": {
                "inputs": ["需求规格说明书.pdf"],
                "outputs": ["技术选型报告.pdf"],
                "operation": {
                    "type": "auto",  # ← 自动化操作！
                    "script": "tech_eval.py",
                    "params": {"criteria": ["performance", "cost", "maintainability"]}
                },
                "description": "评估并选择技术方案"
            },
            "uuid-task-010": {
                "inputs": ["架构设计文档.pdf"],
                "outputs": ["源代码.zip"],
                "operation": {
                    "type": "auto",
                    "script": "code_gen.py",
                    "params": {"template": "microservice"}
                },
                "description": "根据架构自动生成代码框架"
            }
        }
    },
    
    # ===== PUMA 新增：元数据 =====
    "tags": ["Running"],  # ← 从 PMS.Status 映射
    "comment": "",
    "orderIndex": 0,
    "progress": 0.35  # ← 自动计算：已完成任务/总任务
}

print(json.dumps(puma_data, indent=2, ensure_ascii=False))

print("\n\n" + "=" * 80)
print("🔍 PUMA 对 PMS 数据的扩展详解")
print("=" * 80)

