"""
情感分析模块 - 支持SnowNLP和BERT
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from snownlp import SnowNLP
from utils.crawler import get_barrage


# BERT模型单例
_bert_model = None

def get_bert_sentiment_model():
    """获取BERT情感分析模型单例"""
    global _bert_model
    if _bert_model is None:
        try:
            from models.bert_model import BertSentimentModel
            _bert_model = BertSentimentModel()
        except Exception as e:
            print(f"BERT模型加载失败: {e}")
            return None
    return _bert_model


def sentiment_analyse(
        url: str,
        headers: Dict[str, str],
        use_bert: bool = False
) -> pd.DataFrame:
    """
    对弹幕进行情感分析
    
    Args:
        url: 视频URL
        headers: 请求头
        use_bert: 是否使用BERT模型
    
    Returns:
        DataFrame: 包含score和tag两列
    """
    # 获取弹幕
    barrage = get_barrage(
        url=url,
        headers=headers,
        type_='Video'
    )
    
    if len(barrage) == 0:
        return pd.DataFrame(columns=['score', 'tag'])
    
    content_list = barrage['content'].tolist()
    
    # 使用BERT模型
    if use_bert:
        return _sentiment_analyse_bert(content_list)
    
    # 使用SnowNLP
    return _sentiment_analyse_snownlp(content_list)


def _sentiment_analyse_bert(content_list: list) -> pd.DataFrame:
    """使用BERT模型进行情感分析"""
    score_list = []
    tag_list = []
    
    bert_model = get_bert_sentiment_model()
    
    if bert_model is None or bert_model.model is None:
        print("BERT模型不可用，回退到SnowNLP")
        return _sentiment_analyse_snownlp(content_list)
    
    try:
        # 批量预测
        results = bert_model.predict(content_list)
        
        for result in results:
            score = result['sentiment_score']
            tag = result['sentiment_tag']
            
            score_list.append(score)
            tag_list.append(tag)
            
    except Exception as e:
        print(f"BERT预测失败: {e}，回退到SnowNLP")
        return _sentiment_analyse_snownlp(content_list)
    
    sentiment_df = pd.DataFrame({
        'score': score_list,
        'tag': tag_list
    })
    
    print(f"BERT情感分析完成：积极{sum(tag=='positive' for tag in tag_list)}条，"
          f"中性{sum(tag=='neutral' for tag in tag_list)}条，"
          f"消极{sum(tag=='negative' for tag in tag_list)}条")
    
    return sentiment_df


def _sentiment_analyse_snownlp(content_list: list) -> pd.DataFrame:
    score_list = []
    tag_list = []
    
    for text in content_list:
        try:
            if not text or len(text) < 2:
                continue
                
            s = SnowNLP(text)
            score = s.sentiments
            
            # 根据情感分数打标签
            if score < 0.3:
                tag = 'negative'
            elif score > 0.4:
                tag = 'positive'
            else:
                tag = 'neutral'
            
            score_list.append(round(score, 3))
            tag_list.append(tag)
            
        except Exception as e:
            # 如果分析失败，跳过这条弹幕
            continue
    
    sentiment_df = pd.DataFrame({
        'score': score_list,
        'tag': tag_list
    })
    
    print(f"SnowNLP情感分析完成：积极{sum(tag=='positive' for tag in tag_list)}条，"
          f"中性{sum(tag=='neutral' for tag in tag_list)}条，"
          f"消极{sum(tag=='negative' for tag in tag_list)}条")
    
    return sentiment_df


def sentiment_trend(
        url: str,
        headers: Dict[str, str],
        segment: int = 15,
        use_bert: bool = False
) -> pd.DataFrame:
    """
    计算情感趋势（每个时间段的情感分布）
    
    Args:
        url: 视频URL
        headers: 请求头
        segment: 时间段大小(秒)
        use_bert: 是否使用BERT模型
    
    Returns:
        DataFrame: 包含positive, neutral, negative, segment_range四列
    """
    # 获取弹幕
    barrage = get_barrage(
        url=url,
        headers=headers,
        type_='Video'
    )
    
    if len(barrage) == 0:
        return pd.DataFrame(columns=['positive', 'neutral', 'negative', 'segment_range'])
    
    # 情感分析
    sentiment_df = sentiment_analyse(
        url=url,
        headers=headers,
        use_bert=use_bert
    )
    
    if len(sentiment_df) == 0:
        return pd.DataFrame(columns=['positive', 'neutral', 'negative', 'segment_range'])
    
    # 合并时间和情感
    df = pd.concat([barrage[['time']], sentiment_df], axis=1)
    
    # 计算时间段数量
    max_time = df['time'].max()
    num_segment = int(np.ceil(max_time / segment))
    
    # 生成时间段标签
    segment_list = []
    for i in range(num_segment):
        start = i * segment
        end = (i + 1) * segment
        segment_list.append(f'{start}-{end}')
    
    # 统计每个时间段的情感分布
    result = []
    for i, seg_range in enumerate(segment_list):
        start = i * segment
        end = (i + 1) * segment
        
        # 筛选该时间段的数据
        seg_df = df[(df['time'] >= start) & (df['time'] < end)]
        
        if len(seg_df) > 0:
            pos_count = sum(seg_df['tag'] == 'positive')
            neu_count = sum(seg_df['tag'] == 'neutral')
            neg_count = sum(seg_df['tag'] == 'negative')
        else:
            pos_count = neu_count = neg_count = 0
        
        result.append({
            'segment_range': seg_range,
            'positive': pos_count,
            'neutral': neu_count,
            'negative': neg_count,
            'total': pos_count + neu_count + neg_count
        })
    
    trend_df = pd.DataFrame(result)
    return trend_df


def get_sentiment_stats(sentiment_df: pd.DataFrame) -> Dict:
    """
    获取情感统计信息
    """
    if len(sentiment_df) == 0:
        return {
            'positive_ratio': 0,
            'neutral_ratio': 0,
            'negative_ratio': 0,
            'avg_score': 0
        }
    
    total = len(sentiment_df)
    pos_count = sum(sentiment_df['tag'] == 'positive')
    neu_count = sum(sentiment_df['tag'] == 'neutral')
    neg_count = sum(sentiment_df['tag'] == 'negative')
    
    return {
        'positive_ratio': round(pos_count / total * 100, 1),
        'neutral_ratio': round(neu_count / total * 100, 1),
        'negative_ratio': round(neg_count / total * 100, 1),
        'avg_score': round(sentiment_df['score'].mean(), 3)
    }