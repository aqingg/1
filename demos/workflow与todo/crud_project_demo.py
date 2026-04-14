"""
最小化示例：展示 crud/project.py 的执行流程
============================================
演示 CRUD 各个函数如何一步一步执行
"""

import json
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List

# ========== 第1步：数据库配置（同 models/database.py） ==========
engine = create_engine("sqlite:///crud_demo.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== 第2步：定义 Project 模型（同 models/project.py） ==========
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    owner = Column(String)
    editors = Column(Text)
    department = Column(String)
    projectName = Column(String)
    projectInfo = Column(Text)
    projectWorkFlow = Column(Text)
    comment = Column(Text)
    tags = Column(Text)
    orderIndex = Column(Integer, default=0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "owner": self.owner,
            "projectName": self.projectName,
            "department": self.department,
        }

# ========== 第3步：CRUD 函数（同 crud/project.py） ==========

# 1. 查询项目（按 projectId）
def get_project(db: Session, username: str, projectId: int):
    print(f"  [CRUD] get_project() 被调用")
    print(f"  [CRUD] 查询条件: username={username}, projectId={projectId}")
    result = (
        db.query(Project)
        .filter(Project.username == username, Project.id == projectId)
        .first()
    )
    print(f"  [CRUD] 查询结果: {result.projectName if result else 'None'}")
    return result

# 2. 按项目名查重
def project_exists_by_name(db: Session, username: str, projectName: str):
    print(f"  [CRUD] project_exists_by_name() 被调用")
    result = db.query(Project).filter(
        Project.username == username,
        Project.projectName == projectName
    ).first()
    print(f"  [CRUD] 项目是否存在: {result is not None}")
    return result

# 3. 创建项目
def create_project(db: Session, username, department, projectName, 
                   projectInfo, workFlow, owner, editors, comment="", tags=None):
    print(f"  [CRUD] create_project() 被调用")
    print(f"  [CRUD] 准备创建项目: {projectName}")
    
    db_project = Project(
        username=username,
        owner=owner,
        editors=json.dumps(editors or []),
        department=department,
        projectName=projectName,
        projectInfo=json.dumps(projectInfo),
        projectWorkFlow=json.dumps(workFlow),
        comment=comment,
        tags=json.dumps(tags) if tags else None,
    )
    print(f"  [CRUD] 创建模型对象: {db_project}")
    
    db.add(db_project)
    print(f"  [CRUD] db.add() - 添加到会话")
    
    db.commit()
    print(f"  [CRUD] db.commit() - 提交到数据库")
    
    db.refresh(db_project)
    print(f"  [CRUD] db.refresh() - 刷新获取ID: {db_project.id}")
    
    return db_project

# 4. 更新项目信息
def update_project_info(db: Session, project: Project, projectInfo: dict):
    print(f"  [CRUD] update_project_info() 被调用")
    print(f"  [CRUD] 原信息: {project.projectInfo}")
    
    project.projectInfo = json.dumps(projectInfo)
    print(f"  [CRUD] 新信息: {project.projectInfo}")
    
    db.commit()
    print(f"  [CRUD] db.commit() - 保存更改")
    
    db.refresh(project)
    return project

# 5. 列出项目
def list_projects(db: Session, username: str):
    print(f"  [CRUD] list_projects() 被调用")
    print(f"  [CRUD] 查询用户 {username} 的所有项目")
    
    result = (
        db.query(Project)
        .filter(Project.username == username)
        .order_by(Project.orderIndex.asc())
        .all()
    )
    print(f"  [CRUD] 找到 {len(result)} 个项目")
    return result

# 6. 删除项目
def delete_project(db: Session, project_id: int):
    print(f"  [CRUD] delete_project() 被调用")
    print(f"  [CRUD] 准备删除项目ID: {project_id}")
    
    proj = db.query(Project).filter(Project.id == project_id).first()
    if proj:
        db.delete(proj)
        print(f"  [CRUD] db.delete() - 标记删除")
        db.commit()
        print(f"  [CRUD] db.commit() - 确认删除")
    else:
        print(f"  [CRUD] 项目不存在")
    return proj

# 7. 重排项目
def reorder_projects(db: Session, ids: List[int]):
    print(f"  [CRUD] reorder_projects() 被调用")
    print(f"  [CRUD] 新顺序: {ids}")
    
    for idx, pid in enumerate(ids):
        db.query(Project).filter(Project.id == pid).update({
            "orderIndex": idx
        })
        print(f"  [CRUD] 项目 {pid} 的 orderIndex 设为 {idx}")
    
    db.commit()
    print(f"  [CRUD] db.commit() - 保存排序")

# ========== 第4步：演示执行流程 ==========
print("=" * 60)
print("CRUD 执行流程演示")
print("=" * 60)

# 创建表
print("\n【初始化】创建数据表...")
Base.metadata.create_all(bind=engine)
print("✓ 数据表创建成功")

# 创建会话
db = SessionLocal()

# ========== 场景1：创建项目 ==========
print("\n" + "=" * 60)
print("场景1: 创建项目 (Create)")
print("=" * 60)

project1 = create_project(
    db=db,
    username="张三",
    department="研发部",
    projectName="项目A",
    projectInfo={"description": "这是项目A"},
    workFlow={"tasks": []},
    owner="张三",
    editors=["李四"],
    comment="测试项目",
    tags=["重要"]
)
print(f"✓ 项目创建成功: {project1.to_dict()}")

# 再创建几个项目
project2 = create_project(db, "张三", "研发部", "项目B", {"desc": "B"}, {}, "张三", [], "", [])
project3 = create_project(db, "张三", "研发部", "项目C", {"desc": "C"}, {}, "张三", [], "", [])

# ========== 场景2：查询项目 ==========
print("\n" + "=" * 60)
print("场景2: 查询项目 (Read)")
print("=" * 60)

found_project = get_project(db, username="张三", projectId=1)
print(f"✓ 查询结果: {found_project.to_dict() if found_project else '未找到'}")

# ========== 场景3：检查项目名是否存在 ==========
print("\n" + "=" * 60)
print("场景3: 检查项目名是否存在")
print("=" * 60)

exists = project_exists_by_name(db, "张三", "项目A")
print(f"✓ '项目A' 是否存在: {exists is not None}")

exists2 = project_exists_by_name(db, "张三", "不存在的项目")
print(f"✓ '不存在的项目' 是否存在: {exists2 is not None}")

# ========== 场景4：更新项目信息 ==========
print("\n" + "=" * 60)
print("场景4: 更新项目信息 (Update)")
print("=" * 60)

updated = update_project_info(
    db, 
    project=project1, 
    projectInfo={"description": "这是项目A（已更新）", "status": "进行中"}
)
print(f"✓ 项目信息已更新")

# ========== 场景5：列出所有项目 ==========
print("\n" + "=" * 60)
print("场景5: 列出所有项目 (Read List)")
print("=" * 60)

projects = list_projects(db, "张三")
print(f"✓ 项目列表:")
for p in projects:
    print(f"   - ID={p.id}, 名称={p.projectName}, orderIndex={p.orderIndex}")

# ========== 场景6：重新排序 ==========
print("\n" + "=" * 60)
print("场景6: 重新排序项目 (Reorder)")
print("=" * 60)

# 将顺序改为 [项目C, 项目A, 项目B]
reorder_projects(db, [3, 1, 2])

# 再次列出查看顺序
projects = list_projects(db, "张三")
print(f"✓ 重新排序后:")
for p in projects:
    print(f"   - ID={p.id}, 名称={p.projectName}, orderIndex={p.orderIndex}")

# ========== 场景7：删除项目 ==========
print("\n" + "=" * 60)
print("场景7: 删除项目 (Delete)")
print("=" * 60)

deleted = delete_project(db, project_id=2)
print(f"✓ 项目 '{deleted.projectName if deleted else '未知'}' 已删除")

# 验证删除
projects = list_projects(db, "张三")
print(f"✓ 剩余项目数量: {len(projects)}")

# ========== 清理 ==========
db.close()
print("\n" + "=" * 60)
print("演示完成！")
print("=" * 60)
