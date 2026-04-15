"""
PMS 模块功能演示
===============
直观展示 pms.py 三个接口的作用
"""

import json
from datetime import datetime

print("=" * 80)
print("🔗 PMS 外部系统集成 - 功能演示")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PMS 系统架构图                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐       │
│   │  外部 PMS    │         │   PUMA 系统   │         │   PUMA 数据库  │       │
│   │  服务器      │◄───────►│  (pms.py)    │◄───────►│  (Project表)  │       │
│   └──────────────┘         └──────────────┘         └──────────────┘       │
│          ▲                        │                                          │
│          │                        │                                          │
│          │              ┌─────────┴─────────┐                                │
│          │              │  data_source/     │                                │
│          └──────────────┤  PMS.json (缓存)   │                                │
│                         └───────────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

📋 三个核心接口流程：

    Step 1: refresh          Step 2: preview          Step 3: sync
    ┌──────────┐             ┌──────────┐             ┌──────────┐
    │  拉取数据  │────────────►│  预览数据  │────────────►│  同步入库  │
    │  (外部API)│             │ (本地JSON)│             │ (数据库)  │
    └──────────┘             └──────────┘             └──────────┘
""")

print("\n" + "=" * 80)
print("🔄 接口 1: POST /pms/refresh - 从外部 PMS 拉取数据")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│  功能说明                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  • 调用外部 PMS API: http://apiroutecccn.apac.bosch.com/...                │
│  • 获取所有客户项目数据                                                      │
│  • 保存到本地: data_source/PMS.json                                         │
│  • 添加元信息: 更新时间、数据条数                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""")

# 模拟外部 PMS 返回的数据
mock_pms_api_response = [
    {
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
    },
    {
        "ProjectName": "自动化生产线改造",
        "ProjectNo": "PRJ-2024-002",
        "Status": "Quotation",
        "Customer": "Siemens AG",
        "TeamMembers": [
            {"UID": "wangwu", "Role": "Lead"}
        ],
        "StartDate": "2024-03-01",
        "EndDate": "2024-08-15",
        "Budget": 800000
    },
    {
        "ProjectName": "质量检测系统升级",
        "ProjectNo": "PRJ-2024-003",
        "Status": "SOP",
        "Customer": "BASF SE",
        "TeamMembers": [
            {"UID": "zhangsan", "Role": "Engineer"},
            {"UID": "zhaoliu", "Role": "Tester"}
        ],
        "StartDate": "2023-10-01",
        "EndDate": "2024-02-28",
        "Budget": 300000
    }
]

print("📥 模拟外部 PMS API 返回的数据:")
print("-" * 60)
print(f"共 {len(mock_pms_api_response)} 个项目")
print()
for i, proj in enumerate(mock_pms_api_response, 1):
    print(f"  {i}. {proj['ProjectName']}")
    print(f"     编号: {proj['ProjectNo']} | 状态: {proj['Status']} | 客户: {proj['Customer']}")
    print(f"     团队: {', '.join([m['UID'] for m in proj['TeamMembers']])}")
    print()

# 模拟保存到 PMS.json
pms_json_content = {
    "meta": {
        "updatedAt": datetime.now().isoformat(),
        "count": len(mock_pms_api_response)
    },
    "data": mock_pms_api_response
}

print("💾 保存到 data_source/PMS.json:")
print("-" * 60)
print(json.dumps(pms_json_content, indent=2, ensure_ascii=False))

print("\n\n" + "=" * 80)
print("👁️ 接口 2: GET /pms/preview - 预览本地 PMS 数据")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│  功能说明                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  • 读取本地 PMS.json 文件                                                    │
│  • 支持 limit 参数控制返回条数 (默认20, 最大200)                             │
│  • 返回总条数和预览数据                                                       │
│  • 用于查看有哪些项目可以同步                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
""")

print("📤 预览接口返回格式:")
print("-" * 60)
preview_response = {
    "success": True,
    "total": 3,
    "returned": 3,
    "preview": mock_pms_api_response
}
print(json.dumps(preview_response, indent=2, ensure_ascii=False))

print("\n\n" + "=" * 80)
print("🚀 接口 3: POST /pms/sync - 同步到 PUMA 数据库（核心功能）")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│  功能说明                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  • 从 PMS.json 读取项目数据                                                  │
│  • 字段映射: PMS字段 → PUMA表单字段 (通过 DataMapping.json)                  │
│  • 权限设置: 根据 TeamMembers 自动设置 proxies (可编辑人员)                   │
│  • 工作流生成: 使用部门模板创建任务树                                         │
│  • 标签同步: 将 PMS Status 写入 PUMA tags                                    │
│  • 仅新增: 已存在项目跳过，不覆盖                                            │
└─────────────────────────────────────────────────────────────────────────────┘
""")

print("\n📋 同步流程详细步骤:\n")

print("Step 1: 加载配置")
print("-" * 60)
print("  ✓ 加载 PMS.json (3个项目)")
print("  ✓ 加载 unified.json 模板 (研发部)")
print("  ✓ 加载 TeamMembers.json (账号→姓名映射)")
print("  ✓ 加载 DataMapping.json (字段映射规则)")

# 模拟 TeamMembers 映射
team_members_map = {
    "ZHANGSAN": "张三",
    "LISI": "李四",
    "WANGWU": "王五",
    "ZHAOLIU": "赵六"
}

print("\n  账号映射表:")
for account, name in team_members_map.items():
    print(f"    {account} → {name}")

