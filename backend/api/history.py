"""
历史记录API模块 - 管理分析历史
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from utils.database import db

router = APIRouter()

class HistoryItem(BaseModel):
    bvid: str
    title: str
    up_name: str
    analyzed_at: str
    total_danmaku: int
    avg_sentiment: float
    cover_url: Optional[str] = None

class HistoryListResponse(BaseModel):
    total: int
    items: List[HistoryItem]

@router.get("/history", response_model=HistoryListResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    keyword: Optional[str] = None
):
    """获取分析历史记录"""
    try:
        # 从数据库查询
        sql = """
        SELECT 
            v.bvid, v.title, v.up_name, v.cover_url,
            a.total_danmaku, a.avg_sentiment, a.analyzed_at
        FROM analysis_results a
        JOIN videos v ON a.bvid = v.bvid
        """
        params = []
        
        if keyword:
            sql += " WHERE v.title LIKE %s OR v.bvid LIKE %s"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        # 获取总数
        count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as temp"
        with db.get_cursor() as cursor:
            cursor.execute(count_sql, tuple(params) if params else None)
            total = cursor.fetchone()['total']
        
        # 分页
        sql += " ORDER BY a.analyzed_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, (page - 1) * page_size])
        
        with db.get_cursor() as cursor:
            cursor.execute(sql, tuple(params) if params else None)
            items = cursor.fetchall()
        
        # 格式化时间和补全封面URL
        for item in items:
            if item.get('analyzed_at'):
                item['analyzed_at'] = item['analyzed_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return HistoryListResponse(total=total, items=items)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")

@router.delete("/history/{bvid}")
async def delete_history(bvid: str):
    """删除指定历史记录"""
    try:
        # 删除分析结果（会级联删除弹幕）
        sql = "DELETE FROM analysis_results WHERE bvid = %s"
        with db.get_cursor() as cursor:
            cursor.execute(sql, (bvid,))
            deleted = cursor.rowcount
        
        if deleted == 0:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        return {"message": f"历史记录 {bvid} 已删除"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.delete("/history")
async def clear_history():
    """清空所有历史记录"""
    try:
        sql = "DELETE FROM analysis_results"
        with db.get_cursor() as cursor:
            cursor.execute(sql)
            deleted = cursor.rowcount
        
        return {"message": f"已清空 {deleted} 条历史记录"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")
    
import json # 确保顶部有导入 json

@router.get("/history/report/{bvid}")
async def get_report_detail(bvid: str):
    """获取指定视频的完整报告数据（供 Report.vue 使用）"""
    try:
        video_info = {}
        
        with db.get_cursor() as cursor:
            # 1. 查视频基础信息 (去掉了 created_at)
            cursor.execute("SELECT title, up_name, cover_url FROM videos WHERE bvid = %s", (bvid,))
            row = cursor.fetchone()
            if row:
                video_info = {
                    "title": row['title'],
                    "up": row['up_name'],
                    "cover": row['cover_url']
                }
            else:
                raise HTTPException(status_code=404, detail="找不到该视频记录")

            # 2. 查分析结果
            cursor.execute("""
                SELECT total_danmaku, avg_sentiment, positive_ratio, neutral_ratio, negative_ratio,
                       heatmap_data, curve_data, peaks_data, keywords_data
                FROM analysis_results 
                WHERE bvid = %s ORDER BY analyzed_at DESC LIMIT 1
            """, (bvid,))
            res_row = cursor.fetchone()
            
            if not res_row:
                raise HTTPException(status_code=404, detail="该视频尚未完成分析")

            # ================= 开始数据转换（注意这里的缩进，必须顶格和 with 对齐） =================
            total = res_row.get('total_danmaku', 0) or 0
            
            heatmap = json.loads(res_row['heatmap_data']) if res_row.get('heatmap_data') else []
            curve = json.loads(res_row['curve_data']) if res_row.get('curve_data') else []
            peaks_raw = json.loads(res_row['peaks_data']) if res_row.get('peaks_data') else {}
            keywords = json.loads(res_row['keywords_data']) if res_row.get('keywords_data') else {"positive": [], "negative": []}

            avg_sent = round(sum(d[1] for d in curve) / len(curve), 2) if curve else (res_row.get('avg_sentiment') or 0.5)

            def fmt_time(sec):
                return f"{int(sec)//60}:{str(int(sec)%60).zfill(2)}"

            peaks_list = [
                {"type": "positive", "icon": "🏆", "time": peaks_raw.get('positive', {}).get('time', 0), "timeText": fmt_time(peaks_raw.get('positive', {}).get('time', 0)), "value": f"情感值 {peaks_raw.get('positive', {}).get('value', 0)}条", "description": peaks_raw.get('positive', {}).get('description', ''), "samples": []},
                {"type": "negative", "icon": "💢", "time": peaks_raw.get('negative', {}).get('time', 0), "timeText": fmt_time(peaks_raw.get('negative', {}).get('time', 0)), "value": f"情感值 {peaks_raw.get('negative', {}).get('value', 0)}条", "description": peaks_raw.get('negative', {}).get('description', ''), "samples": []},
                {"type": "density", "icon": "🔥", "time": peaks_raw.get('density', {}).get('time', 0), "timeText": fmt_time(peaks_raw.get('density', {}).get('time', 0)), "value": f"{peaks_raw.get('density', {}).get('count', 0)}条弹幕", "description": "弹幕数量峰值", "samples": []}
            ]

            # 生成 30秒一段的时间分段
            time_segments = []
            if curve:
                max_time = max(d[0] for d in curve)
                segment_duration = 30 
                
                danmaku_counts = {}
                try:
                    with db.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT FLOOR(time_point / %s) * %s as segment_start, COUNT(*) as count
                            FROM danmakus WHERE bvid = %s
                            GROUP BY segment_start ORDER BY segment_start
                        """, (segment_duration, segment_duration, bvid))
                        for r in cursor.fetchall():
                            danmaku_counts[r['segment_start']] = r['count']
                except Exception as e:
                    print(f"查询分段弹幕数量失败: {e}")

                i = 0
                while i <= max_time:
                    start_time = i
                    end_time = i + segment_duration
                    seg_scores = [d[1] for d in curve if start_time <= d[0] < end_time]
                    sentiment_val = round(sum(seg_scores) / len(seg_scores), 2) if seg_scores else 0.5
                    
                    time_segments.append({
                        "segment": f"{fmt_time(start_time)}-{fmt_time(end_time)}",
                        "sentiment": sentiment_val,
                        "count": danmaku_counts.get(start_time, 0), 
                        "keywords": "详见上方词云" 
                    })
                    i += segment_duration

            # 计算真实的 distribution 数量
            pos_ratio = float(res_row.get('positive_ratio', 0) or 0)        
            neu_ratio = float(res_row.get('neutral_ratio', 0) or 0)        
            neg_ratio = float(res_row.get('negative_ratio', 0) or 0)                
            pos_count = int(total * pos_ratio / 100) if total > 0 else 0        
            neu_count = int(total * neu_ratio / 100) if total > 0 else 0        
            neg_count = int(total * neg_ratio / 100) if total > 0 else 0

            # 最终拼装返回
            return {
                "videoInfo": video_info,
                "summary": {
                    "totalDanmaku": total,
                    "avgSentiment": avg_sent,
                    "positiveRatio": round(pos_ratio, 1),
                    "peakCount": len(time_segments)
                },
                "distribution": {
                    # ⚠️ 注意这里：把写死的 0 换成了上面算出来的真实变量！
                    "positive": {"count": pos_count, "ratio": round(pos_ratio, 1)},
                    "neutral": {"count": neu_count, "ratio": round(neu_ratio, 1)},
                    "negative": {"count": neg_count, "ratio": round(neg_ratio, 1)}
                },
                "peaks": peaks_list,
                "keywords": keywords,
                "timeSegments": time_segments,
                "heatmapData": heatmap,
                "curveData": curve
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")