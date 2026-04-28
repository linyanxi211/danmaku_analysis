from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api import analysis,video, danmaku, report, model, history  # 导入分析模块
import sys
import os
from websocket import websocket_endpoint #导入websocket模块

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="B站弹幕情感分析API")

# CORS配置 - 现在就需要，否则前端无法访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://127.0.0.1:3000",
                   "http://localhost:8000",
                   "http://127.0.0.1:8000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 - 现在就需要
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(video.router, prefix="/api", tags=["video"])
app.include_router(danmaku.router, prefix="/api", tags=["danmaku"])
app.include_router(report.router, prefix="/api", tags=["report"])
app.include_router(model.router, prefix="/api", tags=["model"])
app.include_router(history.router, prefix="/api", tags=["history"])

@app.websocket("/ws/{bvid}")
async def websocket_route(websocket: WebSocket, bvid: str):
    await websocket_endpoint(websocket, bvid)

@app.get("/")
async def root():
    return {
        "message": "B站弹幕情感分析API",
        "version": "1.0.0",
        "status": "running",
        "websocket": "ws://localhost:8000/ws/{bvid}",
        "endpoints": [
            "/api/analyze - POST 开始分析",
            "/api/analyze/status/{task_id} - GET 查询状态",
            "/api/analyze/result/{task_id} - GET 获取结果",
            "/api/analyze/test - POST 测试连接",
            "/api/history - GET 获取历史记录",
            "/api/report/{bvid} - GET 获取分析报告"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/routes")
async def get_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else []
        })
    return routes

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


