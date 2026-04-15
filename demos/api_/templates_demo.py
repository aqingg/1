"""
最小化示例：展示 api/templates.py 的执行流程
============================================
演示模板接口如何一步一步执行
"""

import json



# ========== 总结 ==========
print("\n" + "=" * 60)
print("总结")
print("=" * 60)
print("""
templates.py 包含 4 个接口：

1. GET /template/getTaskDetail?taskName=xxx
   - 功能: 根据任务名获取任务详情
   - 数据源: TaskDetailJob.json

2. GET /template/getUnified
   - 功能: 获取部门和任务树模板
   - 数据源: unified.json

3. GET /template/teamMembers
   - 功能: 获取团队成员列表
   - 数据源: TeamMembers.json
   - 特点: 返回简化版(members)和完整版(raw)

4. GET /template/standardLinks
   - 功能: 获取系统快捷链接
   - 数据源: StandardLinks.json
   - 特点: 按标题排序

共同点:
- 都是 GET 请求
- 都从 JSON 文件读取数据
- 都不操作数据库
- 都使用 utils/file_loader 加载文件
""")

# 简单的 HTTPException 模拟
class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

# ========== 第1步：创建模拟数据文件 ==========
print("=" * 60)
print("步骤1: 创建模拟的 JSON 模板文件")
print("=" * 60)

# 模拟 TaskDetailJob.json
task_detail_data = [
    {
        "taskName": "需求分析",
        "description": "收集和分析用户需求",
        "estimatedDays": 5,
        "owner": "产品经理"
    },
    {
        "taskName": "系统设计",
        "description": "设计系统架构和数据库",
        "estimatedDays": 7,
        "owner": "架构师"
    },
    {
        "taskName": "编码开发",
        "description": "编写代码实现功能",
        "estimatedDays": 14,
        "owner": "开发工程师"
    }
]

# 模拟 unified.json
unified_data = {
    "departments": ["研发部", "产品部", "测试部"],
    "taskTreeTemplate": {
        "name": "项目阶段",
        "children": [
            {"name": "需求", "status": "Not Started"},
            {"name": "设计", "status": "Not Started"},
            {"name": "开发", "status": "Not Started"},
            {"name": "测试", "status": "Not Started"}
        ]
    }
}

# 模拟 TeamMembers.json
team_members_data = [
    {"name": "张三", "account": "zhangsan", "mail": "zhangsan@company.com"},
    {"name": "李四", "account": "lisi", "mail": "lisi@company.com"},
    {"name": "王五", "account": "wangwu", "mail": "wangwu@company.com"}
]

# 模拟 StandardLinks.json
standard_links_data = {
    "links": [
        {"title": "公司官网", "url": "https://www.company.com"},
        {"title": "内部Wiki", "url": "https://wiki.company.com"},
        {"title": "GitLab", "url": "https://gitlab.company.com"}
    ]
}

print("✓ TaskDetailJob.json: 包含 3 个任务模板")
print("✓ unified.json: 包含部门和任务树模板")
print("✓ TeamMembers.json: 包含 3 个团队成员")
print("✓ StandardLinks.json: 包含 3 个快捷链接")

# ========== 第2步：模拟 load_template 函数 ==========
print("\n" + "=" * 60)
print("步骤2: 模拟文件加载函数")
print("=" * 60)

def load_template(filename: str):
    """模拟从 templates 目录加载 JSON 文件"""
    print(f"  [加载] 读取模板文件: {filename}")
    
    if filename == "TaskDetailJob.json":
        return task_detail_data
    elif filename == "unified.json":
        return unified_data
    elif filename == "TeamMembers.json":
        return team_members_data
    else:
        raise FileNotFoundError(f"模板文件不存在: {filename}")

def load_data_source(filename: str):
    """模拟从 data_source 目录加载 JSON 文件"""
    print(f"  [加载] 读取数据源文件: {filename}")
    
    if filename == "StandardLinks.json":
        return standard_links_data
    else:
        raise FileNotFoundError(f"数据源文件不存在: {filename}")

