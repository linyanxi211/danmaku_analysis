"""
BERT情感分析模型模块
提供基于BERT的微调情感分析功能

这个文件实现了一个完整的BERT情感分析模型，包括：
1. 模型配置管理
2. 数据集处理
3. 模型训练、评估和预测
4. 模型保存和加载
5. ONNX格式导出

使用场景：
- 对B站视频弹幕进行情感分析
- 训练和微调BERT模型
- 批量处理情感分析任务
"""

# 导入必要的库
import os  # 用于文件路径操作
import json  # 用于处理JSON数据
import torch  # PyTorch深度学习库
import torch.nn as nn  # 神经网络模块
import numpy as np  # 数值计算库
import pandas as pd  # 数据处理库
from typing import Dict, List, Tuple, Optional, Union  # 类型提示
from transformers import (
    BertTokenizer,  # BERT分词器
    BertForSequenceClassification,  # BERT分类模型
    Trainer,  # 训练器
    TrainingArguments,  # 训练参数
    get_linear_schedule_with_warmup  # 学习率预热调度器
)
from torch.optim import AdamW  # AdamW优化器
from torch.utils.data import Dataset, DataLoader  # 数据集和数据加载器
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix  # 评估指标
import joblib  # 模型序列化
from datetime import datetime  # 日期时间处理
import warnings  # 警告处理
warnings.filterwarnings('ignore')  # 忽略警告

# ==================== 配置类 ====================

class BertConfig:
    """BERT模型配置类
    
    管理BERT模型的所有配置参数，包括模型名称、训练参数等
    """
    def __init__(self):
        # 模型基本配置
        self.model_name = 'bert-base-chinese'  # 使用中文BERT预训练模型
        self.num_labels = 3  # 情感类别数：积极、中性、消极
        self.max_length = 128  # 文本最大长度，超过会被截断
        
        # 训练参数
        self.batch_size = 16  # 每个批次的样本数
        self.learning_rate = 2e-5  # 学习率，BERT模型通常使用较小的学习率
        self.epochs = 3  # 训练轮数
        self.weight_decay = 0.01  # 权重衰减，防止过拟合
        self.warmup_steps = 0  # 学习率预热步数
        
        # 设备配置
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # 自动选择GPU或CPU
        
        # 模型保存路径
        self.model_path = os.path.join(os.getcwd(), 'models', 'bert_sentiment')
        
        # 混合精度训练（仅在有GPU时使用）
        self.use_fp16 = torch.cuda.is_available()
        
        # 情感标签映射
        self.label_map = {
            'positive': 2,  # 积极情感对应标签0
            'neutral': 1,   # 中性情感对应标签1
            'negative': 0   # 消极情感对应标签2
        }
        self.id2label = {2: 'positive', 1: 'neutral', 0: 'negative'}  # 标签ID到情感的映射
        
        # 确保模型目录存在，如果不存在则创建
        os.makedirs(self.model_path, exist_ok=True)

# ==================== 数据集类 ====================

class SentimentDataset(Dataset):
    """情感分析数据集类
    
    用于处理和加载情感分析数据，继承自PyTorch的Dataset类
    """
    
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int):
        """初始化数据集
        
        Args:
            texts: 文本列表
            labels: 标签列表
            tokenizer: BERT分词器
            max_length: 最大序列长度
        """
        self.texts = texts  # 存储文本数据
        self.labels = labels  # 存储标签数据
        self.tokenizer = tokenizer  # 存储分词器
        self.max_length = max_length  # 存储最大长度
    
    def __len__(self):
        """返回数据集大小"""
        return len(self.texts)
    
    def __getitem__(self, idx):
        """获取指定索引的样本
        
        Args:
            idx: 样本索引
            
        Returns:
            包含input_ids、attention_mask和labels的字典
        """
        text = str(self.texts[idx])  # 获取文本并转换为字符串
        label = self.labels[idx]  # 获取标签
        
        # 使用分词器对文本进行处理
        encoding = self.tokenizer(
            text,
            truncation=True,  # 超过最大长度时截断
            padding='max_length',  # 不足最大长度时填充
            max_length=self.max_length,  # 最大长度
            return_tensors='pt'  # 返回PyTorch张量
        )
        
        # 返回处理后的数据
        return {
            'input_ids': encoding['input_ids'].flatten(),  # 输入ID，展平为一维
            'attention_mask': encoding['attention_mask'].flatten(),  # 注意力掩码，展平为一维
            'labels': torch.tensor(label, dtype=torch.long)  # 标签，转换为长整型张量
        }

