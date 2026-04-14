"""
Todo V2 权限系统详解
====================
演示张三、李四、王五各自的权限
"""

print("=" * 60)
print("Todo V2 权限系统")
print("=" * 60)

print("""
场景：张三创建了一个待办事项
- 创建者 (creator): 张三
- 负责人 (assignees): 李四、王五

待办信息:
  标题: 完成项目文档
  创建者: 张三
  负责人: [李四, 王五]
""")

print("=" * 60)
print("权限检查规则")
print("=" * 60)

print("""
1. is_creator_or_assignee() 函数:
   
   def is_creator_or_assignee(todo, operator_id):
       if operator_id == todo.creator_id:      # 是创建者？
           return True                          # ✓ 有权限
       return operator_id in todo.assignee_ids  # 是负责人？

2. 各操作权限:
   
   ┌─────────────┬──────────┬──────────┬──────────┐
   │   操作      │   张三   │   李四   │   王五   │
   ├─────────────┼──────────┼──────────┼──────────┤
   │ 查看待办    │    ✓     │    ✓     │    ✓     │
   │ 修改标题    │    ✓     │    ✓     │    ✓     │
   │ 修改备注    │    ✓     │    ✓     │    ✓     │
   │ 更新进度    │    ✓     │    ✓     │    ✓     │
   │ 修改负责人  │    ✓     │    ✓     │    ✓     │
   │ 删除待办    │    ✓     │    ✗     │    ✗     │  ← 只有创建者能删除
   └─────────────┴──────────┴──────────┴──────────┘
""")

print("=" * 60)
print("具体权限分析")
print("=" * 60)

print("""
【张三 - 创建者】
  - is_creator_or_assignee() 检查:
    operator_id (张三) == creator_id (张三) ? 
    → True ✓
  
  - 结果: 拥有完全权限，包括删除

【李四 - 负责人】
  - is_creator_or_assignee() 检查:
    operator_id (李四) == creator_id (张三) ? 
    → False
    operator_id (李四) in assignee_ids ([李四, 王五]) ?
    → True ✓
  
  - 结果: 可以查看和更新，但不能删除

【王五 - 负责人】
  - is_creator_or_assignee() 检查:
    operator_id (王五) == creator_id (张三) ?
    → False
    operator_id (王五) in assignee_ids ([李四, 王五]) ?
    → True ✓
  
  - 结果: 可以查看和更新，但不能删除

【赵六 - 无关人员】
  - is_creator_or_assignee() 检查:
    operator_id (赵六) == creator_id (张三) ?
    → False
    operator_id (赵六) in assignee_ids ([李四, 王五]) ?
    → False
  
  - 结果: 没有任何权限
""")

print("=" * 60)
print("代码中的权限检查")
print("=" * 60)

print("""
# 1. 查看待办 (list_todos)
# 所有人（创建者或负责人）都能看到
if todo.creator_id == operator_id or operator_id in todo.assignee_ids:
    显示待办

# 2. 更新待办 (update_todo)
# 检查权限
if not is_creator_or_assignee(todo, operator_id):
    raise PermissionError("No permission")
# 通过检查后可以更新

# 3. 删除待办 (delete_todo)
# 特殊规则：只有创建者能删除
if operator_id != todo.creator_id:
    raise PermissionError("No permission - only creator can delete")
""")

print("=" * 60)
print("总结")
print("=" * 60)

print("""
✓ 张三（创建者）: 完全权限，可以删除
✓ 李四（负责人）: 可以查看和更新，不能删除
✓ 王五（负责人）: 可以查看和更新，不能删除
✗ 赵六（无关人员）: 没有任何权限

设计意图：
- 创建者拥有最高权限，可以管理整个待办
- 负责人可以协作完成任务，但不能删除
- 防止误删：只有创建者能删除，避免负责人误操作
""")
