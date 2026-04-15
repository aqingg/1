"""
api/events.py 简单示例
======================
演示 SSE (Server-Sent Events) 流式接口
"""


import json
import time
from datetime import datetime


# ========== 总结 ==========
print("\n" + "=" * 60)
print("总结")
print("=" * 60)
print("""
api/events.py 只有 1 个接口:

GET /events/stream?username=xxx
  功能: SSE 服务器推送事件流
  特点:
    - 长连接，实时推送
    - 自动心跳（每20秒）
    - 客户端断开自动清理
    - 使用 event_bus 管理订阅

工作流程:
  1. 客户端连接 → subscribe() 订阅事件
  2. 服务器推送 → 通过 queue 接收事件
  3. 格式转换 → yield "data: {json}\n\n"
  4. 客户端断开 → unsubscribe() 取消订阅

适用场景:
  - 实时通知
  - 进度推送
  - 系统广播
  - 在线状态更新
""")

print("=" * 60)
print("api/events.py - SSE 流式接口演示")
print("=" * 60)

# 模拟事件总线
class MockEventBus:
    """模拟事件总线"""
    def __init__(self):
        self.listeners = []
        self.event_history = []
    
    def subscribe(self):
        """订阅事件"""
        listener = {"id": len(self.listeners) + 1, "queue": []}
        self.listeners.append(listener)
        print(f"  [事件总线] 新订阅者加入，ID: {listener['id']}")
        return listener
    
    def unsubscribe(self, listener):
        """取消订阅"""
        if listener in self.listeners:
            self.listeners.remove(listener)
            print(f"  [事件总线] 订阅者 {listener['id']} 离开")
    
    def publish(self, event):
        """发布事件给所有订阅者"""
        self.event_history.append(event)
        for listener in self.listeners:
            listener["queue"].append(event)
        print(f"  [事件总线] 事件已发布: {event['event']}")

event_bus = MockEventBus()

# ========== 接口: SSE 流 ==========
print("\n【接口】GET /events/stream?username=xxx")
print("-" * 60)

def simulate_sse_stream(username, duration=5):
    """
    模拟 SSE 流式推送
    实际接口是异步的，这里用同步方式模拟
    """
    print(f"  用户 '{username}' 连接 SSE 流")
    
    # 1. 订阅事件
    listener = event_bus.subscribe()
    
    # 2. 模拟接收事件
    start_time = time.time()
    events_received = []
    
    print(f"  开始接收事件（模拟 {duration} 秒）...")
    
    while time.time() - start_time < duration:
        # 检查是否有新事件
        if listener["queue"]:
            event = listener["queue"].pop(0)
            events_received.append(event)
            
            # 模拟 SSE 格式输出
            sse_data = f"data: {json.dumps(event)}"
            print(f"    → 收到: {sse_data}")
        
        # 模拟心跳（每2秒）
        elapsed = time.time() - start_time
        if int(elapsed) % 2 == 0 and elapsed > 0:
            heartbeat = {"event": "heartbeat", "time": datetime.now().isoformat()}
            print(f"    → 心跳: data: {json.dumps(heartbeat)}")
        
        time.sleep(0.5)
    
    # 3. 取消订阅
    event_bus.unsubscribe(listener)
    print(f"  连接关闭，共接收 {len(events_received)} 个事件")
    
    return events_received

# ========== 演示场景 ==========
print("\n场景1: 用户张三连接 SSE 流")
print("-" * 40)

# 启动一个后台任务来发布事件
def simulate_background_events():
    """模拟后台产生事件"""
    time.sleep(1)
    event_bus.publish({"event": "project_updated", "project_id": 1, "message": "项目1已更新"})
    
    time.sleep(1.5)
    event_bus.publish({"event": "todo_created", "todo_id": 5, "title": "新待办"})
    
    time.sleep(1)
    event_bus.publish({"event": "progress_changed", "project_id": 1, "progress": 75})

# 在另一个线程中发布事件
import threading
thread = threading.Thread(target=simulate_background_events)
thread.start()

# 主线程接收事件
events = simulate_sse_stream("张三", duration=5)
thread.join()

print("\n场景2: 多个用户同时连接")
print("-" * 40)

# 重置事件总线
event_bus = MockEventBus()

def user_connect(username, delay=0):
    """模拟用户连接"""
    time.sleep(delay)
    listener = event_bus.subscribe()
    print(f"  [{username}] 已连接")
    
    # 接收3秒
    for i in range(3):
        if listener["queue"]:
            event = listener["queue"].pop(0)
            print(f"  [{username}] 收到: {event['event']}")
        time.sleep(1)
    
    event_bus.unsubscribe(listener)
    print(f"  [{username}] 已断开")

# 用户1连接
thread1 = threading.Thread(target=user_connect, args=("李四", 0))
thread1.start()

# 用户2稍后连接
thread2 = threading.Thread(target=user_connect, args=("王五", 1))
thread2.start()

# 发布事件
time.sleep(0.5)
event_bus.publish({"event": "system_notice", "message": "系统通知"})
time.sleep(1)
event_bus.publish({"event": "data_sync", "status": "completed"})

thread1.join()
thread2.join()
