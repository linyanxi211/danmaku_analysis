"""
WebSocket实时推送服务 - 真实弹幕版
"""
import asyncio
import json
import random
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import pandas as pd

# 导入数据库连接
from utils.database import db

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.danmaku_queues: Dict[str, asyncio.Queue] = {}  # 每个视频的弹幕队列
        self.tasks: Dict[str, asyncio.Task] = {}  # 每个视频的推送任务
    
    async def connect(self, websocket: WebSocket, bvid: str):
        await websocket.accept()
        if bvid not in self.active_connections:
            self.active_connections[bvid] = set()
            # 为每个视频创建弹幕队列和推送任务
            self.danmaku_queues[bvid] = asyncio.Queue()
            self.tasks[bvid] = asyncio.create_task(self.push_danmakus(bvid))
        
        self.active_connections[bvid].add(websocket)
        print(f"✅ WebSocket连接建立: {bvid}, 当前连接数: {len(self.active_connections[bvid])}")
    
    def disconnect(self, websocket: WebSocket, bvid: str):
        if bvid in self.active_connections:
            self.active_connections[bvid].discard(websocket)
            if not self.active_connections[bvid]:
                # 没有连接了，取消推送任务
                if bvid in self.tasks:
                    self.tasks[bvid].cancel()
                    del self.tasks[bvid]
                if bvid in self.danmaku_queues:
                    del self.danmaku_queues[bvid]
                del self.active_connections[bvid]
        print(f"❌ WebSocket断开: {bvid}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except:
            pass
    
    async def broadcast_to_video(self, bvid: str, message: dict):
        if bvid in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[bvid]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            for conn in disconnected:
                self.active_connections[bvid].discard(conn)
    
    async def push_danmakus(self, bvid: str):
        """从数据库加载弹幕并推送到前端"""
        try:
            # 从数据库获取该视频的所有弹幕，按时间排序
            sql = """
            SELECT id, bvid, time_point, content, sentiment_score, sentiment_tag
            FROM danmakus 
            WHERE bvid = %s 
            ORDER BY time_point
            """
            
            with db.get_cursor() as cursor:
                cursor.execute(sql, (bvid,))
                danmakus = cursor.fetchall()
            
            print(f"📊 加载到 {len(danmakus)} 条弹幕 for {bvid}")
            
            if not danmakus:
                # 如果没有弹幕，推送模拟数据
                await self.push_mock_danmakus(bvid)
                return
            
            # 按时间顺序推送弹幕
            for dm in danmakus:
                message = {
                    'type': 'new_danmaku',
                    'data': {
                        'id': dm['id'],
                        'bvid': dm['bvid'],
                        'time': float(dm['time_point']),
                        'text': dm['content'],
                        'sentiment_score': float(dm['sentiment_score']),
                        'sentiment_tag': dm['sentiment_tag'],
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
                # 广播给所有订阅该视频的客户端
                await self.broadcast_to_video(bvid, message)
                
                # 根据时间间隔等待（模拟实时播放）
                # 这里简单起见，每0.5秒发送一条
                await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
            print(f"🛑 推送任务被取消: {bvid}")
        except Exception as e:
            print(f"❌ 推送弹幕失败: {e}")
    
    async def push_mock_danmakus(self, bvid: str):
        """如果没有真实弹幕，推送模拟数据"""
        texts = ["哈哈哈", "绝了", "泪目", "支持", "牛逼", "再来一遍", "前方高能", "名场面", "打卡"]
        while True:
            try:
                sentiment_score = round(random.uniform(0, 1), 3)
                if sentiment_score >= 0.6:
                    tag = 'positive'
                elif sentiment_score >= 0.4:
                    tag = 'neutral'
                else:
                    tag = 'negative'
                
                message = {
                    'type': 'new_danmaku',
                    'data': {
                        'id': random.randint(10000, 99999),
                        'bvid': bvid,
                        'time': round(random.uniform(0, 600), 1),
                        'text': random.choice(texts),
                        'sentiment_score': sentiment_score,
                        'sentiment_tag': tag,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                await self.broadcast_to_video(bvid, message)
                await asyncio.sleep(3)
            except asyncio.CancelledError:
                break

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, bvid: str):
    await manager.connect(websocket, bvid)
    
    try:
        # 发送连接成功消息
        await manager.send_personal_message({
            'type': 'connected',
            'bvid': bvid,
            'message': 'WebSocket连接成功'
        }, websocket)
        
        # 保持连接，处理心跳
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get('type') == 'ping':
                    await manager.send_personal_message({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    }, websocket)
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"消息处理错误: {e}")
            
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, bvid)
    except Exception as e:
        print(f"WebSocket错误: {e}")
        manager.disconnect(websocket, bvid)