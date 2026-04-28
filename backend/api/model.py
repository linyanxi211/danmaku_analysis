"""
模型管理API模块 - 处理模型列表、训练、对比等功能
"""
import os
import json
import time
import uuid
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 添加上级目录到路径

from utils.database import db

router = APIRouter()

# ==================== 请求/响应模型 ====================

class ModelInfo(BaseModel):
    """模型信息模型"""
    id: str
    name: str
    type: str  # 'snownlp', 'bert', 'custom'
    accuracy: float
    speed: int  # 条/秒
    size: str
    status: str  # 'active', 'training', 'inactive'
    created_at: str
    description: Optional[str] = None

class ModelListResponse(BaseModel):
    """模型列表响应"""
    total: int
    models: List[ModelInfo]

class TrainRequest(BaseModel):
    """训练请求模型"""
    name: str
    base_model: str = 'bert-base-chinese'
    dataset_bvid: Optional[str] = None  # 如果为空，使用所有数据
    epochs: int = 3
    batch_size: int = 16
    learning_rate: str = '2e-5'

class TrainResponse(BaseModel):
    """训练响应模型"""
    task_id: str
    model_name: str
    status: str
    message: str

class CompareRequest(BaseModel):
    """对比请求模型"""
    bvid: str
    models: List[str]  # 要对比的模型ID列表

class CompareResult(BaseModel):
    """对比结果模型"""
    model: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    inference_time: float
    confusion_matrix: List[List[int]]

class TestRequest(BaseModel):
    """测试请求模型"""
    model_id: str
    text: str

class TestResponse(BaseModel):
    """测试响应模型"""
    model_id: str
    text: str
    sentiment_score: float
    sentiment_tag: str
    confidence: float
    inference_time: float

# ==================== 模拟数据存储 ====================

# 模拟模型数据（实际应从数据库读取）
MOCK_MODELS = [
    {
        'id': 'snownlp-v1',
        'name': 'SnowNLP 基础版',
        'type': 'snownlp',
        'accuracy': 76.3,
        'speed': 2384,
        'size': '2.1MB',
        'status': 'active',
        'created_at': '2024-01-15',
        'description': '基于SnowNLP的快速情感分析模型，无需训练'
    },
    {
        'id': 'bert-base-v1',
        'name': 'BERT 基础版',
        'type': 'bert',
        'accuracy': 89.7,
        'speed': 124,
        'size': '438MB',
        'status': 'inactive',
        'created_at': '2024-02-20',
        'description': '基于BERT-base-chinese的预训练模型'
    },
    {
        'id': 'bert-finetuned-v1',
        'name': 'BERT 微调版',
        'type': 'bert',
        'accuracy': 94.2,
        'speed': 118,
        'size': '438MB',
        'status': 'active',
        'created_at': '2024-03-01',
        'description': '在10万条B站弹幕上微调的BERT模型'
    },
    {
        'id': 'bert-quantized-v1',
        'name': 'BERT 量化版',
        'type': 'bert',
        'accuracy': 93.1,
        'speed': 356,
        'size': '112MB',
        'status': 'inactive',
        'created_at': '2024-03-05',
        'description': 'INT8量化版本，速度提升3倍'
    }
]

# 训练任务存储
training_tasks = {}

# ==================== 辅助函数 ====================

def get_model_by_id(model_id: str) -> Optional[Dict]:
    """根据ID获取模型信息"""
    for model in MOCK_MODELS:
        if model['id'] == model_id:
            return model.copy()
    return None

def simulate_training(task_id: str, request: TrainRequest):
    """模拟训练过程（实际应调用BERT训练脚本）"""
    try:
        # 更新任务状态
        training_tasks[task_id]['status'] = 'training'
        training_tasks[task_id]['progress'] = 0
        
        # 模拟训练步骤
        stages = [
            (10, '正在加载数据集...'),
            (30, '正在预处理数据...'),
            (50, '正在训练模型...'),
            (70, '正在验证模型...'),
            (90, '正在保存模型...'),
            (100, '训练完成')
        ]
        
        for progress, message in stages:
            time.sleep(2)  # 模拟耗时
            training_tasks[task_id]['progress'] = progress
            training_tasks[task_id]['message'] = message
        
        # 训练完成，生成新模型
        new_model = {
            'id': f"bert-{int(time.time())}",
            'name': request.name,
            'type': 'bert',
            'accuracy': round(92 + (request.epochs * 0.5), 1),
            'speed': 120,
            'size': '438MB',
            'status': 'active',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': f'在{request.epochs}轮训练后的微调模型'
        }
        
        training_tasks[task_id]['status'] = 'completed'
        training_tasks[task_id]['result'] = new_model
        
    except Exception as e:
        training_tasks[task_id]['status'] = 'failed'
        training_tasks[task_id]['message'] = str(e)