# ==================== BERT模型类 ====================

class BertSentimentModel:
    """BERT情感分析模型类
    
    实现BERT模型的训练、评估和预测功能
    """
    
    def __init__(self, config: BertConfig = None):
        """初始化模型
        
        Args:
            config: 模型配置，如果为None则使用默认配置
        """
        self.config = config or BertConfig()  # 使用传入的配置或默认配置
        self.tokenizer = None  # 分词器
        self.model = None  # BERT模型
        self.trainer = None  # 训练器
        self.is_trained = False  # 模型是否已训练
        
        # 如果存在已训练模型，自动加载
        model_bin = os.path.join(self.config.model_path, 'pytorch_model.bin')
        model_safetensors = os.path.join(self.config.model_path, 'model.safetensors')
        if os.path.exists(model_bin) or os.path.exists(model_safetensors):
            self.load_model()
    
    def _init_model(self):
        """初始化模型和分词器"""
        print(f"正在加载预训练模型: {self.config.model_name}")
        # 加载预训练分词器
        self.tokenizer = BertTokenizer.from_pretrained(self.config.model_name)
        # 加载预训练BERT模型用于分类任务
        self.model = BertForSequenceClassification.from_pretrained(
            self.config.model_name,
            num_labels=self.config.num_labels
        )
        # 将模型移动到指定设备
        self.model.to(self.config.device)
        print(f"模型加载完成，使用设备: {self.config.device}")
    
    def _prepare_data(self, texts: List[str], labels: List[int]) -> SentimentDataset:
        """准备数据集
        
        Args:
            texts: 文本列表
            labels: 标签列表
            
        Returns:
            情感分析数据集实例
        """
        return SentimentDataset(
            texts=texts,
            labels=labels,
            tokenizer=self.tokenizer,
            max_length=self.config.max_length
        )
    
    def _compute_metrics(self, eval_pred):
        """计算评估指标
        
        Args:
            eval_pred: 评估预测结果，包含预测值和真实标签
            
        Returns:
            包含各种评估指标的字典
        """
        predictions, labels = eval_pred  # 解包预测结果和真实标签
        predictions = np.argmax(predictions, axis=1)  # 取概率最大的类别作为预测结果
        
        # 计算准确率
        accuracy = accuracy_score(labels, predictions)
        # 计算精确率、召回率、F1分数（加权平均）
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average='weighted'
        )
        
        # 计算混淆矩阵
        cm = confusion_matrix(labels, predictions)
        
        # 返回评估指标
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion_matrix': cm.tolist()
        }
    
    def train(
        self,
        train_texts: List[str],
        train_labels: List[int],
        val_texts: Optional[List[str]] = None,
        val_labels: Optional[List[int]] = None,
        output_dir: Optional[str] = None
    ) -> Dict:
        """
        训练模型
        
        Args:
            train_texts: 训练文本列表
            train_labels: 训练标签列表
            val_texts: 验证文本列表（可选）
            val_labels: 验证标签列表（可选）
            output_dir: 输出目录（可选）
        
        Returns:
            训练历史信息
        """
        # 如果模型未初始化，先初始化
        if self.model is None:
            self._init_model()
        
        # 准备训练数据
        print("正在准备训练数据...")
        train_dataset = self._prepare_data(train_texts, train_labels)
        
        # 准备验证数据（如果提供）
        val_dataset = None
        if val_texts and val_labels:
            val_dataset = self._prepare_data(val_texts, val_labels)
        
        # 设置训练参数
        training_args = TrainingArguments(
            output_dir=output_dir or self.config.model_path,  # 输出目录
            num_train_epochs=self.config.epochs,  # 训练轮数
            per_device_train_batch_size=self.config.batch_size,  # 训练批次大小
            per_device_eval_batch_size=self.config.batch_size,  # 评估批次大小
            warmup_steps=self.config.warmup_steps,  # 学习率预热步数
            weight_decay=self.config.weight_decay,  # 权重衰减
            logging_dir=os.path.join(self.config.model_path, 'logs'),  # 日志目录
            logging_steps=100,  # 每100步记录一次日志
            eval_strategy="epoch" if val_dataset else "no",  # 评估策略
            save_strategy="epoch",  # 保存策略
            load_best_model_at_end=True if val_dataset else False,  # 是否加载最佳模型
            metric_for_best_model="accuracy",  # 评估最佳模型的指标
            greater_is_better=True,  # 指标是否越大越好
            fp16=self.config.use_fp16,  # 是否使用混合精度训练
            dataloader_num_workers=2,  # 数据加载器工作线程数
            report_to="none"  # 不报告到外部服务
        )
        
        # 创建训练器
        self.trainer = Trainer(
            model=self.model,  # 模型
            args=training_args,  # 训练参数
            train_dataset=train_dataset,  # 训练数据集
            eval_dataset=val_dataset,  # 验证数据集
            compute_metrics=self._compute_metrics  # 评估指标计算函数
        )
        
        # 开始训练
        print("开始训练...")
        train_result = self.trainer.train()
        
        # 保存模型
        self.trainer.save_model()
        self.tokenizer.save_pretrained(self.config.model_path)
        
        # 保存配置
        config_path = os.path.join(self.config.model_path, 'model_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({
                'label_map': self.config.label_map,
                'id2label': self.config.id2label,
                'num_labels': self.config.num_labels,
                'max_length': self.config.max_length,
                'trained_at': datetime.now().isoformat()  # 训练时间
            }, f, ensure_ascii=False, indent=2)
        
        self.is_trained = True
        print(f"模型训练完成，已保存至: {self.config.model_path}")
        
        # 返回训练历史
        return {
            'training_loss': train_result.training_loss,
            'global_step': train_result.global_step,
            'epoch': getattr(train_result, 'epoch', 3),
            'metrics': train_result.metrics if hasattr(train_result, 'metrics') else {}
        }
    
    def predict(self, texts: Union[str, List[str]]) -> List[Dict]:
        """
        预测情感
        
        Args:
            texts: 单个文本或文本列表
        
        Returns:
            预测结果列表，每个结果包含：
            - text: 原始文本
            - sentiment_score: 情感得分 (0-1)
            - sentiment_tag: 情感标签
            - confidence: 置信度
            - logits: 原始logits
            - probabilities: 各类别概率
        """
        # 检查模型是否已加载
        if self.model is None:
            raise ValueError("模型未加载，请先训练或加载模型")
        
        # 如果输入是单个文本，转换为列表
        if isinstance(texts, str):
            texts = [texts]
        
        # 对文本进行分词处理
        inputs = self.tokenizer(
            texts,
            truncation=True,  # 截断
            padding=True,  # 填充
            max_length=self.config.max_length,  # 最大长度
            return_tensors='pt'  # 返回PyTorch张量
        )
        
        # 将输入移动到指定设备
        inputs = {k: v.to(self.config.device) for k, v in inputs.items()}
        
        # 进行预测
        self.model.eval()  # 设置模型为评估模式
        with torch.no_grad():  # 禁用梯度计算，节省内存
            outputs = self.model(**inputs)  # 模型前向传播
            logits = outputs.logits  # 获取模型输出的原始分数
            probabilities = torch.nn.functional.softmax(logits, dim=-1)  # 转换为概率
            predictions = torch.argmax(logits, dim=-1)  # 获取预测类别
        
        # 手动设置默认标签映射（确保映射存在）
        self.config.id2label = {2: 'positive', 1: 'neutral', 0: 'negative'}
        self.config.label_map = {'positive': 2, 'neutral': 1, 'negative': 0}

        # 计算情感得分（0-1之间）
        # 使用softmax概率加权计算，积极情感得分高，消极情感得分低
        sentiment_scores = []
        for prob in probabilities.cpu().numpy():
            # prob[0] 是 negative 概率, prob[1] 是 neutral 概率, prob[2] 是 positive 概率
            score = (prob[0] * 0.0 + prob[1] * 0.5 + prob[2] * 1.0)
            sentiment_scores.append(float(score))
        
        # 构建预测结果
        results = []
        for i, text in enumerate(texts):
            pred_label = predictions[i].item()  # 获取预测标签ID
            prob = probabilities[i].cpu().numpy()  # 获取预测概率
            
            results.append({
                'text': text,  # 原始文本
                'sentiment_score': round(sentiment_scores[i], 3),  # 情感得分，保留3位小数
                'sentiment_tag': self.config.id2label[pred_label],  # 情感标签
                'confidence': round(float(prob[pred_label]), 3),  # 置信度
                'logits': logits[i].cpu().tolist(),  # 原始logits
                'probabilities': {  # 各类别概率
                    'positive': round(float(prob[2]), 3),
                    'neutral': round(float(prob[1]), 3),
                    'negative': round(float(prob[0]), 3)
                }
            })
        
        return results
    
    def predict_batch(self, texts: List[str], batch_size: int = 32) -> List[Dict]:
        """
        批量预测（适用于大量文本）
        
        Args:
            texts: 文本列表
            batch_size: 批次大小
            
        Returns:
            预测结果列表
        """
        results = []
        # 分批处理文本
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]  # 获取当前批次的文本
            batch_results = self.predict(batch_texts)  # 预测当前批次
            results.extend(batch_results)  # 将结果添加到总结果中
        return results
    
    def evaluate(self, test_texts: List[str], test_labels: List[int]) -> Dict:
        """
        评估模型性能
        
        Args:
            test_texts: 测试文本列表
            test_labels: 测试标签列表
            
        Returns:
            评估指标字典
        """
        # 检查模型是否已加载
        if self.model is None:
            raise ValueError("模型未加载，请先训练或加载模型")
        
        # 准备测试数据集
        test_dataset = self._prepare_data(test_texts, test_labels)
        
        # 创建评估器
        eval_trainer = Trainer(model=self.model)
        
        # 评估
        eval_results = eval_trainer.evaluate(test_dataset)
        
        # 详细计算评估指标
        predictions = []
        labels = []
        
        self.model.eval()  # 设置模型为评估模式
        dataloader = DataLoader(test_dataset, batch_size=self.config.batch_size)  # 创建数据加载器
        
        with torch.no_grad():  # 禁用梯度计算
            for batch in dataloader:
                # 将数据移动到指定设备
                input_ids = batch['input_ids'].to(self.config.device)
                attention_mask = batch['attention_mask'].to(self.config.device)
                label = batch['labels'].to(self.config.device)
                
                # 模型前向传播
                outputs = self.model(input_ids, attention_mask=attention_mask)
                pred = torch.argmax(outputs.logits, dim=-1)  # 获取预测结果
                
                # 将结果添加到列表
                predictions.extend(pred.cpu().tolist())
                labels.extend(label.cpu().tolist())
        
        # 计算评估指标
        accuracy = accuracy_score(labels, predictions)  # 准确率
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, predictions, average='weighted'  # 精确率、召回率、F1分数
        )
        cm = confusion_matrix(labels, predictions)  # 混淆矩阵
        
        # 返回评估指标
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion_matrix': cm.tolist(),
            'eval_loss': eval_results.get('eval_loss', 0),
            'num_samples': len(test_labels)
        }
    
    def load_model(self, model_path: Optional[str] = None):
        """
        加载已训练的模型
        
        Args:
            model_path: 模型路径（可选）
        """
        load_path = model_path or self.config.model_path  # 使用指定路径或默认路径
        
        # 检查路径是否存在
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"模型路径不存在: {load_path}")
        
        print(f"正在加载模型: {load_path}")
        # 加载分词器
        self.tokenizer = BertTokenizer.from_pretrained(load_path)
        # 加载模型
        self.model = BertForSequenceClassification.from_pretrained(load_path)
        # 将模型移动到指定设备
        self.model.to(self.config.device)
        
        # 加载配置
        config_path = os.path.join(load_path, 'model_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                # 更新配置
                self.config.label_map = saved_config.get('label_map', self.config.label_map)
                self.config.id2label = saved_config.get('id2label', self.config.id2label)
                self.config.num_labels = saved_config.get('num_labels', self.config.num_labels)
                self.config.max_length = saved_config.get('max_length', self.config.max_length)
        
        self.is_trained = True
        print(f"模型加载完成，使用设备: {self.config.device}")
    
    def save_model(self, save_path: Optional[str] = None):
        """
        保存模型
        
        Args:
            save_path: 保存路径（可选）
        """
        save_path = save_path or self.config.model_path  # 使用指定路径或默认路径
        
        # 检查模型是否存在
        if self.model is None:
            raise ValueError("没有可保存的模型")
        
        # 保存模型和分词器
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)
        
        # 保存配置
        config_path = os.path.join(save_path, 'model_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({
                'label_map': self.config.label_map,
                'id2label': self.config.id2label,
                'num_labels': self.config.num_labels,
                'max_length': self.config.max_length,
                'saved_at': datetime.now().isoformat()  # 保存时间
            }, f, ensure_ascii=False, indent=2)
        
        print(f"模型已保存至: {save_path}")
    
    def export_onnx(self, save_path: Optional[str] = None):
        """
        导出为ONNX格式（用于加速推理）
        
        Args:
            save_path: 保存路径（可选）
            
        Returns:
            保存路径或None（如果导出失败）
        """
        try:
            import torch.onnx  # 导入ONNX模块
            
            save_path = save_path or os.path.join(self.config.model_path, 'model.onnx')  # 使用指定路径或默认路径
            
            # 准备示例输入
            dummy_input = self.tokenizer(
                "测试文本",
                return_tensors='pt',
                max_length=self.config.max_length,
                padding='max_length',
                truncation=True
            )
            
            # 导出ONNX模型
            torch.onnx.export(
                self.model,  # 模型
                (dummy_input['input_ids'].to(self.config.device),
                 dummy_input['attention_mask'].to(self.config.device)),  # 输入
                save_path,  # 保存路径
                input_names=['input_ids', 'attention_mask'],  # 输入名称
                output_names=['logits'],  # 输出名称
                dynamic_axes={  # 动态轴（支持可变批次大小）
                    'input_ids': {0: 'batch_size'},
                    'attention_mask': {0: 'batch_size'},
                    'logits': {0: 'batch_size'}
                },
                opset_version=11  # ONNX操作集版本
            )
            
            print(f"ONNX模型已导出至: {save_path}")
            return save_path
            
        except Exception as e:
            print(f"ONNX导出失败: {e}")
            return None

