"""
B站弹幕爬虫模块
"""
import re
import time
import requests
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
from bs4 import BeautifulSoup
from .helpers import get_xml_url, get_bvid_from_url
import jieba
import jieba.analyse


def get_barrage(
        url: str,
        headers: Dict[str, str],
        type_: str = 'Video',
        max_retries: int = 3
) -> pd.DataFrame:
    """
    获取B站弹幕数据
    
    Args:
        url: B站视频URL
        headers: 请求头
        type_: 'Video' 返回视频时间点，'Real' 返回真实时间戳
        max_retries: 最大重试次数
    
    Returns:
        DataFrame: 包含time和content两列的弹幕数据
    """
    for attempt in range(max_retries):
        try:
            # 获取XML URL
            xml_url = get_xml_url(url=url, headers=headers)
            
            # 请求弹幕XML
            response = requests.get(
                xml_url,
                headers=headers,
                timeout=10
            )
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            xml = response.text
            
            # 解析XML
            soup = BeautifulSoup(xml, 'xml')
            content_all = soup.find_all(name='d')
            
            if not content_all:
                # 尝试用'lxml'解析
                soup = BeautifulSoup(xml, 'lxml')
                content_all = soup.find_all(name='d')
            
            timeList = []
            contentList = []
            
            for comment in content_all:
                try:
                    # 获取弹幕属性
                    p_attr = comment.attrs.get('p', '')
                    if not p_attr:
                        continue
                    
                    data = p_attr.split(',')
                    
                    if type_ == 'Video':
                        # 视频内时间点（秒）
                        time_val = float(data[0]) if len(data) > 0 else 0
                    elif type_ == 'Real':
                        # 真实时间戳
                        time_stamp = data[4] if len(data) > 4 else '0'
                        time_val = pd.to_datetime(int(time_stamp), unit='s')
                    else:
                        raise TypeError(f'{type_} is not defined. Available method are Video, Real.')
                    
                    text = comment.text.strip()
                    
                    if text:  # 只添加非空弹幕
                        timeList.append(time_val)
                        contentList.append(text)
                        
                except Exception as e:
                    continue  # 跳过解析失败的弹幕
            
            # 创建DataFrame
            barrage = pd.DataFrame({
                'time': timeList,
                'content': contentList
            })
            
            print(f"成功获取 {len(barrage)} 条弹幕")
            return barrage
            
        except Exception as e:
            print(f"第{attempt+1}次尝试失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                print("所有重试都失败，返回空DataFrame")
                return pd.DataFrame(columns=['time', 'content'])


def barrage_num(
    barrage_times: pd.Series,
    segment: int = 15
) -> pd.DataFrame:
    """
    统计每个时间段的弹幕数量
    
    Args:
        barrage_times: 弹幕时间序列
        segment: 时间段长度（秒）
    
    Returns:
        DataFrame: 包含segment和num两列
    """
    if len(barrage_times) == 0:
        return pd.DataFrame(columns=['segment', 'num'])
    
    # 计算时间段数量
    max_time = barrage_times.max()
    num_segment = int(np.ceil(max_time / segment))
    
    segmentDict = {}
    for i in range(num_segment):
        start = i * segment
        end = (i + 1) * segment
        segment_range = f'{start}-{end}'
        segmentDict[segment_range] = 0
    
    # 统计每个时间段的弹幕数量
    for time_val in barrage_times:
        segment_idx = int(time_val // segment)
        if segment_idx < num_segment:
            start = segment_idx * segment
            end = (segment_idx + 1) * segment
            segment_range = f'{start}-{end}'
            segmentDict[segment_range] = segmentDict.get(segment_range, 0) + 1
    
    # 转换为DataFrame
    df_segment = pd.DataFrame(
        list(segmentDict.items()),
        columns=['segment', 'num']
    )
    
    return df_segment


def top_segment(
        url: str,
        headers: Dict[str, str],
        segment: int = 15
) -> Tuple[pd.DataFrame, List[str]]:
    """
    获取弹幕最多的时间段及其关键词
    
    Returns:
        Tuple[弹幕数据, 关键词列表]
    """
    # 获取弹幕
    barrage = get_barrage(
        url=url,
        headers=headers,
        type_='Video'
    )
    
    if len(barrage) == 0:
        return pd.DataFrame(), []
    
    # 统计各时间段弹幕数量
    df_segment = barrage_num(
        barrage_times=barrage['time'],
        segment=segment
    )
    
    if len(df_segment) == 0:
        return pd.DataFrame(), []
    
    # 找到弹幕最多的时段
    max_idx = df_segment['num'].idxmax()
    segment_top_range = df_segment.loc[max_idx, 'segment']
    
    # 解析时间段
    start, end = map(int, segment_top_range.split('-'))
    
    # 筛选该时段的弹幕
    select_barrage = barrage[
        (barrage['time'] >= start) & 
        (barrage['time'] <= end)
    ]
    
    # 提取关键词
    sentence = '\n'.join(select_barrage['content'])
    
    # 设置停用词
    import os
    stopwords_path = os.path.join(os.path.dirname(__file__), '..', '..', 'stopwords.txt')
    if os.path.exists(stopwords_path):
        jieba.analyse.set_stop_words(stopwords_path)
    
    # 提取关键词
    allowPOS = ('n', 'nr', 'ns', 'nz', 'v', 'vd', 'vn', 'a', 'q')
    keywords = jieba.analyse.textrank(
        sentence,
        topK=10,
        withWeight=False,
        allowPOS=allowPOS
    )
    
    return select_barrage, keywords


def barrage_keywords(
        url: str,
        headers: Dict[str, str]
) -> pd.DataFrame:
    """
    提取全文关键词
    
    Returns:
        DataFrame: 关键词及权重
    """
    # 获取弹幕
    barrage = get_barrage(
        url=url,
        headers=headers,
        type_='Video'
    )
    
    if len(barrage) == 0:
        return pd.DataFrame(columns=['key', 'weight'])
    
    # 合并所有弹幕文本
    sentence = '\n'.join(barrage['content'])
    
    # 设置停用词
    import os
    stopwords_path = os.path.join(os.path.dirname(__file__), '..', '..', 'stopwords.txt')
    if os.path.exists(stopwords_path):
        jieba.analyse.set_stop_words(stopwords_path)
    
    # 提取关键词
    allowPOS = ('n', 'nr', 'ns', 'nz', 'v', 'vd', 'vn', 'a', 'q')
    keywords = jieba.analyse.textrank(
        sentence,
        topK=20,
        withWeight=True,
        allowPOS=allowPOS
    )
    
    keywords_df = pd.DataFrame(
        keywords,
        columns=['key', 'weight']
    )
    
    return keywords_df