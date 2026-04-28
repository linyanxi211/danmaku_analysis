"""
分析API - 处理视频分析请求
"""
import uuid
import time
import json
import re
import os
import numpy as np
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import pandas as pd

# 导入工具模块
from utils.crawler import (
    get_barrage,
    barrage_num,
    top_segment,
    barrage_keywords
)
from models.sentiment import (
    sentiment_analyse,
    sentiment_trend,
    get_sentiment_stats
)
from utils.word_frequency import count_word_frequency
from utils.helpers import get_bvid_from_url, ensure_dir
from utils.database import db  # 导入数据库模块

router = APIRouter()

# ==================== 请求/响应模型 ====================

class AnalysisRequest(BaseModel):
    url: str
    segment: int = 15
    save_fig: bool = False
    headers: Optional[Dict[str, str]] = None
    model: str = 'snownlp'  # 'snownlp' 或 'bert'

class AnalysisResponse(BaseModel):
    task_id: str
    bvid: str
    status: str
    message: str
    progress: int = 0

# ==================== 存储任务状态 ====================

analysis_tasks = {}

# ==================== 默认请求头 ====================

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# ==================== 辅助函数 ====================

def extract_bvid(url: str) -> str:
    """从URL中提取BV号"""
    match = re.search(r'BV\w+', url)
    return match.group() if match else 'unknown'