# ==================== 真实BERT训练函数 ====================
def run_bert_training(task_id: str, request: TrainRequest):
    """真实的BERT训练任务"""
    try:
        # 更新任务状态
        training_tasks[task_id]['status'] = 'training'
        training_tasks[task_id]['progress'] = 5
        training_tasks[task_id]['message'] = '准备数据...'
        
        # 导入数据管理模块
        from utils.dataset import DatasetManager
        
        # 生成或加载数据集
        manager = DatasetManager(output_dir='./data')
        info = manager.get_dataset_info()
        
        if not info.get('exists'):
            training_tasks[task_id]['progress'] = 10
            training_tasks[task_id]['message'] = '从数据库导出数据...'
            
            dataset_path = manager.generate_training_dataset(name='bilibili_danmaku')
            if dataset_path is None:
                raise Exception('数据集生成失败，请先分析更多视频')
        else:
            dataset_path = info['filepath']
        
        training_tasks[task_id]['progress'] = 20
        training_tasks[task_id]['message'] = '加载数据集...'
        
        # 加载数据
        import pickle
        with open(dataset_path, 'rb') as f:
            data = pickle.load(f)
        
        train_texts = data['train']['texts']
        train_labels = data['train']['labels']
        val_texts = data['val']['texts']
        val_labels = data['val']['labels']
        
        if len(train_texts) < 100:
            raise Exception(f'训练数据不足 ({len(train_texts)} 条)，请先分析更多视频')
        
        training_tasks[task_id]['progress'] = 30
        training_tasks[task_id]['message'] = '初始化BERT模型...'
        
        # 导入BERT模型
        from models.bert_model import BertSentimentModel, BertConfig
        
        config = BertConfig()
        config.num_labels = 3
        config.epochs = request.epochs
        config.batch_size = request.batch_size
        config.learning_rate = float(request.learning_rate)
        config.max_length = 64
        
        model = BertSentimentModel(config)
        model._init_model()
        
        training_tasks[task_id]['progress'] = 40
        training_tasks[task_id]['message'] = f'开始训练 ({len(train_texts)} 条数据)...'
        
        # 训练模型
        history = model.train(
            train_texts=train_texts,
            train_labels=train_labels,
            val_texts=val_texts,
            val_labels=val_labels
        )
        
        training_tasks[task_id]['progress'] = 90
        training_tasks[task_id]['message'] = '评估模型...'
        
        # 评估模型
        metrics = model.evaluate(val_texts, val_labels)
        
        training_tasks[task_id]['progress'] = 95
        training_tasks[task_id]['message'] = '保存模型...'
        
        # 保存模型
        import os
        os.makedirs('./models', exist_ok=True)
        model.save_model(f'./models/{request.name}')
        
        training_tasks[task_id]['status'] = 'completed'
        training_tasks[task_id]['progress'] = 100
        training_tasks[task_id]['message'] = f'训练完成! 准确率: {metrics["accuracy"]*100:.1f}%'
        training_tasks[task_id]['result'] = {
            'name': request.name,
            'accuracy': round(metrics['accuracy'] * 100, 2),
            'precision': round(metrics['precision'] * 100, 2),
            'recall': round(metrics['recall'] * 100, 2),
            'f1': round(metrics['f1'] * 100, 2),
            'dataset_size': len(train_texts) + len(val_texts),
            'confusion_matrix': metrics['confusion_matrix']
        }
        
        print(f"训练完成! 准确率: {metrics['accuracy']*100:.1f}%")
        
    except Exception as e:
        training_tasks[task_id]['status'] = 'failed'
        training_tasks[task_id]['message'] = str(e)
        print(f"训练失败: {e}")


