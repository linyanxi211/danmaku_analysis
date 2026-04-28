"""
视频信息API模块 - 处理视频基本信息
"""
import re
import requests
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from utils.crawler import get_barrage
from utils.helpers import get_xml_url, get_bvid_from_url
from utils.database import db

router = APIRouter()

# ==================== 请求/响应模型 ====================

class VideoInfo(BaseModel):
    """视频信息模型"""
    bvid: str
    title: str
    up_name: str
    up_mid: Optional[int] = None
    duration: int
    cover_url: str
    description: Optional[str] = None
    pubdate: Optional[int] = None
    view_count: Optional[int] = None
    danmaku_count: Optional[int] = None
    like_count: Optional[int] = None
    coin_count: Optional[int] = None
    favorite_count: Optional[int] = None
    share_count: Optional[int] = None

class VideoParseRequest(BaseModel):
    """解析视频请求"""
    url: str

class VideoParseResponse(BaseModel):
    """解析视频响应"""
    bvid: str
    title: str
    up_name: str
    cover_url: str
    duration: int
    success: bool
    message: str

class VideoListResponse(BaseModel):
    """视频列表响应"""
    total: int
    videos: List[Dict]

# ==================== 辅助函数 ====================

def fetch_video_info_from_bilibili(bvid: str, headers: Dict) -> Optional[Dict]:
    """
    从B站API获取视频详细信息
    """
    try:
        # B站API接口
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if data.get('code') != 0:
            return None
        
        info = data['data']
        
        # 解析UP主信息
        owner = info.get('owner', {})
        
        # 解析视频信息
        video_info = {
            'bvid': bvid,
            'title': info.get('title', ''),
            'up_name': owner.get('name', '未知'),
            'up_mid': owner.get('mid'),
            'duration': info.get('duration', 0),
            'cover_url': info.get('pic', ''),
            'description': info.get('desc', ''),
            'pubdate': info.get('pubdate', 0),
            'view_count': info.get('stat', {}).get('view', 0),
            'danmaku_count': info.get('stat', {}).get('danmaku', 0),
            'like_count': info.get('stat', {}).get('like', 0),
            'coin_count': info.get('stat', {}).get('coin', 0),
            'favorite_count': info.get('stat', {}).get('favorite', 0),
            'share_count': info.get('stat', {}).get('share', 0)
        }
        
        return video_info
        
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return None

def get_video_title_from_page(bvid: str, headers: Dict) -> str:
    """
    从视频页面解析标题（备用方案）
    """
    try:
        url = f"https://www.bilibili.com/video/{bvid}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return f"视频 {bvid}"
        
        # 尝试从HTML中提取标题
        html = response.text
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
        if title_match:
            title = title_match.group(1)
            # 移除 " _哔哩哔哩_bilibili" 后缀
            title = re.sub(r'\s*_哔哩哔哩_bilibili$', '', title)
            return title
        
        return f"视频 {bvid}"
        
    except Exception as e:
        print(f"从页面解析标题失败: {e}")
        return f"视频 {bvid}"

# ==================== API接口 ====================

@router.get("/video/{bvid}", response_model=VideoInfo)
async def get_video_info(bvid: str):
    """
    获取视频详细信息
    
    优先从数据库查询，如果没有则从B站API获取并保存
    """
    # 1. 先从数据库查询
    video = db.get_video(bvid)
    if video:
        return VideoInfo(**video)
    
    # 2. 数据库中没有，从B站API获取
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com',
    }
    
    video_info = fetch_video_info_from_bilibili(bvid, headers)
    
    if video_info:
        # 保存到数据库
        db.save_video(video_info)
        return VideoInfo(**video_info)
    
    # 3. API失败，尝试从页面解析基本信息
    title = get_video_title_from_page(bvid, headers)
    
    # 获取弹幕以估算时长
    try:
        barrage = get_barrage(
            url=f"https://www.bilibili.com/video/{bvid}",
            headers=headers,
            type_='Video'
        )
        duration = int(barrage['time'].max()) if len(barrage) > 0 else 0
    except:
        duration = 0
    
    basic_info = {
        'bvid': bvid,
        'title': title,
        'up_name': '未知',
        'duration': duration,
        'cover_url': f"https://i0.hdslb.com/bfs/archive/{bvid}.jpg"
    }
    
    # 保存基本信息
    db.save_video(basic_info)
    
    return VideoInfo(**basic_info)

