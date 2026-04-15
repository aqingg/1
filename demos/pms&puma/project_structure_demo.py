"""
Project 数据结构可视化演示
============================
展示系统中 "project" 的完整属性结构
"""

import json

print("=" * 70)
print("📦 Project 数据结构 - 属性图解")
print("=" * 70)

print("""
┌─────────────────────────────────────────────────────────────────────┐
│                         🗃️  Project 数据表                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📌 基础信息字段 (数据库直接存储)                                    │
│  ┌─────────────────┬──────────────┬────────────────────────────────┐│
│  │ 字段名          │ 类型         │ 说明                           ││
│  ├─────────────────┼──────────────┼────────────────────────────────┤│
│  │ id              │ Integer      │ 项目唯一ID (主键)              ││
│  │ username        │ String       │ 创建者账号                     ││
│  │ owner           │ String       │ 项目负责人姓名                 ││
│  │ department      │ String       │ 所属部门                       ││
│  │ projectName     │ String       │ 项目名称                       ││
│  │ comment         │ Text         │ 项目备注                       ││
│  │ tags            │ Text(JSON)   │ 项目标签 ["quotation", ...]    ││
│  │ editors         │ Text(JSON)   │ 编辑者列表                     ││
│  │ orderIndex      │ Integer      │ 排序索引                       ││
│  └─────────────────┴──────────────┴────────────────────────────────┘│
│                                                                     │
│  📦 JSON 字段 (复杂结构，以JSON字符串存储)                           │
│  ┌─────────────────┬────────────────────────────────────────────────┐│
│  │ projectInfo     │ 项目元信息 (owner, proxies, uuid, 表单数据)    ││
│  │ projectWorkFlow │ 工作流数据 (taskTree任务树, taskDetails详情)   ││
│  └─────────────────┴────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 70)
print("📋 Project 数据结构 - 详细展开")
print("=" * 70)

print("""
Project
├── 🔢 id: 1                          ← 项目唯一标识
├── 👤 username: "zhangsan"           ← 创建者账号
├── 👑 owner: "张三"                   ← 项目负责人姓名
├── 🏢 department: "研发部"            ← 所属部门
├── 📁 projectName: "项目A"            ← 项目名称
├── 💬 comment: "这是一个测试项目"      ← 备注
├── 🏷️  tags: ["quotation"]            ← 标签 (quotation/running/sop)
├── ✏️  editors: ["李四", "王五"]       ← 可编辑人员
├── 📊 orderIndex: 0                   ← 排序位置
│
├── 📄 projectInfo (JSON对象)
│   ├── owner: {"label": "Owner", "value": "张三"}
│   ├── proxies: {"label": "Proxies", "value": "李四,王五"}
│   ├── uuid: {"label": "uuid", "value": "550e8400-e29b-41d4-a716-446655440000"}
│   └── projectInfo: [                   ← 动态表单数据
│       ├── {"label": "项目编号", "value": "PRJ-2024-001", "type": "text"}
│       ├── {"label": "客户名称", "value": "ABC公司", "type": "text"}
│       ├── {"label": "开始日期", "value": "2024-01-15", "type": "date"}
│       └── {"label": "预算", "value": "100000", "type": "number"}
│   ]
│
└── ⚙️ projectWorkFlow (JSON对象)
    ├── taskTree: [                      ← 任务树结构
    │   └── {
    │       "id": "uuid-1",
    │       "taskName": "项目启动",
    │       "status": "Done",            ← Done / In Progress / Decline
    │       "children": [
    │           {
    │               "id": "uuid-2",
    │               "taskName": "需求分析",
    │               "status": "In Progress",
    │               "children": [...]
    │           }
    │       ]
    │   }
    │
    └── taskDetails: {                   ← 任务详情映射
        "uuid-1": {
            "inputs": [...],
            "outputs": [...],
            "operation": {...},
            "description": "任务描述"
        },
        "uuid-2": { ... }
    }
""")

print("\n" + "=" * 70)
print("📝 实际样例 - 一个真实的 Project 对象")
print("=" * 70)

# 创建一个完整的样例
sample_project = {
    "id": 1,
    "username": "zhangsan",
    "owner": "张三",
    "department": "研发部",
    "projectName": "智能分析平台",
    "comment": "Q1季度重点项目，预计3个月完成",
    "tags": ["running"],
    "editors": ["李四"],
    "orderIndex": 0,
    "progress": 0.35,  # 由 calc_progress() 自动计算
    
    "projectInfo": {
        "owner": {"label": "Owner", "value": "张三"},
        "proxies": {"label": "Proxies", "value": "李四"},
        "uuid": {"label": "uuid", "value": "550e8400-e29b-41d4-a716-446655440000"},
        "projectInfo": [
            {"label": "项目编号", "value": "PRJ-2024-001", "type": "text"},
            {"label": "客户名称", "value": "ABC科技有限公司", "type": "text"},
            {"label": "开始日期", "value": "2024-01-15", "type": "date"},
            {"label": "预计完成", "value": "2024-04-15", "type": "date"},
            {"label": "预算(元)", "value": "500000", "type": "number"},
            {"label": "项目状态", "value": "进行中", "type": "select"}
        ]
    },
    
    "projectWorkFlow": {
        "taskTree": [
            {
                "id": "task-001",
                "taskName": "项目启动",
                "status": "Done",
                "children": [
                    {
                        "id": "task-002",
                        "taskName": "需求调研",
                        "status": "Done",
                        "children": []
                    },
                    {
                        "id": "task-003",
                        "taskName": "方案设计",
                        "status": "In Progress",
                        "children": [
                            {
                                "id": "task-004",
                                "taskName": "技术选型",
                                "status": "Done",
                                "children": []
                            },
                                {
                                "id": "task-005",
                                "taskName": "架构设计",
                                "status": "In Progress",
                                "children": []
                            }
                        ]
                    }
                ]
            }
        ],
        "taskDetails": {
            "task-001": {
                "inputs": [],
                "outputs": ["立项文档"],
                "operation": {"type": "manual"},
                "description": "项目启动会议，确定目标和团队"
            },
            "task-002": {
                "inputs": [],
                "outputs": ["需求文档"],
                "operation": {"type": "manual"},
                "description": "与客户沟通，收集业务需求"
            },
            "task-003": {
                "inputs": ["需求文档"],
                "outputs": ["设计文档"],
                "operation": {"type": "manual"},
                "description": "制定技术方案和项目计划"
            }
        }
    }
}

print("\n📦 Python 字典格式:")
print("-" * 50)
print(json.dumps(sample_project, indent=2, ensure_ascii=False))

print("\n\n" + "=" * 70)
print("🔍 关键概念说明")
print("=" * 70)

print("""
1️⃣  权限控制
    ├── owner (张三): 拥有所有权限（查看、编辑、删除）
    ├── proxies (李四): 可以编辑项目
    └── 其他用户: 无权限访问

2️⃣  项目标签 (tags)
    ├── ["quotation"]: 报价阶段
    ├── ["running"]: 进行中
    └── ["sop"]: 标准作业程序

3️⃣  工作流状态 (status)
    ├── "Done": 已完成 ✓
    ├── "In Progress": 进行中 🔄
    └── "Decline": 已拒绝/跳过 ✗

4️⃣  进度计算 (progress)
    自动计算 = 已完成任务数 / 总任务数
    示例: 2个Done / 5个总任务 = 0.4 (40%)

5️⃣  UUID 作用
    每个任务节点都有唯一UUID，用于:
    ├── 精确定位任务
    ├── 关联任务详情 (taskDetails)
    └── 路径解析 (AlgoID替换)
""")

print("\n" + "=" * 70)
print("✅ 演示完成！")
print("=" * 70)