print("\n\nStep 2: 字段映射规则 (DataMapping.json)")
print("-" * 60)
field_mapping = {
    "ProjectNo": "项目编号",
    "Customer": "客户名称",
    "StartDate": "开始日期",
    "EndDate": "预计完成",
    "Budget": "预算(元)"
}
print("  PMS字段 → PUMA字段:")
for pms_field, puma_field in field_mapping.items():
    print(f"    {pms_field:15} → {puma_field}")

print("\n\nStep 3: 处理每个项目")
print("-" * 60)

sync_results = []
existing_projects = ["已有项目X"]  # 模拟已存在的项目

for i, pms_item in enumerate(mock_pms_api_response, 1):
    project_name = pms_item["ProjectName"]
    print(f"\n  项目 {i}: {project_name}")
    
    # 检查是否已存在
    if project_name in existing_projects:
        print(f"    ⚠️  已存在，跳过")
        sync_results.append({"name": project_name, "status": "skipped", "reason": "已存在"})
        continue
    
    # 计算 proxies
    team = pms_item.get("TeamMembers", [])
    proxies = set()
    for member in team:
        uid = member.get("UID", "").upper()
        if uid in team_members_map:
            proxies.add(team_members_map[uid])
    
    if not proxies:
        print(f"    ⚠️  无匹配团队成员，跳过")
        sync_results.append({"name": project_name, "status": "skipped", "reason": "无匹配团队成员"})
        continue
    
    proxies_str = ", ".join(sorted(proxies))
    print(f"    ✓ 团队成员: {proxies_str}")
    
    # 字段映射示例
    print(f"    ✓ 字段映射:")
    mapped_data = {}
    for pms_key, puma_label in field_mapping.items():
        val = pms_item.get(pms_key, "")
        if val:
            mapped_data[puma_label] = val
            print(f"      {puma_label}: {val}")
    
    # 标签
    status = pms_item.get("Status", "")
    print(f"    ✓ 标签: [{status}]")
    
    # 生成的工作流结构
    print(f"    ✓ 生成工作流: 任务树 + UUID任务详情")
    
    sync_results.append({"name": project_name, "status": "created", "proxies": proxies_str})

print("\n\nStep 4: 同步结果统计")
print("-" * 60)
created = sum(1 for r in sync_results if r["status"] == "created")
skipped = sum(1 for r in sync_results if r["status"] == "skipped")
print(f"  ✅ 成功创建: {created} 个项目")
print(f"  ⏭️  跳过: {skipped} 个项目")

print("\n  详细结果:")
for result in sync_results:
    icon = "✅" if result["status"] == "created" else "⏭️"
    print(f"    {icon} {result['name']}")
    if result["status"] == "created":
        print(f"       可编辑: {result['proxies']}")
    else:
        print(f"       原因: {result['reason']}")

print("\n\n" + "=" * 80)
print("📝 同步后生成的 PUMA Project 对象示例")
print("=" * 80)

# 展示同步后生成的项目结构
synced_project = {
    "id": 1,
    "username": "SYSTEM",
    "owner": "",  # PMS 创建的项目 owner 为空
    "department": "研发部",
    "projectName": "Bosch智能工厂项目",
    "comment": "",
    "tags": ["Running"],  # 从 PMS Status 自动同步
    "editors": [],
    "orderIndex": 0,
    "projectInfo": {
        "owner": {"label": "Owner", "value": ""},
        "proxies": {"label": "Proxies", "value": "张三, 李四"},  # 从 TeamMembers 计算
        "uuid": {"label": "uuid", "value": "auto-generated-uuid"},
        "projectInfo": [
            [{"label": "项目编号", "value": "PRJ-2024-001", "type": "text"},
             {"label": "客户名称", "value": "Bosch GmbH", "type": "text"}],
            [{"label": "开始日期", "value": "2024-01-15", "type": "date"},
             {"label": "预计完成", "value": "2024-06-30", "type": "date"}],
            [{"label": "预算(元)", "value": "500000", "type": "number"}]
        ]
    },
    "projectWorkFlow": {
        "taskTree": [
            {
                "id": "uuid-xxx-1",
                "taskName": "项目启动",
                "status": "In Progress",
                "children": [
                    {"id": "uuid-xxx-2", "taskName": "需求分析", "status": "In Progress", "children": []},
                    {"id": "uuid-xxx-3", "taskName": "方案设计", "status": "In Progress", "children": []}
                ]
            }
        ],
        "taskDetails": {
            "uuid-xxx-1": {"inputs": [], "outputs": [], "operation": {}, "description": ""},
            "uuid-xxx-2": {"inputs": [], "outputs": [], "operation": {}, "description": ""}
        }
    }
}

print("\n生成的 Project 对象:")
print(json.dumps(synced_project, indent=2, ensure_ascii=False))

print("\n\n" + "=" * 80)
print("🔑 关键特性总结")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│  特性                    │ 说明                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. 增量同步             │ 仅新增，不覆盖已有项目 (防止数据丢失)              │
│  2. 字段可配置映射        │ 通过 DataMapping.json 灵活配置字段对应关系         │
│  3. 自动权限设置          │ 根据 PMS TeamMembers 自动设置 PUMA proxies        │
│  4. 状态标签同步          │ PMS Status → PUMA tags (Running/Quotation/SOP)   │
│  5. 工作流自动生成        │ 使用部门模板生成标准任务树                         │
│  6. 部门隔离             │ 同步时指定 department，不同部门使用不同模板        │
└─────────────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 80)
print("✅ PMS 模块演示完成！")
print("=" * 80)
print("""
使用流程:
  1. 调用 /pms/refresh 拉取外部数据
  2. 调用 /pms/preview 查看可同步项目
  3. 调用 /pms/sync?department=研发部 执行同步
""")