@router.post("/video/parse", response_model=VideoParseResponse)
async def parse_video_url(request: VideoParseRequest):
    """
    解析视频URL，获取BV号和基本信息
    """
    try:
        # 从URL提取BV号
        bvid = get_bvid_from_url(request.url)
        
        # 获取视频信息
        video_info = await get_video_info(bvid)
        
        return VideoParseResponse(
            bvid=bvid,
            title=video_info.title,
            up_name=video_info.up_name,
            cover_url=video_info.cover_url,
            duration=video_info.duration,
            success=True,
            message="解析成功"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")

@router.get("/videos", response_model=VideoListResponse)
async def get_video_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词")
):
    """
    获取视频列表（分页）
    """
    # 这里需要从数据库查询，暂时返回模拟数据
    # TODO: 实现数据库分页查询
    
    # 模拟数据
    mock_videos = [
        {
            'bvid': 'BV1GJ411x7h7',
            'title': '【罗翔说刑法】',
            'up_name': '罗翔说刑法',
            'duration': 1200,
            'cover_url': 'https://i0.hdslb.com/bfs/archive/xxx.jpg',
            'danmaku_count': 12345
        },
        {
            'bvid': 'BV1vs411M7aT',
            'title': '老师好我叫何同学',
            'up_name': '老师好我叫何同学',
            'duration': 900,
            'cover_url': 'https://i0.hdslb.com/bfs/archive/xxx.jpg',
            'danmaku_count': 23456
        }
    ]
    
    return VideoListResponse(
        total=2,
        videos=mock_videos
    )

@router.get("/video/{bvid}/basic")
async def get_basic_video_info(bvid: str):
    """
    获取视频基本信息（轻量级，适合列表展示）
    如果数据库中没有封面，自动从B站API获取
    """
    video = db.get_video(bvid)
    
    if video:
        # 如果数据库中没有封面URL，尝试从B站API获取
        if not video.get('cover_url'):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com',
            }
            api_info = fetch_video_info_from_bilibili(bvid, headers)
            if api_info and api_info.get('cover_url'):
                video['cover_url'] = api_info['cover_url']
                # 更新数据库
                db.save_video(video)
        
        return {
            'bvid': video['bvid'],
            'title': video['title'],
            'up_name': video['up_name'],
            'cover_url': video.get('cover_url', ''),
            'duration': video.get('duration', 0)
        }
    
    raise HTTPException(status_code=404, detail="视频不存在")

@router.get("/video/{bvid}/stats")
async def get_video_stats(bvid: str):
    """
    获取视频统计信息（播放量、弹幕数等）
    """
    # 从数据库获取分析结果中的统计信息
    result = db.get_analysis_result(bvid)
    
    if result:
        return {
            'bvid': bvid,
            'total_danmaku': result.get('total_danmaku', 0),
            'avg_sentiment': result.get('sentiment_stats', {}).get('avg_score', 0),
            'positive_ratio': result.get('sentiment_stats', {}).get('positive_ratio', 0),
            'analyzed_at': result.get('analyzed_at')
        }
    
    # 如果没有分析结果，返回基本信息
    video = db.get_video(bvid)
    if video:
        return {
            'bvid': bvid,
            'total_danmaku': 0,
            'avg_sentiment': 0,
            'positive_ratio': 0,
            'message': '该视频尚未分析'
        }
    
    raise HTTPException(status_code=404, detail="视频不存在")

@router.delete("/video/{bvid}")
async def delete_video(bvid: str):
    """
    删除视频及其相关数据
    """
    # TODO: 实现删除功能
    return {"message": f"视频 {bvid} 删除成功"}