"""
弹幕数据管理API模块 - 处理弹幕的查询、导出和统计
"""
import csv
import json
import pandas as pd
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, field_serializer
import io
from datetime import datetime

from utils.database import db

router = APIRouter()

# ==================== 请求/响应模型 ====================

class DanmakuItem(BaseModel):
    """弹幕项模型"""
    id: int
    bvid: str
    time_point: float
    content: str
    sentiment_score: float
    sentiment_tag: str
    created_at: datetime

    # 添加序列化器，将 datetime 转换为字符串
    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    class Config:
        from_attributes = True  # 允许从ORM模型创建

class DanmakuListResponse(BaseModel):
    """弹幕列表响应"""
    total: int
    page: int
    page_size: int
    items: List[DanmakuItem]

class DanmakuStatsResponse(BaseModel):
    """弹幕统计响应"""
    bvid: str
    total_count: int
    time_range: Dict[str, float]
    sentiment_distribution: Dict[str, int]
    avg_sentiment: float
    top_keywords: List[str]

class SegmentDanmakuRequest(BaseModel):
    """时间段弹幕请求"""
    bvid: str
    start: float
    end: float

# ==================== API接口 ====================

@router.get("/danmaku/{bvid}", response_model=DanmakuListResponse)
async def get_danmakus(
    bvid: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页数量"),
    sentiment: Optional[str] = Query(None, description="情感过滤：positive/neutral/negative"),
    sort_by: str = Query("time_point", description="排序字段：time_point/sentiment_score"),
    order: str = Query("asc", description="排序方向：asc/desc")
):
    """
    获取弹幕列表（支持分页、过滤、排序）
    """
    try:
        # 构建基础查询
        sql = "SELECT * FROM danmakus WHERE bvid = %s"
        params = [bvid]
        
        # 情感过滤
        if sentiment and sentiment in ['positive', 'neutral', 'negative']:
            sql += " AND sentiment_tag = %s"
            params.append(sentiment)
        
        # 获取总数
        count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as temp"
        with db.get_cursor() as cursor:
            cursor.execute(count_sql, tuple(params))
            total = cursor.fetchone()['total']
        
        # 排序
        if sort_by in ['time_point', 'sentiment_score']:
            sql += f" ORDER BY {sort_by} {order.upper()}"
        
        # 分页
        sql += " LIMIT %s OFFSET %s"
        params.extend([page_size, (page - 1) * page_size])
        
        # 执行查询
        with db.get_cursor() as cursor:
            cursor.execute(sql, tuple(params))
            items = cursor.fetchall()
        
        return DanmakuListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[DanmakuItem(**item) for item in items]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取弹幕失败: {str(e)}")

