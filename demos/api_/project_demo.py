"""
api/project.py 最简单示例
==========================
演示项目接口的基本使用
"""

import json
from datetime import datetime

print("=" * 60)
print("api/project.py - 项目接口演示")
print("=" * 60)

# 模拟数据库
projects_db = []
next_id = 1

# ========== 接口1: 查询项目 ==========
print("\n【接口1】GET /project/getProject")
print("-" * 50)

def get_project(project_id, username):
    """查询单个项目"""
    print(f"  调用: get_project(project_id={project_id}, username='{username}')")
    
    # 查找项目
    project = None
    for p in projects_db:
        if p["id"] == project_id:
            project = p
            break
    
    if not project:
        print("  结果: 项目不存在")
        return {"exists": False}
    
    # 检查权限
    if username not in [project["owner"], project.get("proxies", "")]:
        print("  结果: 无权限访问")
        return {"exists": False, "reason": "no_permission"}
    
    print(f"  结果: 找到项目 '{project['name']}'")
    return {"exists": True, "data": project}

# ========== 接口2: 创建项目 ==========
print("\n【接口2】POST /project/createProject")
print("-" * 50)

def create_project(username, project_name, department):
    """创建新项目"""
    global next_id
    print(f"  调用: create_project(username='{username}', name='{project_name}')")
    
    # 检查是否已存在
    for p in projects_db:
        if p["name"] == project_name:
            print("  结果: 项目已存在")
            return {"error": "Project already exists"}
    
    # 创建项目
    project = {
        "id": next_id,
        "name": project_name,
        "owner": username,
        "department": department,
        "status": "created",
        "created_at": datetime.now().isoformat()
    }
    projects_db.append(project)
    next_id += 1
    
    print(f"  结果: 项目创建成功，ID={project['id']}")
    return {"message": "Project created", "data": project}

# ========== 接口3: 更新项目 ==========
print("\n【接口3】POST /project/updateProjectInfo")
print("-" * 50)

def update_project(project_id, username, new_info):
    """更新项目信息"""
    print(f"  调用: update_project(project_id={project_id}, username='{username}')")
    
    # 查找项目
    project = None
    for p in projects_db:
        if p["id"] == project_id:
            project = p
            break
    
    if not project:
        print("  结果: 项目不存在")
        return {"error": "Project not found"}
    
    # 检查权限
    if username != project["owner"]:
        print("  结果: 无权限编辑")
        return {"error": "No permission"}
    
    # 更新信息
    project.update(new_info)
    print(f"  结果: 项目已更新")
    return {"message": "Project updated", "data": project}

# ========== 接口4: 删除项目 ==========
print("\n【接口4】POST /project/deleteProject")
print("-" * 50)

def delete_project(project_id, username):
    """删除项目"""
    print(f"  调用: delete_project(project_id={project_id}, username='{username}')")
    
    global projects_db
    
    # 查找并删除
    for i, p in enumerate(projects_db):
        if p["id"] == project_id:
            if p["owner"] != username:
                print("  结果: 无权限删除")
                return {"error": "No permission"}
            
            deleted = projects_db.pop(i)
            print(f"  结果: 项目 '{deleted['name']}' 已删除")
            return {"message": "Project deleted"}
    
    print("  结果: 项目不存在")
    return {"error": "Project not found"}

# ========== 接口5: 列出项目 ==========
print("\n【接口5】GET /project/listProjects")
print("-" * 50)

def list_projects(username):
    """列出用户可见的项目"""
    print(f"  调用: list_projects(username='{username}')")
    
    # 过滤用户有权限的项目
    visible = []
    for p in projects_db:
        if username in [p["owner"], p.get("proxies", "")]:
            visible.append(p)
    
    print(f"  结果: 找到 {len(visible)} 个项目")
    return {"projects": visible}

# ========== 演示场景 ==========
print("\n" + "=" * 60)
print("演示场景: 项目生命周期")
print("=" * 60)

# 1. 创建项目
print("\n1. 张三创建项目")
result = create_project("张三", "项目A", "研发部")
print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

print("\n2. 张三再创建一个项目")
result = create_project("张三", "项目B", "产品部")
print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

# 2. 列出项目
print("\n3. 张三查看自己的项目")
result = list_projects("张三")
print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

# 3. 查询项目
print("\n4. 张三查询项目1")
result = get_project(1, "张三")
print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

# 4. 更新项目
print("\n5. 张三更新项目1")
result = update_project(1, "张三", {"status": "in_progress", "progress": 50})
print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

# 5. 李四尝试访问（无权限）
print("\n6. 李四尝试访问项目1（无权限）")
result = get_project(1, "李四")
print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

# 6. 删除项目
print("\n7. 张三删除项目2")
result = delete_project(2, "张三")
print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

# 7. 再次列出
print("\n8. 张三再次查看项目列表")
result = list_projects("张三")
print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

# ========== 总结 ==========
print("\n" + "=" * 60)
print("总结")
print("=" * 60)
print("""
api/project.py 核心接口:

1. getProject      - 查询项目详情
2. createProject   - 创建新项目
3. updateProjectInfo - 更新项目信息
4. deleteProject   - 删除项目
5. listProjects    - 列出所有项目

权限控制:
  - owner: 项目创建者，有所有权限
  - proxies: 代理，有编辑权限
  - 其他用户: 无权限

实际功能还包括:
  - 工作流管理 (updateWorkFlow)
  - 项目排序 (reorderProjects)
  - 路径获取 (getPath)
  - SSE 实时推送
""")
