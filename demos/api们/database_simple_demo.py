"""
api/database.py 简单演示
========================
说明：这个文件是数据库管理接口，与 models 的关系见底部说明
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

# ========== 模拟环境 ==========
BASE_DIR = Path("demo_db")
DB_FILE = BASE_DIR / "app.db"
BACKUP_DIR = BASE_DIR / "backups"

BASE_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)
DB_FILE.write_text("SQLite database content", encoding="utf-8")

print("=" * 60)
print("api/database.py - 4个接口演示")
print("=" * 60)

# ========== 接口1: 备份数据库 ==========
print("\n【接口1】POST /database/snapshot - 备份数据库")
print("-" * 60)

def backup_database(mode="manual"):
    """备份数据库文件"""
    # 1. 生成带时间戳的文件名
    time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{mode}_{time_str}.db"
    backup_path = BACKUP_DIR / backup_name
    
    # 2. 复制文件
    shutil.copy2(DB_FILE, backup_path)
    
    # 3. 返回结果
    return {
        "success": True,
        "backup_file": backup_name,
        "message": f"数据库已备份到 {backup_name}"
    }

# 执行备份
result = backup_database("manual")
print(f"调用 backup_database('manual')")
print(f"返回: {json.dumps(result, indent=2, ensure_ascii=False)}")

# ========== 接口2: 列出JSON文件 ==========
print("\n【接口2】GET /database/editable_files - 列出所有JSON文件")
print("-" * 60)

# 创建几个示例文件
(BASE_DIR / "config.json").write_text('{}', encoding="utf-8")
(BASE_DIR / "data").mkdir(exist_ok=True)
(BASE_DIR / "data" / "users.json").write_text('[]', encoding="utf-8")

def list_json_files():
    """扫描目录下的所有JSON文件"""
    files = list(BASE_DIR.rglob("*.json"))
    return [str(f.relative_to(BASE_DIR)) for f in files]

files = list_json_files()
print(f"调用 list_json_files()")
print(f"返回: {files}")

# ========== 接口3: 更新JSON文件 ==========
print("\n【接口3】PUT /database/update - 更新JSON文件")
print("-" * 60)

def update_json_file(filename, new_content):
    """更新JSON文件内容"""
    # 安全检查：防止 ../ 攻击
    if ".." in filename:
        return {"error": "非法路径"}
    
    # 检查文件是否存在
    target = BASE_DIR / filename
    if not target.exists():
        return {"error": "文件不存在"}
    
    # 验证JSON格式
    try:
        json.loads(new_content)
    except:
        return {"error": "无效的JSON"}
    
    # 写入文件
    target.write_text(new_content, encoding="utf-8")
    return {"success": True, "message": f"{filename} 已更新"}

# 更新文件
new_data = json.dumps({"version": "2.0", "updated": True})
result = update_json_file("config.json", new_data)
print(f"调用 update_json_file('config.json', '{new_data}')")
print(f"返回: {json.dumps(result, indent=2, ensure_ascii=False)}")

# ========== 接口4: 创建JSON文件 ==========
print("\n【接口4】POST /database/create - 创建新JSON文件")
print("-" * 60)

def create_json_file(filepath, content):
    """创建新的JSON文件"""
    # 检查扩展名
    if not filepath.endswith('.json'):
        return {"error": "必须以.json结尾"}
    
    # 检查是否已存在
    target = BASE_DIR / filepath
    if target.exists():
        return {"error": "文件已存在"}
    
    # 创建目录
    target.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    target.write_text(content, encoding="utf-8")
    return {"success": True, "message": f"{filepath} 已创建"}

# 创建新文件
result = create_json_file("settings/theme.json", '{"theme": "dark"}')
print(f"调用 create_json_file('settings/theme.json', '{{\"theme\": \"dark\"}}')")
print(f"返回: {json.dumps(result, indent=2, ensure_ascii=False)}")

# 尝试创建已存在的文件
result = create_json_file("config.json", '{}')
print(f"\n再次调用 create_json_file('config.json', ...)")
print(f"返回: {json.dumps(result, indent=2, ensure_ascii=False)}")

# ========== 与 models 的关系说明 ==========
print("\n" + "=" * 60)
print("api/database.py 与 models 的关系")
print("=" * 60)
print("""
【models 层】
  - 定义数据库表结构（SQLAlchemy 模型）
  - 例如：Project, Todo 等表
  - 操作：增删改查数据库记录

【api/database.py】
  - 管理数据库文件本身（不是表记录）
  - 操作：
    1. 备份整个 .db 文件
    2. 管理 JSON 配置文件
  - 不操作 SQLAlchemy 模型

【关系图】

  客户端
    │
    ▼
  ┌─────────────────┐
  │ api/database.py │  ← 管理文件（备份、JSON配置）
  │  - 备份.db文件   │
  │  - 读写JSON文件  │
  └─────────────────┘
         │
         ▼
  文件系统 (.db文件, .json文件)

  客户端
    │
    ▼
  ┌─────────────────┐
  │ api/project.py  │  ← 管理业务数据
  │ api/todo_v2.py  │
  └─────────────────┘
         │
         ▼
  ┌─────────────────┐
  │  crud/project.py│  ← 数据库操作
  │  crud/todo_v2.py│
  └─────────────────┘
         │
         ▼
  ┌─────────────────┐
  │ models/project.py│ ← 表结构定义
  │ models/todo.py   │
  └─────────────────┘
         │
         ▼
     SQLite数据库

【总结】
- models 层：操作数据库表中的数据记录
- api/database.py：操作数据库文件本身和JSON配置文件
- 两者互补，但职责不同
""")

# 清理
import shutil
if BASE_DIR.exists():
    shutil.rmtree(BASE_DIR)
print("\n[完成] 演示结束")
