<h1 align="center">B站视频弹幕情感分析与可视化系统</h1>
<p align="center"><strong>基于 Vue3 + FastAPI 构建的 B 站弹幕情感可视化分析系统。系统集成传统基线模型与深度学习模型（BERT），提供多维数据联动、双模型对比分析及流式数据导出功能。</strong></p>


>   [!WARNING]
>
>   ***本项目仅用于学习使用！！！***
>
>   ***本项目仅用于学习使用！！！***
>
>   ***本项目仅用于学习使用！！！***

## 核心亮点
- 双模型对比验证：针对传统算法在反讽语境下的痛点，设计了“极性对齐映射函数”与“时空切片采样”机制，在同一坐标系内实现 SnowNLP 与 BERT 的直观对比，从“看结论”升级为“看证据”。
- 性能瓶颈突破：针对大模型在 CPU 下的阻塞问题，采用分层随机采样策略，结合 Pipeline 批量推理，将全量对比耗时压缩至秒级。
- 后端流式导出架构：彻底摒弃前端生成文件导致的 OOM 崩溃，重构为 Python fpdf2 + pandas 动态生成，通过 HTTP 流式响应实现无损下载。
- 全链路状态管理：基于 Vue3 组合式 API 与 PinIA，实现跨组件 WebSocket 通信与页面刷新时的状态恢复。

## 二、技术栈
- 前端：Vue3 + Vite + Element Plus + ECharts + ECharts-Wordcloud
- 后端：FastAPI + Uvicorn + PyMySQL + Transformers (HuggingFace)
- 算法模型：SnowNLP (基线) / BERT (微调版)
- 数据导出：fpdf2 (PDF) / pandas (Excel)

## 三、快速开始
1. 环境要求
- Python 3.9+
- Node.js 16+
- MySQL 8.0+
2.后端启动
```bash
# 进入后端目录
cd backend
# 安装依赖
pip install -r requirements.txt
# 配置数据库（修改 utils/database.py 中的密码）并初始化表结构
# 启动服务
python app.py
```
3.前端启动
```bash
# 进入前端目录
cd frontend
# 安装依赖
npm install
# 启动开发服务器
npm run dev
```

## 四、核心模块
- 双模型对比算法流
  - 系统不采用全量计算，而是采用 10秒时间窗切片 + 随机抽样(15条) 策略。针对异构模型输出（连续值 vs 离散标签），设计了 1 - score 的极性对齐映射，实现了双曲线在同一坐标系的绝对量化对比。
- 数据导出策略
  - 完全抛弃前端生成文件的脆弱方案。后端利用内存流，pandas 负责数据整理，fpdf2 负责中文排版，通过 FastAPI 的 StreamingResponse 以 Blob 形式交付给前端触发浏览器原生下载，前端实现零计算负担的无损导出。

## 五、系统截图


License
本项目采用 MIT 许可证。