# ==================== 工具函数 ====================

def prepare_data_from_db(bvid: str, limit: int = 10000) -> Tuple[List[str], List[int]]:
    """
    从数据库加载数据用于训练
    
    Args:
        bvid: B站视频ID
        limit: 数据限制数量
        
    Returns:
        文本列表和标签列表
    """
    from utils.database import db  # 导入数据库工具
    
    # SQL查询语句
    sql = """
    SELECT content, sentiment_tag FROM danmakus 
    WHERE bvid = %s AND sentiment_tag IS NOT NULL
    LIMIT %s
    """
    
    # 执行查询
    with db.get_cursor() as cursor:
        cursor.execute(sql, (bvid, limit))
        results = cursor.fetchall()
    
    # 提取文本
    texts = [r['content'] for r in results]
    
    # 转换标签
    label_map = {'positive': 0, 'neutral': 1, 'negative': 2}
    labels = [label_map.get(r['sentiment_tag'], 1) for r in results]
    
    return texts, labels

def create_bert_model():
    """
    创建BERT模型实例的工厂函数
    
    Returns:
        BERT情感分析模型实例
    """
    return BertSentimentModel()

# 单例模式实现
_bert_model = None  # 全局模型实例

def get_bert_model():
    """
    获取BERT模型单例
    
    Returns:
        BERT情感分析模型单例
    """
    global _bert_model  # 声明全局变量
    if _bert_model is None:  # 如果模型实例不存在
        _bert_model = BertSentimentModel()  # 创建新实例
    return _bert_model  # 返回模型实例