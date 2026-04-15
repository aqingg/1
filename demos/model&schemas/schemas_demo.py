"""
最小化示例：展示 schemas (Pydantic) 的执行流程
===============================================
这个例子演示数据验证和序列化的完整流程
"""

# ========== 第1步：导入 Pydantic ==========
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from datetime import date

# ========== 第2步：定义 Schema 类 ==========
class TodoCreate(BaseModel):
    """创建待办事项的验证模型"""
    title: str                    # 必填字段
    due_date: date               # 必填字段，必须是日期类型
    comment: Optional[str] = ""  # 可选，默认空字符串
    tags: List[str] = []         # 可选，默认空列表
    assignee_ids: List[str]      # 必填，负责人列表

class TodoOut(BaseModel):
    """输出待办事项的序列化模型"""
    id: int
    title: str
    due_date: date
    comment: str
    tags: List[str]
    assignee_ids: List[str]
    creator_id: str
    
    class Config:
        orm_mode = True  # 允许从 ORM 模型转换

# ========== 第3步：模拟前端传来的数据（正确格式） ==========
print("=" * 50)
print("场景1: 验证正确的数据")
print("=" * 50)

valid_data = {
    "title": "完成项目文档",
    "due_date": "2024-12-31",  # 字符串会自动转为 date
    "comment": "需要详细说明",
    "tags": ["重要", "文档"],
    "assignee_ids": ["user1", "user2"]
}

print(f"输入数据: {valid_data}")

# 创建 Schema 对象 - 自动验证
try:
    todo = TodoCreate(**valid_data)
    print(f"✓ 验证通过！")
    print(f"  标题: {todo.title}")
    print(f"  截止日期: {todo.due_date} (类型: {type(todo.due_date).__name__})")
    print(f"  标签: {todo.tags}")
    print(f"  负责人: {todo.assignee_ids}")
except ValidationError as e:
    print(f"✗ 验证失败: {e}")

# ========== 第4步：模拟前端传来的数据（错误格式） ==========
print("\n" + "=" * 50)
print("场景2: 验证错误的数据")
print("=" * 50)

invalid_data = {
    "title": "",  # 空字符串（可能不符合业务逻辑）
    "due_date": "不是日期",  # 错误的日期格式
    "assignee_ids": "user1"  # 应该是列表，不是字符串
}

print(f"输入数据: {invalid_data}")

try:
    todo = TodoCreate(**invalid_data)
    print(f"✓ 验证通过！")
except ValidationError as e:
    print(f"✗ 验证失败！")
    print(f"错误详情:\n{e}")

# ========== 第5步：数据转换（Schema → Dict） ==========
print("\n" + "=" * 50)
print("场景3: Schema 对象转换为字典（用于返回给前端）")
print("=" * 50)

todo_out = TodoOut(
    id=1,
    title="完成项目文档",
    due_date=date(2024, 12, 31),
    comment="需要详细说明",
    tags=["重要", "文档"],
    assignee_ids=["user1", "user2"],
    creator_id="admin"
)

# 转换为字典
todo_dict = todo_out.model_dump()  # Pydantic v2 用法
print(f"Schema 对象: {todo_out}")
print(f"↓ 转换为字典 ↓")
print(f"字典数据: {todo_dict}")
print(f"JSON 可序列化: {isinstance(todo_dict, dict)}")

# ========== 第6步：从字典创建 Schema（Dict → Schema） ==========
print("\n" + "=" * 50)
print("场景4: 从字典创建 Schema 对象")
print("=" * 50)

api_response = {
    "id": 2,
    "title": "代码审查",
    "due_date": date(2024, 11, 15),
    "comment": "",
    "tags": [],
    "assignee_ids": ["user3"],
    "creator_id": "manager"
}

print(f"API 返回数据: {api_response}")
todo_from_api = TodoOut(**api_response)
print(f"↓ 创建 Schema 对象 ↓")
print(f"对象属性: title={todo_from_api.title}, id={todo_from_api.id}")

# ========== 第7步：部分更新（模拟 PATCH 请求） ==========
print("\n" + "=" * 50)
print("场景5: 部分更新数据")
print("=" * 50)

class TodoUpdate(BaseModel):
    """更新待办事项 - 所有字段都是可选的"""
    title: Optional[str] = None
    comment: Optional[str] = None
    tags: Optional[List[str]] = None

# 只更新 comment
partial_data = {"comment": "更新后的说明"}
update = TodoUpdate(**partial_data)
print(f"部分更新数据: {partial_data}")
print(f"更新对象: title={update.title}, comment={update.comment}")

# 检查哪些字段被更新了
update_dict = update.model_dump(exclude_unset=True)  # 只包含显式设置的字段
print(f"实际要更新的字段: {update_dict}")

# ========== 第8步：字段类型自动转换 ==========
print("\n" + "=" * 50)
print("场景6: 自动类型转换")
print("=" * 50)

auto_convert = {
    "title": "测试项目",           # 字符串
    "due_date": "2024-06-15",      # 字符串自动转为 date
    "assignee_ids": ("user1", "user2")  # 元组自动转为列表
}

print(f"输入数据: {auto_convert}")
print(f"  title 输入类型: {type(auto_convert['title']).__name__}")
print(f"  due_date 输入类型: {type(auto_convert['due_date']).__name__}")
print(f"  assignee_ids 输入类型: {type(auto_convert['assignee_ids']).__name__}")
print("↓ 自动转换后 ↓")

todo = TodoCreate(**auto_convert)
print(f"✓ 转换成功！")
print(f"  title: {todo.title} (类型: {type(todo.title).__name__})")
print(f"  due_date: {todo.due_date} (类型: {type(todo.due_date).__name__})")
print(f"  assignee_ids: {todo.assignee_ids} (类型: {type(todo.assignee_ids).__name__})")

# ========== 第9步：展示验证错误（类型不匹配） ==========
print("\n" + "=" * 50)
print("场景7: 类型不匹配的错误")
print("=" * 50)

type_mismatch = {
    "title": 123,  # 整数，但要求是字符串
    "due_date": "2024-06-15",
    "assignee_ids": ["user1"]
}

print(f"输入数据: {type_mismatch}")
print(f"  title 输入类型: {type(type_mismatch['title']).__name__} (要求是 str)")

try:
    todo = TodoCreate(**type_mismatch)
except ValidationError as e:
    print(f"✗ 验证失败！")
    print(f"错误: title 字段应该是字符串，但传了整数")

print("\n" + "=" * 50)
print("演示完成！")
print("=" * 50)