print("✓ load_template() 函数已定义")
print("✓ load_data_source() 函数已定义")

# ========== 第3步：模拟 API 接口函数 ==========
print("\n" + "=" * 60)
print("步骤3: 模拟 API 接口函数")
print("=" * 60)

# 接口1: 获取任务详情
def get_task_detail(taskName: str):
    """
    从 templates/TaskDetailJob.json 查找指定任务详情
    对应: GET /template/getTaskDetail?taskName=xxx
    """
    print(f"\n  [API] get_task_detail() 被调用")
    print(f"  [API] 查询任务: {taskName}")
    
    data = load_template("TaskDetailJob.json")
    
    for item in data:
        if item.get("taskName") == taskName:
            print(f"  [API] ✓ 找到任务: {item}")
            return item
    
    print(f"  [API] ✗ 任务未找到")
    raise HTTPException(status_code=404, detail=f"Task '{taskName}' not found")

# 接口2: 获取 Unified 模板
def get_unified_template():
    """
    返回 unified.json（部门与任务树模板）
    对应: GET /template/getUnified
    """
    print(f"\n  [API] get_unified_template() 被调用")
    
    data = load_template("unified.json")
    print(f"  [API] ✓ 返回 unified 模板")
    return data

# 接口3: 获取 Team Members
def get_team_members():
    """
    返回 TeamMembers.json 中的成员信息
    对应: GET /template/teamMembers
    """
    print(f"\n  [API] get_team_members() 被调用")
    
    data = load_template("TeamMembers.json")
    names = [item.get("name") for item in data if "name" in item]
    
    result = {
        "success": True,
        "members": names,      # 只返回名字列表
        "raw": data            # 返回完整数据
    }
    print(f"  [API] ✓ 返回 {len(names)} 个成员")
    return result

# 接口4: 获取 Standard Links
def get_standard_links():
    """
    返回系统预置的快捷链接
    对应: GET /template/standardLinks
    """
    print(f"\n  [API] get_standard_links() 被调用")
    
    try:
        data = load_data_source("StandardLinks.json")
        links = data.get("links", [])
        
        # 按标题排序
        sorted_links = sorted(links, key=lambda l: l.get("title", "").lower())
        print(f"  [API] ✓ 返回 {len(sorted_links)} 个链接（已排序）")
        return sorted_links
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="StandardLinks.json not found")

print("✓ 4 个 API 接口函数已定义")

# ========== 第4步：演示接口调用 ==========
print("\n" + "=" * 60)
print("步骤4: 演示接口调用")
print("=" * 60)

# 演示1: 获取任务详情
print("\n【演示1】获取任务详情")
print("-" * 40)
print("请求: GET /template/getTaskDetail?taskName=需求分析")
result = get_task_detail("需求分析")
print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

# 演示2: 获取不存在的任务
print("\n【演示2】获取不存在的任务")
print("-" * 40)
print("请求: GET /template/getTaskDetail?taskName=不存在的任务")
try:
    result = get_task_detail("不存在的任务")
except HTTPException as e:
    print(f"响应: 404 - {e.detail}")

# 演示3: 获取 Unified 模板
print("\n【演示3】获取 Unified 模板")
print("-" * 40)
print("请求: GET /template/getUnified")
result = get_unified_template()
print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

# 演示4: 获取团队成员
print("\n【演示4】获取团队成员")
print("-" * 40)
print("请求: GET /template/teamMembers")
result = get_team_members()
print(f"响应:")
print(f"  members: {result['members']}")
print(f"  raw: {json.dumps(result['raw'], ensure_ascii=False)}")

# 演示5: 获取快捷链接
print("\n【演示5】获取快捷链接")
print("-" * 40)
print("请求: GET /template/standardLinks")
result = get_standard_links()
print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
