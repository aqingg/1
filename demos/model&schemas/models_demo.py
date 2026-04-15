"""
最小化示例：展示 models 的执行流程
=====================================
这个例子演示了从数据库创建到数据操作的完整流程
"""

# ========== 第1步：导入必要的库 ==========
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

# ========== 第2步：创建数据库引擎 ==========
# 使用 SQLite 内存数据库（实际项目会用文件数据库）
engine = create_engine(
    "sqlite:///demo.db",  # 数据库文件
    connect_args={"check_same_thread": False}
)

# ========== 第3步：创建会话工厂和基类 ==========
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== 第4步：定义数据模型 ==========
class Project(Base):
    """项目模型 - 对应数据库中的 projects 表"""
    __tablename__ = "projects"
    
    # 定义字段
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    owner = Column(String)
    project_info = Column(Text)  # 存储 JSON 字符串
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            "id": self.id,
            "project_name": self.project_name,
            "owner": self.owner,
            "project_info": json.loads(self.project_info) if self.project_info else {}
        }

# ========== 第5步：创建数据表 ==========
print("步骤1: 创建数据表...")
Base.metadata.create_all(bind=engine)
print("✓ 数据表创建成功！\n")

# ========== 第6步：创建数据库会话 ==========
print("步骤2: 创建数据库会话...")
db = SessionLocal()
print("✓ 会话创建成功！\n")

# ========== 第7步：添加数据（Create） ==========
print("步骤3: 添加新项目...")
new_project = Project(
    project_name="测试项目",
    owner="张三",
    project_info=json.dumps({
        "description": "这是一个测试项目",
        "start_date": "2024-01-01"
    })
)
db.add(new_project)  # 添加到会话
db.commit()          # 提交到数据库
print(f"✓ 项目创建成功，ID: {new_project.id}\n")

# ========== 第8步：查询数据（Read） ==========
print("步骤4: 查询项目...")
project = db.query(Project).filter(Project.project_name == "测试项目").first()
print(f"✓ 查询结果: {project.to_dict()}\n")

# ========== 第9步：更新数据（Update） ==========
print("步骤5: 更新项目...")
project.owner = "李四"
db.commit()
print(f"✓ 更新后: {project.to_dict()}\n")

# ========== 第10步：删除数据（Delete） ==========
print("步骤6: 删除项目...")
db.delete(project)
db.commit()
print("✓ 项目已删除\n")

# ========== 第11步：验证删除 ==========
print("步骤7: 验证删除...")
projects = db.query(Project).all()
print(f"✓ 剩余项目数量: {len(projects)}\n")

# ========== 第12步：关闭会话 ==========
db.close()
print("步骤8: 会话已关闭")
print("\n演示完成！")