# ==================== API接口 ====================

@router.get("/models", response_model=ModelListResponse)
async def get_model_list(
    type: Optional[str] = None,
    status: Optional[str] = None
):
    """
    获取模型列表（支持筛选）
    """
    models = MOCK_MODELS.copy()
    
    # 筛选
    if type:
        models = [m for m in models if m['type'] == type]
    if status:
        models = [m for m in models if m['status'] == status]
    
    return ModelListResponse(
        total=len(models),
        models=[ModelInfo(**m) for m in models]
    )

@router.get("/models/{model_id}", response_model=ModelInfo)
async def get_model_detail(model_id: str):
    """
    获取模型详细信息
    """
    model = get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    return ModelInfo(**model)

@router.post("/models/train", response_model=TrainResponse)
async def train_model(request: TrainRequest, background_tasks: BackgroundTasks):
    """
    开始训练新模型
    """
    task_id = str(uuid.uuid4())
    
    # 初始化任务
    training_tasks[task_id] = {
        'task_id': task_id,
        'status': 'pending',
        'progress': 0,
        'message': '等待开始',
        'request': request.dict()
    }
    
    # 后台运行训练
    background_tasks.add_task(run_bert_training, task_id, request)
    
    return TrainResponse(
        task_id=task_id,
        model_name=request.name,
        status='pending',
        message='训练任务已提交'
    )

@router.get("/models/train/{task_id}")
async def get_training_status(task_id: str):
    """
    获取训练任务状态
    """
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = training_tasks[task_id]
    return {
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message'],
        'result': task.get('result')
    }

@router.post("/models/compare", response_model=List[CompareResult])
async def compare_models(request: CompareRequest):
    """
    对比多个模型在同一视频上的表现
    """
    # 获取视频的测试数据
    result = db.get_analysis_result(request.bvid)
    if not result:
        raise HTTPException(status_code=404, detail="视频分析结果不存在")
    
    # 模拟对比结果
    results = []
    for model_id in request.models:
        model = get_model_by_id(model_id)
        if not model:
            continue
        
        # 根据模型类型生成不同的指标
        base_acc = model['accuracy']
        results.append(CompareResult(
            model=model['name'],
            accuracy=base_acc,
            precision=base_acc - 0.5,
            recall=base_acc - 0.3,
            f1_score=base_acc - 0.4,
            inference_time=1000 / model['speed'],
            confusion_matrix=[
                [int(base_acc * 10), 8, 7],
                [6, int(base_acc * 8), 16],
                [4, 12, int(base_acc * 9)]
            ]
        ))
    
    return results