@router.get("/danmaku/{bvid}/segment")
async def get_danmakus_by_segment(
    bvid: str,
    start: float = Query(..., description="开始时间(秒)"),
    end: float = Query(..., description="结束时间(秒)"),
    limit: int = Query(1000, le=5000, description="返回数量限制")
):
    """
    获取指定时间段的弹幕
    """
    try:
        sql = """
        SELECT * FROM danmakus 
        WHERE bvid = %s AND time_point BETWEEN %s AND %s
        ORDER BY time_point
        LIMIT %s
        """
        
        with db.get_cursor() as cursor:
            cursor.execute(sql, (bvid, start, end, limit))
            items = cursor.fetchall()
        
        # 计算该时段的统计信息
        if items:
            sentiments = [item['sentiment_tag'] for item in items]
            avg_score = sum(item['sentiment_score'] for item in items) / len(items)
            
            stats = {
                'total': len(items),
                'time_range': f"{start}-{end}",
                'avg_sentiment': round(avg_score, 3),
                'sentiment_distribution': {
                    'positive': sentiments.count('positive'),
                    'neutral': sentiments.count('neutral'),
                    'negative': sentiments.count('negative')
                }
            }
        else:
            stats = {
                'total': 0,
                'time_range': f"{start}-{end}",
                'avg_sentiment': 0,
                'sentiment_distribution': {
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                }
            }
        
        return {
            'bvid': bvid,
            'segment': stats,
            'danmakus': items[:100]  # 最多返回100条详细弹幕
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时段弹幕失败: {str(e)}")

@router.get("/danmaku/{bvid}/stats", response_model=DanmakuStatsResponse)
async def get_danmaku_stats(bvid: str):
    """
    获取弹幕统计信息
    """
    try:
        # 获取总数和情感分布
        sql = """
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN sentiment_tag = 'positive' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN sentiment_tag = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
            SUM(CASE WHEN sentiment_tag = 'negative' THEN 1 ELSE 0 END) as negative_count,
            AVG(sentiment_score) as avg_sentiment,
            MIN(time_point) as min_time,
            MAX(time_point) as max_time
        FROM danmakus 
        WHERE bvid = %s
        """
        
        with db.get_cursor() as cursor:
            cursor.execute(sql, (bvid,))
            stats = cursor.fetchone()
        
        if not stats or stats['total_count'] == 0:
            return DanmakuStatsResponse(
                bvid=bvid,
                total_count=0,
                time_range={'min': 0, 'max': 0},
                sentiment_distribution={'positive': 0, 'neutral': 0, 'negative': 0},
                avg_sentiment=0,
                top_keywords=[]
            )
        
        # 获取热门关键词（从分析结果表）
        keywords = []
        result = db.get_analysis_result(bvid)
        if result and result.get('keywords_data'):
            keywords_data = result['keywords_data']
            if isinstance(keywords_data, dict):
                keywords = keywords_data.get('positive', [])[:5] + keywords_data.get('negative', [])[:5]
        
        return DanmakuStatsResponse(
            bvid=bvid,
            total_count=stats['total_count'],
            time_range={
                'min': float(stats['min_time']),
                'max': float(stats['max_time'])
            },
            sentiment_distribution={
                'positive': int(stats['positive_count']),
                'neutral': int(stats['neutral_count']),
                'negative': int(stats['negative_count'])
            },
            avg_sentiment=round(float(stats['avg_sentiment']), 3) if stats['avg_sentiment'] else 0,
            top_keywords=keywords
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/danmaku/{bvid}/export")
async def export_danmakus(
    bvid: str,
    format: str = Query("json", description="导出格式：json/csv"),
    sentiment: Optional[str] = Query(None, description="情感过滤")
):
    """
    导出弹幕数据（JSON/CSV格式）
    """
    try:
        # 构建查询
        sql = "SELECT * FROM danmakus WHERE bvid = %s"
        params = [bvid]
        
        if sentiment and sentiment in ['positive', 'neutral', 'negative']:
            sql += " AND sentiment_tag = %s"
            params.append(sentiment)
        
        sql += " ORDER BY time_point"
        
        # 执行查询
        with db.get_cursor() as cursor:
            cursor.execute(sql, tuple(params))
            items = cursor.fetchall()
        
        if not items:
            raise HTTPException(status_code=404, detail="没有找到弹幕数据")
        
        if format == 'json':
            # 返回JSON格式
            return {
                'bvid': bvid,
                'total': len(items),
                'danmakus': items
            }
            
        elif format == 'csv':
            # 生成CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow(['时间(秒)', '弹幕内容', '情感得分', '情感标签'])
            
            # 写入数据
            for item in items:
                writer.writerow([
                    item['time_point'],
                    item['content'],
                    item['sentiment_score'],
                    item['sentiment_tag']
                ])
            
            # 返回CSV文件
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={bvid}_danmakus.csv"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@router.get("/danmaku/{bvid}/search")
async def search_danmakus(
    bvid: str,
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200)
):
    """
    搜索包含关键词的弹幕
    """
    try:
        # 模糊搜索
        sql = """
        SELECT * FROM danmakus 
        WHERE bvid = %s AND content LIKE %s
        ORDER BY time_point
        LIMIT %s OFFSET %s
        """
        
        # 获取总数
        count_sql = """
        SELECT COUNT(*) as total FROM danmakus 
        WHERE bvid = %s AND content LIKE %s
        """
        
        search_pattern = f"%{keyword}%"
        
        with db.get_cursor() as cursor:
            cursor.execute(count_sql, (bvid, search_pattern))
            total = cursor.fetchone()['total']
            
            cursor.execute(sql, (bvid, search_pattern, page_size, (page - 1) * page_size))
            items = cursor.fetchall()
        
        return {
            'bvid': bvid,
            'keyword': keyword,
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': items
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.delete("/danmaku/{bvid}")
async def delete_danmakus(
    bvid: str,
    start: Optional[float] = Query(None, description="删除起始时间"),
    end: Optional[float] = Query(None, description="删除结束时间")
):
    """
    删除弹幕数据（支持按时间段删除）
    """
    try:
        if start is not None and end is not None:
            # 删除指定时间段
            sql = "DELETE FROM danmakus WHERE bvid = %s AND time_point BETWEEN %s AND %s"
            params = (bvid, start, end)
        else:
            # 删除全部
            sql = "DELETE FROM danmakus WHERE bvid = %s"
            params = (bvid,)
        
        with db.get_cursor() as cursor:
            cursor.execute(sql, params)
            deleted_count = cursor.rowcount
        
        return {
            'bvid': bvid,
            'deleted_count': deleted_count,
            'message': f'成功删除 {deleted_count} 条弹幕'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")