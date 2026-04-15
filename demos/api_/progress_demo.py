"""
progress.py 最简单示例
======================
演示两个接口函数如何运行
"""

# ========== 接口1: 获取项目进度 ==========
print("=" * 50)
print("接口1: GET /progress/{project_id}")
print("=" * 50)

def get_progress(project_id: int):
    """
    获取指定项目的进度
    输入: project_id (项目ID)
    输出: 各部门的进度信息
    """
    print(f"  调用: get_progress(project_id={project_id})")
    
    result = {
        "project_id": project_id,
        "progress": [
            {"department": "R&D", "progress": 70},
            {"department": "Purchase", "progress": 40}
        ]
    }
    
    print(f"  返回: {result}")
    return result

# 调用示例
print("\n示例1: 查询项目1的进度")
result1 = get_progress(1)

print("\n示例2: 查询项目2的进度")
result2 = get_progress(2)

# ========== 接口2: 更新进度 ==========
print("\n" + "=" * 50)
print("接口2: POST /progress/update")
print("=" * 50)

def update_progress(progress_data: dict):
    """
    更新进度信息
    输入: progress_data (进度数据字典)
    输出: 更新结果
    """
    print(f"  调用: update_progress({progress_data})")
    
    result = {
        "message": "Progress updated (dummy)",
        "received": progress_data
    }
    
    print(f"  返回: {result}")
    return result

# 调用示例
print("\n示例1: 更新项目1的进度")
update_data1 = {
    "project_id": 1,
    "department": "R&D",
    "progress": 75
}
result3 = update_progress(update_data1)

print("\n示例2: 更新项目2的进度")
update_data2 = {
    "project_id": 2,
    "department": "Purchase",
    "progress": 50
}
result4 = update_progress(update_data2)

# ========== 总结 ==========
print("\n" + "=" * 50)
print("总结")
print("=" * 50)
print("""
progress.py 只有两个接口:

1. GET /progress/{project_id}
   功能: 查询项目进度
   输入: 项目ID (数字)
   输出: 各部门进度列表

2. POST /progress/update
   功能: 更新进度
   输入: JSON数据 {"project_id": 1, "department": "R&D", "progress": 75}
   输出: 更新结果确认

特点:
- 代码最简单，只有25行
- 目前返回的是假数据(dummy)
- 没有连接真实数据库
""")
