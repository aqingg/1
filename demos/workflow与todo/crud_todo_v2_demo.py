"""
最小化示例：展示 crud/todo_v2.py 的执行流程
============================================
演示 Todo V2 各个接口如何一步一步执行
"""

import json
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List

# ========== 第1步：数据库配置 ==========
engine = create_engine("sqlite:///todo_v2_demo.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== 第2步：定义 Todo 模型（简化版） ==========
class Todo(Base):
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    due_date = Column(Date, nullable=False)
    comment = Column(Text, default="")
    tags = Column(JSON, default=list)
    link = Column(String(512), default="")
    progress = Column(JSON, default=dict)  # {user_id: progress_percentage}
    order_index = Column(Integer, default=0)
    assignee_ids = Column(JSON, nullable=False, default=list)
    creator_id = Column(String(64), nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "due_date": str(self.due_date),
            "progress": self.progress,
            "assignee_ids": self.assignee_ids,
            "creator_id": self.creator_id,
            "order_index": self.order_index
        }

# ========== 第3步：权限检查函数 ==========
def is_creator_or_assignee(todo: Todo, operator_id: str) -> bool:
    """检查用户是否有权限操作该待办"""
    if operator_id == todo.creator_id:
        return True
    
    # 处理 assignee_ids 可能是 JSON 字符串的情况
    assignees = todo.assignee_ids
    if isinstance(assignees, str):
        assignees = json.loads(assignees)
    
    return operator_id in (assignees or [])

# ========== 第4步：CRUD 函数 ==========

# 1. 查询待办列表
def list_todos(db: Session, operator_id: str) -> List[Todo]:
    """查询用户可见的所有待办（创建者或负责人）"""
    print(f"  [CRUD] list_todos() 被调用")
    print(f"  [CRUD] 查询用户 {operator_id} 的待办")
    
    # 简化版：查询 creator_id 匹配或 assignee_ids 包含 operator_id 的待办
    all_todos = db.query(Todo).all()
    result = []
    for todo in all_todos:
        # 处理 assignee_ids 可能是 JSON 字符串的情况
        assignees = todo.assignee_ids
        if isinstance(assignees, str):
            assignees = json.loads(assignees)
        
        if todo.creator_id == operator_id or operator_id in (assignees or []):
            result.append(todo)
    
    # 按 order_index 排序
    result.sort(key=lambda x: x.order_index)
    print(f"  [CRUD] 找到 {len(result)} 个待办")
    return result

# 2. 创建待办
class TodoCreateV2:
    """简化版的创建请求类"""
    def __init__(self, title, due_date, assignee_ids, operator_id, comment="", tags=None, link=""):
        self.title = title
        self.due_date = due_date
        self.assignee_ids = assignee_ids
        self.operator_id = operator_id
        self.comment = comment
        self.tags = tags or []
        self.link = link

def create_todo(db: Session, payload: TodoCreateV2) -> Todo:
    """创建新的待办事项"""
    print(f"  [CRUD] create_todo() 被调用")
    print(f"  [CRUD] 创建待办: {payload.title}")
    
    # 1️⃣ 所有已有 Todo 后移一位（新待办插到最前）
    print(f"  [CRUD] 将现有待办的 order_index + 1")
    existing_todos = db.query(Todo).all()
    for todo in existing_todos:
        todo.order_index += 1
    
    # 2️⃣ 初始化 per-user progress
    progress_map = {uid: 0 for uid in payload.assignee_ids}
    progress_map[payload.operator_id] = 0  # creator 也有进度
    print(f"  [CRUD] 初始化进度: {progress_map}")
    
    # 3️⃣ 创建新 Todo
    todo = Todo(
        title=payload.title,
        due_date=payload.due_date,
        comment=payload.comment,
        tags=payload.tags,
        link=payload.link or "",
        progress=progress_map,
        order_index=0,  # ⭐ 固定为第一个
        assignee_ids=payload.assignee_ids,
        creator_id=payload.operator_id,
    )
    
    db.add(todo)
    db.commit()
    db.refresh(todo)
    print(f"  [CRUD] 待办创建成功，ID: {todo.id}")
    return todo

# 3. 更新待办
class TodoUpdateV2:
    """简化版的更新请求类"""
    def __init__(self, id, operator_id, title=None, comment=None, progress=None, assignee_ids=None):
        self.id = id
        self.operator_id = operator_id
        self.title = title
        self.comment = comment
        self.progress = progress
        self.assignee_ids = assignee_ids

def update_todo(db: Session, payload: TodoUpdateV2) -> Todo:
    """更新待办事项"""
    print(f"  [CRUD] update_todo() 被调用")
    print(f"  [CRUD] 更新待办 ID: {payload.id}")
    
    # 查询待办
    todo = db.query(Todo).filter(Todo.id == payload.id).first()
    if not todo:
        raise ValueError("Todo not found")
    
    # 权限检查
    if not is_creator_or_assignee(todo, payload.operator_id):
        raise PermissionError("No permission")
    print(f"  [CRUD] 权限检查通过")
    
    # 更新基本字段
    if payload.title is not None:
        todo.title = payload.title
    if payload.comment is not None:
        todo.comment = payload.comment
    
    # 更新进度
    if payload.progress is not None:
        if not isinstance(todo.progress, dict):
            todo.progress = {}
        for user_id, value in payload.progress.items():
            todo.progress[user_id] = value
        print(f"  [CRUD] 更新进度: {todo.progress}")
    
    # 更新负责人列表
    if payload.assignee_ids is not None:
        old_assignees = set(todo.assignee_ids or [])
        new_assignees = set(payload.assignee_ids or [])
        
        todo.assignee_ids = list(new_assignees)
        
        # 新增 assignee → progress = 0
        for uid in new_assignees - old_assignees:
            if not isinstance(todo.progress, dict):
                todo.progress = {}
            todo.progress[uid] = 0
        
        # 移除 assignee → 删除 progress
        for uid in old_assignees - new_assignees:
            if isinstance(todo.progress, dict):
                todo.progress.pop(uid, None)
        
        print(f"  [CRUD] 更新负责人: {todo.assignee_ids}")
        print(f"  [CRUD] 同步进度: {todo.progress}")
    
    db.commit()
    db.refresh(todo)
    print(f"  [CRUD] 待办更新成功")
    return todo

# 4. 删除待办
def delete_todo(db: Session, todo_id: int, operator_id: str):
    """删除待办（仅创建者可删除）"""
    print(f"  [CRUD] delete_todo() 被调用")
    print(f"  [CRUD] 删除待办 ID: {todo_id}")
    
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        print(f"  [CRUD] 待办不存在")
        return None
    
    # V2: only creator can delete
    if operator_id != todo.creator_id:
        raise PermissionError("No permission - only creator can delete")
    
    db.delete(todo)
    db.commit()
    print(f"  [CRUD] 待办已删除")
    return todo

# ========== 第5步：演示执行流程 ==========
print("=" * 60)
print("Todo V2 CRUD 执行流程演示")
print("=" * 60)

# 创建表
print("\n【初始化】创建数据表...")
Base.metadata.create_all(bind=engine)
print("✓ 数据表创建成功")

db = SessionLocal()

# ========== 场景1：创建待办 ==========
print("\n" + "=" * 60)
print("场景1: 创建待办 (Create)")
print("=" * 60)

# 张三创建第一个待办
todo1 = create_todo(
    db,
    TodoCreateV2(
        title="完成项目文档",
        due_date=date(2024, 12, 31),
        assignee_ids=["李四", "王五"],
        operator_id="张三"
    )
)
print(f"✓ 待办1创建: {todo1.to_dict()}")

# 张三创建第二个待办（会自动排到后面）
todo2 = create_todo(
    db,
    TodoCreateV2(
        title="代码审查",
        due_date=date(2024, 11, 15),
        assignee_ids=["李四"],
        operator_id="张三"
    )
)
print(f"✓ 待办2创建: {todo2.to_dict()}")

# ========== 场景2：查询待办列表 ==========
print("\n" + "=" * 60)
print("场景2: 查询待办列表 (Read)")
print("=" * 60)

# 张三查看自己的待办
print("\n张三查看自己的待办:")
todos = list_todos(db, "张三")
for t in todos:
    print(f"   - [{t.order_index}] {t.title} (负责人: {t.assignee_ids})")

# 李四查看（作为负责人）
print("\n李四查看（作为负责人）:")
todos = list_todos(db, "李四")
for t in todos:
    print(f"   - {t.title}")

# 王五查看（作为负责人）
print("\n王五查看（作为负责人）:")
todos = list_todos(db, "王五")
for t in todos:
    print(f"   - {t.title}")

# 赵六查看（无权限）
print("\n赵六查看（无权限）:")
todos = list_todos(db, "赵六")
print(f"   找到 {len(todos)} 个待办")

# ========== 场景3：更新待办 ==========
print("\n" + "=" * 60)
print("场景3: 更新待办 (Update)")
print("=" * 60)

# 李四更新自己的进度
print("\n李四更新自己的进度:")
updated = update_todo(
    db,
    TodoUpdateV2(
        id=1,
        operator_id="李四",
        progress={"李四": 50}  # 完成50%
    )
)
print(f"✓ 更新后进度: {updated.progress}")

# 王五更新自己的进度
print("\n王五更新自己的进度:")
updated = update_todo(
    db,
    TodoUpdateV2(
        id=1,
        operator_id="王五",
        progress={"王五": 80}  # 完成80%
    )
)
print(f"✓ 更新后进度: {updated.progress}")

# 张三修改负责人（移除王五，添加赵六）
print("\n张三修改负责人（移除王五，添加赵六）:")
updated = update_todo(
    db,
    TodoUpdateV2(
        id=1,
        operator_id="张三",
        assignee_ids=["李四", "赵六"]  # 王五被移除，赵六被添加
    )
)
print(f"✓ 更新后负责人: {updated.assignee_ids}")
print(f"✓ 同步后进度: {updated.progress}")  # 赵六的进度应该是0

# ========== 场景4：删除待办 ==========
print("\n" + "=" * 60)
print("场景4: 删除待办 (Delete)")
print("=" * 60)

# 李四尝试删除（应该失败，不是创建者）
print("\n李四尝试删除待办2（应该失败）:")
try:
    delete_todo(db, todo_id=2, operator_id="李四")
except PermissionError as e:
    print(f"✗ 删除失败: {e}")

# 张三删除（应该成功）
print("\n张三删除待办2（应该成功）:")
deleted = delete_todo(db, todo_id=2, operator_id="张三")
print(f"✓ 已删除: {deleted.title if deleted else 'None'}")

# 验证删除
print("\n删除后张三的待办列表:")
todos = list_todos(db, "张三")
for t in todos:
    print(f"   - {t.title}")

# ========== 清理 ==========
db.close()
print("\n" + "=" * 60)
print("演示完成！")
print("=" * 60)