def generate_heatmap_data(barrage_df, sentiment_df, segment: int) -> List[List]:
    """生成热力图数据 [时间点, 情感层级, 弹幕数量]"""
    import pandas as pd
    if len(barrage_df) == 0 or len(sentiment_df) == 0:
        return []
    
    # 合并时间和情感分数
    df = pd.concat([barrage_df[['time']], sentiment_df], axis=1)
    
    # 计算时间段和情感层级
    df['time_segment'] = (df['time'] // segment) * segment
    df['sentiment_level'] = pd.cut(
        df['score'],
        bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
        labels=[0, 1, 2, 3, 4]
    )
    
    # 分组统计
    grouped = df.groupby(['time_segment', 'sentiment_level']).size().reset_index(name='count')
    
    # 转换为列表格式
    heatmap_data = []
    for _, row in grouped.iterrows():
        heatmap_data.append([
            int(row['time_segment']),
            int(row['sentiment_level']),
            int(row['count'])
        ])
    
    return heatmap_data

def generate_curve_data(trend_df: pd.DataFrame) -> List[List]:
    """生成情感曲线数据"""
    if len(trend_df) == 0:
        return []
    
    curve_data = []
    for _, row in trend_df.iterrows():
        # 解析时间段起始时间
        start = int(row['segment_range'].split('-')[0])
        
        # 计算平均情感值（加权平均）
        total = row.get('total', row['positive'] + row['neutral'] + row['negative'])
        if total > 0:
            avg_sentiment = (
                row['positive'] * 0.8 + 
                row['neutral'] * 0.5 + 
                row['negative'] * 0.2
            ) / total
        else:
            avg_sentiment = 0.5
        
        curve_data.append([start, round(avg_sentiment, 3)])
    
    return curve_data

def identify_peaks(trend_df: pd.DataFrame) -> Dict:
    print(f"📊 trend_df 数据:\n{trend_df}")
    """识别高潮时刻"""
    if len(trend_df) == 0:
        return {
            'positive': {'time': 0, 'value': 0, 'description': '无数据'},
            'negative': {'time': 0, 'value': 0, 'description': '无数据'},
            'density': {'time': 0, 'count': 0}
        }
    
    # 确保有total列
    if 'total' not in trend_df.columns:
        trend_df['total'] = trend_df['positive'] + trend_df['neutral'] + trend_df['negative']
    
    # 情感峰值（最积极）
    pos_idx = trend_df['positive'].idxmax()
    pos_row = trend_df.loc[pos_idx]
    pos_time = int(pos_row['segment_range'].split('-')[0])
    print(f"✅ 积极峰值: 索引={pos_idx}, 时间={pos_time}, 值={pos_row['positive']}")
    
    # 情感谷值（最消极）
    neg_idx = trend_df['negative'].idxmax()
    neg_row = trend_df.loc[neg_idx]
    neg_time = int(neg_row['segment_range'].split('-')[0])
    print(f"✅ 消极峰值: 索引={neg_idx}, 时间={neg_time}, 值={neg_row['negative']}")
    
    # 弹幕密度峰值
    den_idx = trend_df['total'].idxmax()
    den_row = trend_df.loc[den_idx]
    den_time = int(den_row['segment_range'].split('-')[0])
    print(f"✅ 密度峰值: 索引={den_idx}, 时间={den_time}, 值={den_row['total']}")
    
    return {
        'positive': {
            'time': pos_time,
            'value': int(pos_row['positive']),
            'description': '观众情绪最高涨的时刻'
        },
        'negative': {
            'time': neg_time,
            'value': int(neg_row['negative']),
            'description': '观众情绪最低落的时刻'
        },
        'density': {
            'time': den_time,
            'count': int(den_row['total'])
        }
    }

def generate_trend_data_from_df(barrage_df: pd.DataFrame, sentiment_df: pd.DataFrame, segment: int) -> pd.DataFrame:
    """将弹幕和情感DataFrame转换为时间轴趋势数据
    
    Args:
        barrage_df: 弹幕DataFrame，包含time和content列
        sentiment_df: 情感DataFrame，包含score和tag列
        segment: 时间段大小(秒)
    
    Returns:
        DataFrame: 包含positive, neutral, negative, segment_range, total列
    """
    if len(barrage_df) == 0 or len(sentiment_df) == 0:
        return pd.DataFrame(columns=['positive', 'neutral', 'negative', 'segment_range', 'total'])
    
    df = pd.concat([barrage_df[['time']], sentiment_df], axis=1)
    
    max_time = df['time'].max()
    num_segment = int(np.ceil(max_time / segment))
    
    segment_list = []
    for i in range(num_segment):
        start = i * segment
        end = (i + 1) * segment
        segment_list.append(f'{start}-{end}')
    
    result = []
    for i, seg_range in enumerate(segment_list):
        start = i * segment
        end = (i + 1) * segment
        
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
    
    return pd.DataFrame(result)


def extract_keywords_by_sentiment(url: str, headers: Dict) -> Dict:
    """按情感分类提取关键词"""
    # 获取所有弹幕
    barrage = get_barrage(url, headers, 'Video')
    
    if len(barrage) == 0:
        return {'positive': [], 'negative': []}
    
    # 情感分析
    sentiment = sentiment_analyse(url, headers)
    
    # 合并
    import pandas as pd
    df = pd.concat([barrage, sentiment], axis=1)
    
    # 分别提取积极和消极弹幕
    positive_text = '\n'.join(df[df['tag'] == 'positive']['content'].tolist())
    negative_text = '\n'.join(df[df['tag'] == 'negative']['content'].tolist())
    
    # 提取关键词
    import jieba.analyse
    
    # 设置停用词
    stopwords_path = os.path.join(os.path.dirname(__file__), '..', '..', 'stopwords.txt')
    if os.path.exists(stopwords_path):
        jieba.analyse.set_stop_words(stopwords_path)
    
    # 提取积极关键词
    positive_keywords = []
    if positive_text:
        pos_kw = jieba.analyse.textrank(positive_text, topK=10, withWeight=False)
        positive_keywords = [kw for kw in pos_kw if len(kw) > 1][:10]
    
    # 提取消极关键词
    negative_keywords = []
    if negative_text:
        neg_kw = jieba.analyse.textrank(negative_text, topK=10, withWeight=False)
        negative_keywords = [kw for kw in neg_kw if len(kw) > 1][:10]
    
    return {
        'positive': positive_keywords,
        'negative': negative_keywords
    }

# ==================== 真实分析任务 ====================

async def run_analysis_task(task_id: str, request: AnalysisRequest):
    """真实分析任务"""
    print(f"\n{'='*60}")
    print(f"🚀 开始分析任务: {task_id}")
    print(f"📹 视频URL: {request.url}")
    print(f"🤖 使用模型: {request.model}")
    print(f"{'='*60}")
    try:
        # ==================== 初始化 ====================
        # 更新内存状态
        analysis_tasks[task_id]['status'] = 'processing'
        analysis_tasks[task_id]['message'] = '开始分析...'
        
        headers = request.headers if request.headers else DEFAULT_HEADERS
        segment = request.segment
        use_bert = request.model == 'bert'
        
        # ==================== 位置1：创建任务记录 ====================
        bvid = extract_bvid(request.url)
        print(f"🔍 BV号: {bvid}")
        db.create_task(task_id, bvid)
        
        # 1. 爬取弹幕 (10%)
        print("🕷️ 开始爬取弹幕...")
        analysis_tasks[task_id]['progress'] = 10
        analysis_tasks[task_id]['message'] = '正在爬取弹幕...'
        db.update_task(task_id, 'processing', 10, '正在爬取弹幕...')
        
        barrage = get_barrage(
            url=request.url,
            headers=headers,
            type_='Video'
        )
        
        if len(barrage) == 0:
            raise Exception("未获取到弹幕数据")
        
        total_danmaku = len(barrage)
        analysis_tasks[task_id]['total_danmaku'] = total_danmaku
        print(f"✅ 爬取完成: {total_danmaku} 条弹幕")

        # ==================== 位置2：保存视频信息 ====================
        print("💾 保存视频信息...")
        
        # 从B站API获取视频详细信息
        video_info = {
            'bvid': bvid,
            'title': f'视频 {bvid}',
            'up_name': '未知',
            'duration': int(barrage['time'].max()) if len(barrage) > 0 else 0,
            'cover_url': ''
        }
        
        try:
            from api.video import fetch_video_info_from_bilibili
            api_video_info = fetch_video_info_from_bilibili(bvid, headers)
            if api_video_info:
                video_info['title'] = api_video_info.get('title', video_info['title'])
                video_info['up_name'] = api_video_info.get('up_name', video_info['up_name'])
                video_info['cover_url'] = api_video_info.get('cover_url', '')
                video_info['duration'] = api_video_info.get('duration', video_info['duration'])
        except Exception as e:
            print(f"⚠️ 获取视频信息失败: {e}")
        
        db.save_video(video_info)
        
        # 2. 情感分析 (30%)
        model_name = "BERT" if use_bert else "SnowNLP"
        print(f"🧠 进行情感分析 (使用{model_name})...")
        analysis_tasks[task_id]['progress'] = 30
        analysis_tasks[task_id]['message'] = f'正在使用{model_name}进行情感分析...'
        db.update_task(task_id, 'processing', 30, f'正在使用{model_name}进行情感分析...')
        
        sentiment_df = sentiment_analyse(
            url=request.url,
            headers=headers,
            use_bert=use_bert
        )
        
        # ==================== 位置3：保存弹幕数据 ====================
        if len(sentiment_df) > 0:
            print("💾 保存弹幕数据...")
            db.save_danmakus(bvid, barrage, sentiment_df)
        
        # 3. 情感趋势 (50%)
        print("📊 计算情感趋势...")
        analysis_tasks[task_id]['progress'] = 50
        analysis_tasks[task_id]['message'] = '正在计算情感趋势...'
        db.update_task(task_id, 'processing', 50, '正在计算情感趋势...')
        
        trend_df = sentiment_trend(
            url=request.url,
            headers=headers,
            segment=segment,
            use_bert=use_bert
        )
        print(f"✅ 情感趋势完成: {len(trend_df)} 个时间段")
        
        # 4. 生成热力图数据 (60%)
        print("🔥 生成热力图数据...")
        analysis_tasks[task_id]['progress'] = 60
        analysis_tasks[task_id]['message'] = '正在生成热力图数据...'
        db.update_task(task_id, 'processing', 60, '正在生成热力图数据...')
        
        heatmap_data = generate_heatmap_data(barrage, sentiment_df, segment)
        print(f"✅ 热力图数据生成: {len(heatmap_data)} 个数据点")

        # 5. 生成曲线数据 (70%)
        print("📈 生成情感曲线...")
        analysis_tasks[task_id]['progress'] = 70
        analysis_tasks[task_id]['message'] = '正在生成情感曲线...'
        db.update_task(task_id, 'processing', 70, '正在生成情感曲线...')
        
        curve_data = generate_curve_data(trend_df)
        print(f"✅ 曲线数据生成: {len(curve_data)} 个数据点")
        
        # 6. 识别高潮时刻 (80%)
        print("⏰ 识别高潮时刻...")
        analysis_tasks[task_id]['progress'] = 80
        analysis_tasks[task_id]['message'] = '正在识别高潮时刻...'
        db.update_task(task_id, 'processing', 80, '正在识别高潮时刻...')
        
        peaks = identify_peaks(trend_df)
        print(f"✅ 高潮时刻识别完成")

        # 7. 提取关键词 (90%)
        print("🔑 提取关键词...")
        analysis_tasks[task_id]['progress'] = 90
        analysis_tasks[task_id]['message'] = '正在提取关键词...'
        db.update_task(task_id, 'processing', 90, '正在提取关键词...')
        
        keywords = extract_keywords_by_sentiment(request.url, headers)
        print(f"✅ 关键词提取完成: 积极{len(keywords['positive'])}个, 消极{len(keywords['negative'])}个")

        # 8. 组装结果
        print("📦 组装结果...")
        result = {
            'bvid': bvid,
            'total_danmaku': total_danmaku,
            'segments': trend_df.to_dict('records') if len(trend_df) > 0 else [],
            'heatmap_data': heatmap_data,
            'curve_data': curve_data,
            'peaks': peaks,
            'keywords': keywords,
            'sentiment_stats': get_sentiment_stats(sentiment_df) if len(sentiment_df) > 0 else {}
        }
        
        # ==================== 位置4：保存分析结果 ====================
        print(f"💾 保存分析结果到数据库: {bvid}")
        try:
            db.save_analysis_result(bvid, result)
            print(f"✅ 分析结果保存成功: {bvid}")
        except Exception as e:
            print(f"❌ 保存分析结果失败: {e}")
            raise
        
        # 9. 完成 (100%)
        analysis_tasks[task_id]['progress'] = 100
        analysis_tasks[task_id]['status'] = 'completed'
        analysis_tasks[task_id]['message'] = '分析完成'
        analysis_tasks[task_id]['result'] = result
        
        # ==================== 位置5：完成任务 ====================
        db.complete_task(task_id)
        print(f"✅ 任务完成: {task_id}")
        print(f"{'='*60}\n")

    except Exception as e:
        # ==================== 位置6：任务失败处理 ====================
        analysis_tasks[task_id]['status'] = 'failed'
        analysis_tasks[task_id]['message'] = f'分析失败: {str(e)}'
        print(f"分析任务失败: {e}")
        
        # 数据库中也标记失败
        try:
            db.fail_task(task_id, str(e))
        except:
            pass

def generate_trend_data(barrage_df: pd.DataFrame, sentiment_df: pd.DataFrame, segment: int) -> pd.DataFrame:
    """基于 BERT 预测结果，计算情感趋势分段统计"""
    import pandas as pd
    
    if len(barrage_df) == 0 or len(sentiment_df) == 0:
        return pd.DataFrame()
    
    # 合并时间和情感标签 (确保索引对齐)
    df = pd.concat([barrage_df[['time']], sentiment_df['tag']], axis=1)
    
    # 计算时间段
    df['time_segment'] = (df['time'] // segment) * segment
    
    # 分组统计
    stats = df.groupby('time_segment')['tag'].value_counts().unstack(fill_value=0)
    
    # 确保列存在
    for col in ['positive', 'neutral', 'negative']:
        if col not in stats.columns:
            stats[col] = 0
            
    stats['total'] = stats.sum(axis=1)
    
    # 组装成旧格式，兼容后面的 identify_peaks 等函数
    trend_data = []
    for time_seg, row in stats.iterrows():
        start = int(time_seg)
        end = start + segment
        trend_data.append({
            'segment_range': f"{start}-{end}",
            'positive': int(row['positive']),
            'neutral': int(row['neutral']),
            'negative': int(row['negative']),
            'total': int(row['total'])
        })
        
    return pd.DataFrame(trend_data)
async def run_bert_analysis_task(task_id: str, bvid: str, url: str, segment: int):
    """BERT 异步分析任务（数据流极简版）"""
    print(f"\n{'='*60}")
    print(f"🚀 开始 BERT 分析任务: {task_id}")
    print(f"📹 视频BV号: {bvid}")
    print(f"{'='*60}")
        
    try:
        bert_analysis_tasks[task_id]['status'] = 'processing'
        bert_analysis_tasks[task_id]['message'] = '开始 BERT 分析...'
            
        headers = DEFAULT_HEADERS
            
        # ==========================================
        # 阶段 1：获取数据（统一列名为 'time' 和 'content'）
        # ==========================================
        bert_analysis_tasks[task_id]['progress'] = 10
        danmakus_from_db = db.get_danmakus(bvid, limit=10000)
            
        barrage = None
        if danmakus_from_db and len(danmakus_from_db) > 0:
            print(f"📥 从数据库获取到 {len(danmakus_from_db)} 条弹幕")
            barrage = pd.DataFrame([
                {'time': d['time_point'], 'content': d['content']}
                for d in danmakus_from_db
            ])
        else:
            print("⚠️ 数据库无弹幕，调用爬虫...")
            bert_analysis_tasks[task_id]['message'] = '正在爬取弹幕...'
            from utils.crawler import get_barrage
            barrage = get_barrage(url=url, headers=headers, type_='Video')
            # 爬虫返回的列名本身就是 'time'，什么都不用改！
            
        if barrage is None or len(barrage) == 0:
            raise Exception("未获取到弹幕数据")
            
        # ==========================================
        # 阶段 2：强制写入视频信息（解决外键约束）
        # ==========================================
        print("💾 确保视频信息存在...")
        video_info = {
            'bvid': bvid,
            'title': f'视频 {bvid}',
            'up_name': '未知UP主',
            'duration': int(barrage['time'].max()) if len(barrage) > 0 else 0,
            'cover_url': ''
        }
        try:
            from api.video import fetch_video_info_from_bilibili
            api_info = fetch_video_info_from_bilibili(bvid, headers)
            if api_info:
                video_info.update({
                    'title': api_info.get('title', video_info['title']),
                    'up_name': api_info.get('up_name', video_info['up_name']),
                    'cover_url': api_info.get('cover_url', ''),
                    'duration': api_info.get('duration', video_info['duration'])
                })
        except Exception as e:
            print(f"⚠️ 获取视频详细信息失败: {e}")
            
        db.save_video(video_info) # 无论是新视频还是旧视频，执行一次确保安全

        # ==========================================
        # 阶段 3：BERT 核心预测
        # ==========================================
        print("🧠 使用 BERT 模型进行情感分析...")
        bert_analysis_tasks[task_id]['progress'] = 30
        bert_analysis_tasks[task_id]['message'] = '正在使用 BERT 进行情感分析...'
            
        from models.bert_model import get_bert_model
        bert_model = get_bert_model()
        if bert_model is None or bert_model.model is None:
            raise Exception("BERT 模型不可用")
            
        content_list = barrage['content'].fillna('').tolist()
        bert_results = bert_model.predict_batch(content_list)
            
        sentiment_df = pd.DataFrame([
            {'tag': r['sentiment_tag'], 'score': r['sentiment_score']} 
            for r in bert_results
        ])
            
        pos_cnt = sum(1 for t in sentiment_df['tag'] if t == 'positive')
        neg_cnt = sum(1 for t in sentiment_df['tag'] if t == 'negative')
        print(f"✅ BERT 预测完成: 积极{pos_cnt}条, 中性{len(sentiment_df)-pos_cnt-neg_cnt}条, 消极{neg_cnt}条")

        # ==========================================
        # 阶段 4：保存弹幕（列名完美对齐，无需 rename）
        # ==========================================
        print("💾 保存弹幕和情感数据...")
        bert_analysis_tasks[task_id]['progress'] = 45
        db.save_danmakus(bvid, barrage, sentiment_df) # barrage 现在绝对是 'time' 列，完美对接！

        # ==========================================
        # 阶段 5：生成图表数据（修正了函数名）
        # ==========================================
        bert_analysis_tasks[task_id]['progress'] = 55
        trend_df = generate_trend_data(barrage, sentiment_df, segment) # 去掉了错误的 _from_df
            
        bert_analysis_tasks[task_id]['progress'] = 65
        heatmap_data = generate_heatmap_data(barrage, sentiment_df, segment)
            
        bert_analysis_tasks[task_id]['progress'] = 75
        curve_data = generate_curve_data(trend_df)
            
        bert_analysis_tasks[task_id]['progress'] = 85
        peaks = identify_peaks(trend_df)

        # ==========================================
        # 阶段 6：提取关键词（基于 BERT 结果，不用旧模型）
        # ==========================================
        print("🔑 提取关键词...")
        bert_analysis_tasks[task_id]['progress'] = 95
            
        import jieba.analyse
        import os
        stopwords_path = os.path.join(os.path.dirname(__file__), '..', '..', 'stopwords.txt')
        if os.path.exists(stopwords_path):
            jieba.analyse.set_stop_words(stopwords_path)
            
        # 提取积极弹幕的原始文本            
        pos_indices = sentiment_df[sentiment_df['tag'] == 'positive'].index.tolist()
        pos_text = '\n'.join([content_list[i] for i in pos_indices if i < len(content_list)])
        # 提取消极弹幕的原始文本
        neg_indices = sentiment_df[sentiment_df['tag'] == 'negative'].index.tolist()
        neg_text = '\n'.join([content_list[i] for i in neg_indices if i < len(content_list)])
            
        keywords = {
            'positive': [kw for kw in jieba.analyse.textrank(pos_text, topK=10, withWeight=False) if len(kw) > 1][:10] if pos_text else [],
            'negative': [kw for kw in jieba.analyse.textrank(neg_text, topK=10, withWeight=False) if len(kw) > 1][:10] if neg_text else []
        }

        # ==========================================
        # 阶段 7：组装并保存结果
        # ==========================================
        print("📦 组装结果...")
        from models.sentiment import get_sentiment_stats
        result = {
            'bvid': bvid,
            'total_danmaku': len(barrage),
            'segments': trend_df.to_dict('records') if len(trend_df) > 0 else [],
            'heatmap_data': heatmap_data,
            'curve_data': curve_data,
            'peaks': peaks,
            'keywords': keywords,
            'sentiment_stats': get_sentiment_stats(sentiment_df) if len(sentiment_df) > 0 else {}
        }
            
        try:
            db.save_analysis_result(bvid, result)
            print(f"✅ 分析结果保存成功: {bvid}")
        except Exception as e:
            print(f"❌ 保存分析结果失败: {e}")
            
        # 完成
        bert_analysis_tasks[task_id]['progress'] = 100
        bert_analysis_tasks[task_id]['status'] = 'completed'
        bert_analysis_tasks[task_id]['message'] = 'BERT 分析完成'
        bert_analysis_tasks[task_id]['result'] = result
        db.complete_task(task_id)
        print(f"✅ 任务完成: {task_id}\n{'='*60}\n")
    
    except Exception as e:
        bert_analysis_tasks[task_id]['status'] = 'failed'
        bert_analysis_tasks[task_id]['message'] = f'BERT 分析失败: {str(e)}'
        print(f"BERT 分析任务失败: {e}")
        try:
            db.fail_task(task_id, str(e))
        except:
            pass

# ==================== BERT API 接口 ====================

# BERT 任务存储
bert_analysis_tasks = {}


class BertAnalysisRequest(BaseModel):
    url: str
    segment: int = 15


class BertAnalysisResponse(BaseModel):
    task_id: str
    bvid: str
    status: str
    message: str
    progress: int = 0


@router.post("/analyze/bert", response_model=BertAnalysisResponse)
async def analyze_video_with_bert(
    request: BertAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """开始 BERT 情感分析"""
    task_id = str(uuid.uuid4())
    bvid = extract_bvid(request.url)
    
    # 【新增】初始化 BERT 任务状态到字典中（OpenCode 漏掉了这步）
    bert_analysis_tasks[task_id] = {
        'task_id': task_id,
        'status': 'pending',
        'progress': 0,
        'message': 'BERT任务已提交',
        'result': None
    }
    
    background_tasks.add_task(run_bert_analysis_task, task_id, bvid, request.url, request.segment)
    
    return BertAnalysisResponse(
        task_id=task_id,
        bvid=bvid,
        status='pending',
        message='BERT 分析任务已提交',
        progress=0
    )


@router.get("/analyze/bert/status/{task_id}")
async def get_bert_analysis_status(task_id: str):
    """获取 BERT 分析任务状态"""
    if task_id not in bert_analysis_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = bert_analysis_tasks[task_id]
    return {
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message'],
        'total_danmaku': task.get('total_danmaku', 0)
    }


@router.get("/analyze/bert/result/{task_id}")
async def get_bert_analysis_result(task_id: str):
    """获取 BERT 分析结果"""
    if task_id not in bert_analysis_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = bert_analysis_tasks[task_id]
    
    if task['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"任务尚未完成")
    
    return task['result']


# ==================== API 接口 ====================

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """开始分析视频"""
    task_id = str(uuid.uuid4())
    bvid = extract_bvid(request.url)
    
    # 初始化任务状态
    analysis_tasks[task_id] = {
        'task_id': task_id,
        'url': request.url,
        'bvid': bvid,
        'status': 'pending',
        'progress': 0,
        'message': '等待开始',
        'result': None
    }
    
    # 后台运行真实分析任务
    background_tasks.add_task(run_analysis_task, task_id, request)
    
    return AnalysisResponse(
        task_id=task_id,
        bvid=bvid,
        status='pending',
        message='分析任务已提交',
        progress=0
    )

@router.get("/analyze/status/{task_id}")
async def get_analysis_status(task_id: str):
    """获取分析任务状态"""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = analysis_tasks[task_id]
    return {
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress'],
        'message': task['message'],
        'total_danmaku': task.get('total_danmaku', 0)
    }

@router.get("/analyze/result/{task_id}")
async def get_analysis_result(task_id: str):
    """获取分析结果"""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = analysis_tasks[task_id]
    
    if task['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"任务尚未完成")
    
    return task['result']

@router.post("/analyze/test")
async def test_analysis(request: AnalysisRequest):
    """测试连接和爬虫"""
    try:
        headers = request.headers if request.headers else DEFAULT_HEADERS
        
        # 测试爬虫
        barrage = get_barrage(
            url=request.url,
            headers=headers,
            type_='Video'
        )
        
        total_danmaku = len(barrage)
        bvid = extract_bvid(request.url)

        # ==================== 新增：保存测试数据到数据库 ====================
        if total_danmaku > 0:
            # 1. 保存视频信息
            video_info = {
                'bvid': bvid,
                'title': f'测试视频 {bvid}',
                'up_name': '测试UP主',
                'duration': int(barrage['time'].max()) if len(barrage) > 0 else 0,
                'cover_url': ''
            }
            
            # 从B站API获取视频详细信息
            try:
                from api.video import fetch_video_info_from_bilibili
                api_video_info = fetch_video_info_from_bilibili(bvid, headers)
                if api_video_info:
                    video_info['title'] = api_video_info.get('title', video_info['title'])
                    video_info['up_name'] = api_video_info.get('up_name', video_info['up_name'])
                    video_info['cover_url'] = api_video_info.get('cover_url', '')
                    video_info['duration'] = api_video_info.get('duration', video_info['duration'])
            except Exception as e:
                print(f"⚠️ 获取视频信息失败: {e}")
            
            db.save_video(video_info)
            
            # 2. 进行简单的情感分析并保存弹幕
            from models.sentiment import sentiment_analyse
            sentiment_df = sentiment_analyse(url=request.url, headers=headers)
            
            if len(sentiment_df) > 0:
                db.save_danmakus(bvid, barrage, sentiment_df)
                
                # 3. 保存简单的分析结果
                from models.sentiment import get_sentiment_stats
                stats = get_sentiment_stats(sentiment_df)
                
                result = {
                    'bvid': bvid,
                    'total_danmaku': total_danmaku,
                    'segments': [],
                    'heatmap_data': [],
                    'curve_data': [],
                    'peaks': {
                        'positive': {'time': 0, 'value': 0, 'description': ''},
                        'negative': {'time': 0, 'value': 0, 'description': ''},
                        'density': {'time': 0, 'count': 0}
                    },
                    'keywords': {'positive': [], 'negative': []},
                    'sentiment_stats': stats
                }
                db.save_analysis_result(bvid, result)

        return {
            'success': True,
            'bvid': extract_bvid(request.url),
            'total_danmaku': len(barrage),
            'message': '连接成功，爬虫工作正常'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")
    

# ===== 追加到 backend/api/analysis.py 末尾 =====

@router.get('/compare/curve/{bvid}')
def get_compare_curve(bvid: str):
    """
    获取双模型情感对比曲线数据
    注意：这里需要查询数据库获取弹幕，请根据你的实际表名和字段调整 SQL
    """
    import time
    
    # 1. 从数据库获取弹幕 (⚠️请根据你的实际数据库表结构调整这里)
    from utils.database import SessionLocal
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        # 假设你的弹幕表叫 danmakus，包含 bvid, time(秒), content 字段
        # 如果字段名不同，请修改下面的 SQL
        sql = text("SELECT time, content FROM danmakus WHERE bvid = :bvid ORDER BY time")
        result = db.execute(sql, {"bvid": bvid})
        danmakus = [{"time": float(row[0]), "content": row[1]} for row in result]
    finally:
        db.close()

    if not danmakus:
        return {"error": "未找到弹幕数据，请先使用单模型分析一次该视频以抓取弹幕"}

    # 2. 准备模型
    SnowNLP = _get_snownlp()
    bert_classifier = _get_bert()
    
    # 3. 分段计算 (每10秒一段)
    max_time = danmakus[-1]['time']
    segment_size = 10
    curve_data = []
    
    # BERT标签映射
    bert_label_map = {'positive': True, '1': True, 'LABEL_1': True}
    
    for start_time in range(0, int(max_time) + segment_size, segment_size):
        end_time = start_time + segment_size
        
        # 筛选当前时间段的弹幕
        seg_texts = [d['content'] for d in danmakus if start_time <= d['time'] < end_time]
        
        if not seg_texts:
            # 没有弹幕的时段补中间值 0.5
            curve_data.append({"time": start_time, "snownlp": 0.5, "bert": 0.5})
            continue
            
        # --- 计算 SnowNLP 平均分 ---
        snow_scores = [SnowNLP(text).sentiments for text in seg_texts]
        avg_snow = sum(snow_scores) / len(snow_scores)
        
        # --- 计算 BERT 平均分 ---
        # pipeline 支持直接传入 list 进行批量预测，速度比循环快得多
        bert_results = bert_classifier(seg_texts)
        bert_score_sum = 0
        for r in bert_results:
            score = r['score']
            # 如果是正面标签，score就是正面概率；如果是负面标签，用 1-score 转换
            is_positive = bert_label_map.get(r['label'], False)
            bert_score_sum += score if is_positive else (1 - score)
        avg_bert = bert_score_sum / len(bert_results)
        
        curve_data.append({
            "time": start_time,
            "snownlp": round(avg_snow, 4),
            "bert": round(avg_bert, 4)
        })
        
    return {"curve_data": curve_data}

# ===== 追加到 backend/api/analysis.py 最末尾 =====

class CompareAnalyzeReq(BaseModel):
    url: str

# 局部模型缓存（避免重复加载）
_compare_cache = {'snownlp': None, 'bert': None}

def _get_snow():
    if _compare_cache['snownlp'] is None:
        from snownlp import SnowNLP
        _compare_cache['snownlp'] = SnowNLP
    return _compare_cache['snownlp']

def _get_bert_pipe():
    if _compare_cache['bert'] is None:
        from transformers import pipeline
        _compare_cache['bert'] = pipeline(
            'sentiment-analysis',
            model='./models/bert_sentiment',  # 用你本地已有的模型路径
            device=-1
        )
    return _compare_cache['bert']

@router.post('/analyze/compare')
def analyze_compare(req: CompareAnalyzeReq):
    """
    对比模式专用接口：拉取弹幕，分别用两个模型算分，返回双曲线数据
    """
    import re
    
    # 1. 提取BV号
    match = re.search(r'BV\w{10}', req.url)
    if not match:
        return {"error": "无效的BV号"}
    bvid = match.group(0)

    # 2. 查数据库拿弹幕（使用你项目原有的 db 实例）
    from utils.database import db
    # 给一个足够大的 limit 确保拿到所有弹幕
    danmakus = db.get_danmakus(bvid, limit=100000)

    if not danmakus:
        return {"error": "未找到弹幕，请先用单模型分析一次该视频"}

    # 3. 加载模型
    SnowNLP = _get_snow()
    bert_classifier = _get_bert_pipe()
    bert_label_map = {'positive': True, '1': True, 'LABEL_1': True}

        # 4. 批量计算 + 统计分布 (极致提速版)
    import random
    
    max_time = max([d['time_point'] for d in danmakus])
    segment_size = 10
    curve_data = []
    
    # 用于统计分布的计数器
    snow_dist = {'positive': 0, 'negative': 0, 'neutral': 0}
    bert_dist = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    # 准备工作：收集所有需要跑 BERT 的文本，记录它们属于哪个时间段
    all_bert_texts = []
    time_mapping = []
    
    for start_time in range(0, int(max_time) + segment_size, segment_size):
        end_time = start_time + segment_size
        seg_texts = [d['content'] for d in danmakus if start_time <= d['time_point'] < end_time]
        
        if not seg_texts:
            curve_data.append({"time": start_time, "snownlp": 0.5, "bert": 0.5})
            continue
            
        # 抽样 (两个模型用同一批样本，保证对比绝对公平)
        sample_texts = random.sample(seg_texts, min(15, len(seg_texts)))
        
        # --- 算 SnowNLP ---
        snow_scores = [SnowNLP(text).sentiments for text in sample_texts]
        avg_snow = sum(snow_scores) / len(snow_scores)
        curve_data.append({"time": start_time, "snownlp": round(avg_snow, 4), "bert": 0}) # bert先占0
        
        # SnowNLP 分布统计 (>0.6正, <0.4负, 中间中性)
        for score in snow_scores:
            if score > 0.6: snow_dist['positive'] += 1
            elif score < 0.4: snow_dist['negative'] += 1
            else: snow_dist['neutral'] += 1
            
        # 收集 BERT 待测文本
        for t in sample_texts:
            all_bert_texts.append(t)
            time_mapping.append(start_time)

    # --- 极速核心：一次性批量跑 BERT ---
    if all_bert_texts:
        bert_results = bert_classifier(all_bert_texts)
        bert_segment_scores = {} # 按时间段收集分数
        
        for i, r in enumerate(bert_results):
            t = time_mapping[i]
            is_positive = bert_label_map.get(r['label'], False)
            score = r['score'] if is_positive else (1 - r['score'])
            
            # BERT 分布统计 (置信度低算中性)
            if score > 0.6: bert_dist['positive'] += 1
            elif score < 0.4: bert_dist['negative'] += 1
            else: bert_dist['neutral'] += 1
            
            if t not in bert_segment_scores:
                bert_segment_scores[t] = []
            bert_segment_scores[t].append(score)
            
        # 将 BERT 结果填回 curve_data
        for item in curve_data:
            t = item['time']
            if t in bert_segment_scores:
                scores = bert_segment_scores[t]
                item['bert'] = round(sum(scores) / len(scores), 4)

    return {
        "curve_data": curve_data,
        "distribution": { "snownlp": snow_dist, "bert": bert_dist }
    }