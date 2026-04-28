"""
BERT微调训练脚本
从数据库导出数据并训练模型
解决弹幕情感分析准确率低的问题
"""
import os
os.environ['HF_HOME'] = 'D:\\AI_Cache\\huggingface' 
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
import sys
import time
import json
import pickle
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.bert_model import BertSentimentModel, BertConfig
from utils.dataset import DatasetManager


def check_data_and_train():
    """
    检查数据集并训练模型
    """
    print("\n" + "="*60)
    print("🚀 BERT微调训练工具")
    print("="*60)
    
    # 检查依赖
    try:
        import torch
        print(f"✓ PyTorch: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("  (使用CPU训练，速度较慢)")
    except ImportError:
        print("❌ 缺少 PyTorch，请安装: pip install torch")
        return None
    
    # 1. 生成/加载数据集
    print("\n" + "-"*40)
    print("步骤1: 准备训练数据")
    print("-"*40)
    
    manager = DatasetManager(output_dir='./data')
    info = manager.get_dataset_info()
    
    if not info.get('exists'):
        print("📦 正在从数据库导出数据...")
        dataset_path = manager.generate_training_dataset(name='bilibili_danmaku')
        if dataset_path is None:
            print("\n❌ 数据集生成失败")
            print("请先在首页分析几个视频，确保有足够的弹幕数据")
            return None
    else:
        print(f"✓ 已存在数据集: {info['filename']}")
        print(f"  总样本: {info['total']}")
        print(f"  训练集: {info['train_size']}")
        print(f"  验证集: {info['val_size']}")
        dataset_path = info['filepath']
    
    # 加载数据
    with open(dataset_path, 'rb') as f:
        data = pickle.load(f)
    
    train_texts = data['train']['texts']
    train_labels = data['train']['labels']
    val_texts = data['val']['texts']
    val_labels = data['val']['labels']
    
    print(f"\n✓ 数据加载完成")
    print(f"  训练集: {len(train_texts)} 条")
    print(f"  验证集: {len(val_texts)} 条")
    
    if len(train_texts) < 500:
        print(f"\n⚠️ 警告: 数据量较少 ({len(train_texts)} 条)")
        print("建议先分析更多视频以获得更好的训练效果")
    
    # 2. 配置训练参数
    print("\n" + "-"*40)
    print("步骤2: 配置训练参数")
    print("-"*40)
    
    config = BertConfig()
    config.num_labels = 3
    config.epochs = 3
    config.batch_size = 16
    config.learning_rate = 2e-5
    config.max_length = 64  # 弹幕文本较短，64足够
    config.model_name = 'bert-base-chinese'
    
    print(f"训练配置：")
    print(f"  - 基础模型: {config.model_name}")
    print(f"  - 训练轮数: {config.epochs}")
    print(f"  - 批次大小: {config.batch_size}")
    print(f"  - 学习率: {config.learning_rate}")
    print(f"  - 最大长度: {config.max_length}")
    print(f"  - 训练设备: {config.device}")
    
    # 3. 训练模型
    print("\n" + "-"*40)
    print("步骤3: 开始训练")
    print("-"*40)
    print("训练中，请稍候...")
    
    model = BertSentimentModel(config)
    
    start_time = time.time()
    result = model.train(
        train_texts=train_texts,
        train_labels=train_labels,
        val_texts=val_texts,
        val_labels=val_labels
    )
    training_time = time.time() - start_time
    
    print(f"\n⏱️ 训练耗时: {training_time:.1f} 秒")
    
    # 4. 评估模型
    print("\n" + "-"*40)
    print("步骤4: 评估模型")
    print("-"*40)
    
    metrics = model.evaluate(val_texts, val_labels)
    
    print(f"\n模型性能:")
    print(f"  准确率: {metrics['accuracy']*100:.1f}%")
    print(f"  精确率: {metrics['precision']*100:.1f}%")
    print(f"  召回率: {metrics['recall']*100:.1f}%")
    print(f"  F1分数: {metrics['f1']*100:.1f}%")
    
    print(f"\n混淆矩阵:")
    cm = metrics['confusion_matrix']
    print("         预测:消极  预测:中性  预测:积极")
    print(f"实际:消极     {cm[0][0]:4d}      {cm[0][1]:4d}      {cm[0][2]:4d}")
    print(f"实际:中性     {cm[1][0]:4d}      {cm[1][1]:4d}      {cm[1][2]:4d}")
    print(f"实际:积极     {cm[2][0]:4d}      {cm[2][1]:4d}      {cm[2][2]:4d}")
    
    # 5. 保存结果
    print("\n" + "-"*40)
    print("步骤5: 保存模型")
    print("-"*40)
    
    result_info = {
        'dataset_path': dataset_path,
        'dataset_size': len(train_texts) + len(val_texts),
        'training_time_seconds': training_time,
        'metrics': {
            'accuracy': round(metrics['accuracy'] * 100, 2),
            'precision': round(metrics['precision'] * 100, 2),
            'recall': round(metrics['recall'] * 100, 2),
            'f1': round(metrics['f1'] * 100, 2)
        },
        'trained_at': datetime.now().isoformat()
    }
    
    result_path = os.path.join(config.model_path, 'training_result.json')
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result_info, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 模型已保存: {config.model_path}")
    print(f"✓ 结果记录: {result_path}")
    
    print("\n" + "="*60)
    print("✅ 训练完成!")
    print(f"   最终准确率: {metrics['accuracy']*100:.1f}%")
    print("="*60)
    
    return model


def test_trained_model():
    """测试已训练的模型"""
    print("\n" + "="*60)
    print("🧪 测试训练好的模型")
    print("="*60)
    
    try:
        model = BertSentimentModel()
        model.load_model()
    except Exception as e:
        print(f"❌ 无法加载模型: {e}")
        print("请先运行训练")
        return
    
    # 【修改这里：加入弹幕特色用例和我们的“理性陈述”验收用例】
    test_samples = [
        "太牛了！这操作绝了",                 # 期望: 积极
        "就这？就这？我直呼内行",             # 期望: 消极 (反讽)
        "哈哈哈哈哈笑死我了",                 # 期望: 积极
        "封建的制度必将灭亡",                 # 期望: 中性 (验收大模型提示词是否成功迁移)
        "宗教忽悠不住年轻人了",               # 期望: 中性 (验收大模型提示词是否成功迁移)
        "这什么垃圾视频，退钱了",             # 期望: 消极
        "弹幕护体",                           # 期望: 中性 (无意义刷屏)
        "高能预警",                           # 期望: 中性 (常规弹幕)
        "后面有糖",                           # 期望: 中性 (客观提示)
        "看哭了，太感动了",                   # 期望: 积极
    ]
    
    print("\n测试结果:")
    for text in test_samples:
        result = model.predict(text)[0]
        emoji = {"positive": "😊", "neutral": "😐", "negative": "😡"}[result['sentiment_tag']] # 把消极换成生气更直观
        print(f"  {emoji} [{result['sentiment_tag']:>7s}] ({result['sentiment_score']:.2f}) | {text}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='BERT微调训练')
    parser.add_argument('--train', action='store_true', help='训练模型')
    parser.add_argument('--test', action='store_true', help='测试模型')
    
    args = parser.parse_args()
    
    if args.train:
        check_data_and_train()
    elif args.test:
        test_trained_model()
    else:
        # 交互式菜单
        print("\n请选择操作:")
        print("  1. 训练模型 (从数据库导出数据并训练)")
        print("  2. 测试模型")
        print("  3. 训练并测试")
        
        choice = input("\n请选择 (1/2/3): ").strip()
        
        if choice == '1':
            check_data_and_train()
        elif choice == '2':
            test_trained_model()
        elif choice == '3':
            model = check_data_and_train()
            if model:
                test_trained_model()
        else:
            print("无效选择")