@router.post("/models/test", response_model=TestResponse)
async def test_model(request: TestRequest):
    """
    用单条文本测试模型效果
    """
    model = get_model_by_id(request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 模拟情感分析
    import random
    import time
    
    # 模拟推理时间
    start = time.time()
    time.sleep(0.01)  # 10ms
    
    # 根据模型类型生成不同的结果
    if model['type'] == 'snownlp':
        score = random.uniform(0.3, 0.8)
    else:
        score = random.uniform(0.2, 0.9)
    
    # 确定标签
    if score >= 0.6:
        tag = 'positive'
    elif score >= 0.4:
        tag = 'neutral'
    else:
        tag = 'negative'
    
    inference_time = (time.time() - start) * 1000  # 转换为毫秒
    
    return TestResponse(
        model_id=request.model_id,
        text=request.text,
        sentiment_score=round(score, 3),
        sentiment_tag=tag,
        confidence=round(random.uniform(0.7, 0.95), 3),
        inference_time=round(inference_time, 2)
    )

@router.post("/models/{model_id}/activate")
async def activate_model(model_id: str):
    """
    激活模型（设为当前使用的模型）
    """
    model = get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 在实际应用中，这里应该更新数据库中的当前模型配置
    return {
        'success': True,
        'message': f'模型 {model["name"]} 已激活',
        'model_id': model_id
    }

@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """
    删除模型
    """
    model = get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 在实际应用中，这里应该删除模型文件和数据
    return {
        'success': True,
        'message': f'模型 {model["name"]} 已删除'
    }

@router.get("/models/metrics/{model_id}")
async def get_model_metrics(model_id: str):
    """
    获取模型详细指标（混淆矩阵、PR曲线等）
    """
    model = get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 模拟指标数据
    return {
        'model_id': model_id,
        'confusion_matrix': {
            'positive': [85, 8, 7],
            'neutral': [6, 78, 16],
            'negative': [4, 12, 84]
        },
        'precision_recall': {
            'positive': {'precision': 0.89, 'recall': 0.85},
            'neutral': {'precision': 0.82, 'recall': 0.79},
            'negative': {'precision': 0.86, 'recall': 0.88}
        },
        'f1_scores': {
            'positive': 0.87,
            'neutral': 0.80,
            'negative': 0.87
        },
        'accuracy': model['accuracy'],
        'training_history': {
            'loss': [0.8, 0.5, 0.3, 0.2, 0.15],
            'accuracy': [0.7, 0.8, 0.85, 0.88, 0.9]
        }
    }

@router.get("/models/datasets")
async def get_datasets():
    """
    获取可用的训练数据集
    """
    # 从数据库获取已分析的视频作为数据集候选
    try:
        sql = """
        SELECT bvid, title, total_danmaku, analyzed_at 
        FROM analysis_results 
        ORDER BY analyzed_at DESC 
        LIMIT 20
        """
        with db.get_cursor() as cursor:
            cursor.execute(sql)
            datasets = cursor.fetchall()
        
        return {
            'total': len(datasets),
            'datasets': [
                {
                    'bvid': d['bvid'],
                    'title': d['title'],
                    'size': d['total_danmaku'],
                    'created_at': d['analyzed_at'].strftime('%Y-%m-%d %H:%M:%S')
                } for d in datasets
            ]
        }
    except Exception as e:
        # 返回模拟数据
        return {
            'total': 3,
            'datasets': [
                {'bvid': 'BV1GJ411x7h7', 'title': '视频1', 'size': 1200, 'created_at': '2024-03-01'},
                {'bvid': 'BV1xx', 'title': '视频2', 'size': 800, 'created_at': '2024-03-02'},
                {'bvid': 'BV1yy', 'title': '视频3', 'size': 1500, 'created_at': '2024-03-03'}
            ]
        }

@router.get("/models/dataset/info")
async def get_dataset_info():
    """
    获取训练数据集信息
    """
    try:
        from utils.dataset import DatasetManager
        manager = DatasetManager(output_dir='./data')
        info = manager.get_dataset_info()
        
        if not info.get('exists'):
            return {
                'exists': False,
                'message': '暂无训练数据集，请先分析视频',
                'total_danmakus': 0
            }
        
        return {
            'exists': True,
            'filename': info['filename'],
            'total': info['total'],
            'train_size': info['train_size'],
            'val_size': info['val_size'],
            'created_at': info['created_at']
        }
    except Exception as e:
        return {
            'exists': False,
            'error': str(e)
        }

@router.post("/models/dataset/generate")
async def generate_dataset():
    """
    从数据库生成训练数据集
    """
    try:
        from utils.dataset import DatasetManager
        import os
        
        manager = DatasetManager(output_dir='./data')
        
        # 检查现有数据量
        info = manager.get_dataset_info()
        if info.get('exists'):
            return {
                'success': True,
                'message': '数据集已存在',
                'total': info['total'],
                'train_size': info['train_size'],
                'val_size': info['val_size']
            }
        
        # 生成新数据集
        dataset_path = manager.generate_training_dataset(name='bilibili_danmaku')
        
        if dataset_path:
            return {
                'success': True,
                'message': '数据集生成成功',
                'filepath': dataset_path
            }
        else:
            return {
                'success': False,
                'message': '数据量不足，请先分析更多视频'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@router.get("/models/training/status")
async def get_training_status():
    """
    获取当前模型训练状态
    """
    try:
        import os
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'bert_sentiment')
        config_path = os.path.join(model_path, 'training_result.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                import json
                result = json.load(f)
            return {
                'trained': True,
                'metrics': result.get('metrics', {}),
                'trained_at': result.get('trained_at', ''),
                'dataset_size': result.get('dataset_size', 0)
            }
        else:
            return {
                'trained': False,
                'message': '尚未训练模型'
            }
    except Exception as e:
        return {
            'trained': False,
            'error': str(e)
        }