"""
报告生成API模块 - 处理分析报告的生成和导出
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
import pandas as pd

import io
from fastapi.responses import StreamingResponse
from fpdf import FPDF

from utils.database import db

router = APIRouter()

# ==================== 请求/响应模型 ====================

class ReportSummary(BaseModel):
    """报告摘要模型"""
    bvid: str
    title: str
    up_name: str
    analyzed_at: str
    total_danmaku: int
    avg_sentiment: float
    positive_ratio: float
    neutral_ratio: float
    negative_ratio: float

class ReportPeak(BaseModel):
    """高潮时刻模型"""
    time: int
    time_text: str
    value: int
    description: str
    samples: List[str]

class ReportData(BaseModel):
    """完整报告数据模型"""
    summary: ReportSummary
    sentiment_distribution: Dict[str, int]
    heatmap_data: List[List]
    curve_data: List[List]
    peaks: Dict[str, ReportPeak]
    keywords: Dict[str, List[str]]
    time_segments: List[Dict]
    generated_at: str
    report_id: str

class ReportListResponse(BaseModel):
    """报告列表响应"""
    total: int
    reports: List[Dict]

# ==================== 辅助函数 ====================

def format_time(seconds: int) -> str:
    """将秒数格式化为 MM:SS"""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def generate_report_id(bvid: str) -> str:
    """生成报告ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"RPT-{bvid}-{timestamp}"

def get_peak_samples(bvid: str, time_point: int, limit: int = 3) -> List[str]:
    """获取高潮时刻的示例弹幕"""
    try:
        sql = """
        SELECT content FROM danmakus 
        WHERE bvid = %s AND ABS(time_point - %s) < 5
        ORDER BY sentiment_score DESC
        LIMIT %s
        """
        with db.get_cursor() as cursor:
            cursor.execute(sql, (bvid, time_point, limit))
            results = cursor.fetchall()
            return [r['content'] for r in results if r.get('content')]
    except:
        return []

# ==================== API接口 ====================

@router.get("/report/{bvid}")
async def get_report(bvid: str):
    """
    获取视频分析报告 - 返回前端期望的数据结构
    """
    try:
        import pymysql
        import json
        from utils.database import DB_CONFIG
        
        # 直接连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 1. 获取视频信息
        print("📹 查询视频信息...")
        cursor.execute("SELECT * FROM videos WHERE bvid = %s", (bvid,))
        video = cursor.fetchone()
        print(f"   视频查询结果: {video}")

        if not video:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="视频不存在")
        
        # 2. 获取分析结果
        print("📊 查询分析结果...")
        cursor.execute("SELECT * FROM analysis_results WHERE bvid = %s", (bvid,))
        result = cursor.fetchone()
        print(f"   分析结果查询结果: {result}")
        if not result:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="分析结果不存在")
        
        print(f"✅ 查询成功，准备解析数据...")

        cursor.close()
        conn.close()
        
        # 3. 解析JSON字段
        heatmap_data = json.loads(result['heatmap_data']) if result.get('heatmap_data') else []
        curve_data = json.loads(result['curve_data']) if result.get('curve_data') else []
        peaks_data = json.loads(result['peaks_data']) if result.get('peaks_data') else {}
        keywords_data = json.loads(result['keywords_data']) if result.get('keywords_data') else {'positive': [], 'negative': []}
        
        # 4. 构建视频信息（前端期望的格式）
        videoInfo = {
            'title': video.get('title', f'视频 {bvid}'),
            'up': video.get('up_name', '未知'),
            'cover': video.get('cover_url', ''),
            'publishTime': ''
        }
        
        # 5. 构建摘要
        summary = {
            'totalDanmaku': result['total_danmaku'] or 0,
            'avgSentiment': result['avg_sentiment'] or 0,
            'positiveRatio': result['positive_ratio'] or 0,
            'peakCount': 0
        }
        
        # 6. 情感分布（前端期望的格式）
        total = result['total_danmaku'] or 0
        distribution = {
            'positive': {
                'count': int(total * (result['positive_ratio'] or 0) / 100),
                'ratio': result['positive_ratio'] or 0
            },
            'neutral': {
                'count': int(total * (result['neutral_ratio'] or 0) / 100),
                'ratio': result['neutral_ratio'] or 0
            },
            'negative': {
                'count': int(total * (result['negative_ratio'] or 0) / 100),
                'ratio': result['negative_ratio'] or 0
            }
        }
        
        # 7. 组装高潮时刻（前端期望的格式）
        peaks = []
        for peak_type in ['positive', 'negative', 'density']:
            peak_data = peaks_data.get(peak_type, {})
            time_point = peak_data.get('time', 0) or 0
            peaks.append({
                'type': peak_type,
                'icon': {'positive': '🏆', 'negative': '💢', 'density': '🔥'}.get(peak_type, '📌'),
                'time': time_point,
                'timeText': format_time(time_point),
                'value': f"{peak_data.get('description', '')} {peak_data.get('value', 0)}",
                'description': peak_data.get('description', ''),
                'samples': get_peak_samples(bvid, time_point)
            })
        
        # 8. 关键词
        keywords = keywords_data
        
        # 9. 生成分段数据（前端期望的格式）
        timeSegments = []
        for i, point in enumerate(curve_data):
            if isinstance(point, list) and len(point) >= 2:
                timeSegments.append({
                    'segment': f"{point[0]//60}:{(point[0]%60):02d}-{(point[0]//60)}:{(point[0]%60):02d}",
                    'sentiment': point[1],
                    'count': 0,
                    'keywords': ''
                })
        
        # 10. 返回前端期望的数据结构
        return {
            'videoInfo': videoInfo,
            'summary': summary,
            'distribution': distribution,
            'peaks': peaks,
            'keywords': keywords,
            'timeSegments': timeSegments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"报告生成错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取报告失败: {str(e)}")

@router.get("/reports", response_model=ReportListResponse)
async def get_report_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    bvid: Optional[str] = Query(None, description="筛选BV号")
):
    """
    获取报告列表
    """
    try:
        # 构建查询
        sql = """
        SELECT 
            a.bvid, 
            v.title, 
            v.up_name,
            a.total_danmaku,
            a.avg_sentiment,
            a.analyzed_at
        FROM analysis_results a
        JOIN videos v ON a.bvid = v.bvid
        """
        params = []
        
        if bvid:
            sql += " WHERE a.bvid = %s"
            params.append(bvid)
        
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
            reports = cursor.fetchall()
        
        # 格式化时间
        for report in reports:
            if report.get('analyzed_at'):
                report['analyzed_at'] = report['analyzed_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return ReportListResponse(
            total=total,
            reports=reports
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告列表失败: {str(e)}")

@router.delete("/report/{bvid}")
async def delete_report(bvid: str):
    """
    删除报告（只删除 analysis_results 中的记录）
    """
    try:
        sql = "DELETE FROM analysis_results WHERE bvid = %s"
        with db.get_cursor() as cursor:
            cursor.execute(sql, (bvid,))
            deleted = cursor.rowcount
        
        if deleted == 0:
            raise HTTPException(status_code=404, detail="报告不存在")
        
        return {"message": f"报告 {bvid} 删除成功", "deleted": deleted}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# ==================== HTML报告生成 ====================

def generate_html_report(report_data: ReportData) -> str:
    """生成HTML格式的报告"""
    data = report_data.dict()
    summary = data['summary']
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>弹幕情感分析报告 - {summary['bvid']}</title>
        <style>
            body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 40px; background: #f5f7fa; }}
            .report-container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            h1 {{ color: #1E88E5; text-align: center; }}
            .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
            .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 12px; text-align: center; }}
            .summary-card .number {{ font-size: 32px; font-weight: bold; color: #1E88E5; }}
            .summary-card .label {{ color: #666; font-size: 14px; }}
            .section {{ margin: 40px 0; }}
            .section h2 {{ border-bottom: 2px solid #1E88E5; padding-bottom: 10px; }}
            .peaks {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
            .peak-card {{ padding: 20px; border-radius: 12px; }}
            .peak-card.positive {{ background: #e8f5e9; }}
            .peak-card.negative {{ background: #ffebee; }}
            .peak-card.density {{ background: #e3f2fd; }}
            .keywords {{ display: flex; gap: 40px; }}
            .keyword-box {{ flex: 1; }}
            .keyword-tag {{ display: inline-block; background: #e3f2fd; padding: 5px 12px; margin: 4px; border-radius: 16px; }}
            .footer {{ text-align: center; color: #999; margin-top: 40px; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="report-container">
            <h1>📊 弹幕情感分析报告</h1>
            
            <div class="summary">
                <div class="summary-card">
                    <div class="number">{summary['total_danmaku']}</div>
                    <div class="label">总弹幕数</div>
                </div>
                <div class="summary-card">
                    <div class="number">{summary['avg_sentiment']:.2f}</div>
                    <div class="label">平均情感</div>
                </div>
                <div class="summary-card">
                    <div class="number">{summary['positive_ratio']:.1f}%</div>
                    <div class="label">积极比例</div>
                </div>
                <div class="summary-card">
                    <div class="number">{summary['negative_ratio']:.1f}%</div>
                    <div class="label">消极比例</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 视频信息</h2>
                <p><strong>BV号：</strong> {summary['bvid']}</p>
                <p><strong>标题：</strong> {summary['title']}</p>
                <p><strong>UP主：</strong> {summary['up_name']}</p>
                <p><strong>分析时间：</strong> {summary['analyzed_at']}</p>
            </div>
            
            <div class="section">
                <h2>🔥 高潮时刻</h2>
                <div class="peaks">
    """
    
    # 添加高潮时刻
    for peak_type, peak in data['peaks'].items():
        color_class = {
            'positive': 'positive',
            'negative': 'negative',
            'density': 'density'
        }.get(peak_type, '')
        
        icon = {
            'positive': '🏆',
            'negative': '💢',
            'density': '🔥'
        }.get(peak_type, '')
        
        html += f"""
                    <div class="peak-card {color_class}">
                        <div style="font-size: 32px;">{icon}</div>
                        <div style="font-size: 24px; font-weight: bold;">{peak['time_text']}</div>
                        <div style="margin: 10px 0;">{peak['description']}</div>
                        <div style="font-size: 12px; color: #666;">
        """
        
        for sample in peak['samples']:
            html += f'<div>"{sample}"</div>'
        
        html += """
                        </div>
                    </div>
        """
    
    html += f"""
                </div>
            </div>
            
            <div class="section">
                <h2>☁️ 关键词云</h2>
                <div class="keywords">
                    <div class="keyword-box">
                        <h3>积极关键词</h3>
        """
    
    for kw in data['keywords'].get('positive', []):
        html += f'<span class="keyword-tag">{kw}</span>'
    
    html += f"""
                    </div>
                    <div class="keyword-box">
                        <h3>消极关键词</h3>
        """
    
    for kw in data['keywords'].get('negative', []):
        html += f'<span class="keyword-tag">{kw}</span>'
    
    html += f"""
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>报告ID: {data['report_id']} | 生成时间: {data['generated_at']}</p>
                <p>由 弹幕情感分析系统 生成</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

# ==================== 真实的文件导出接口 ====================
@router.get("/report/export/{bvid}")
async def export_report_file(bvid: str, format: str = Query(..., description="导出格式: pdf, excel")):
    """
    导出弹幕数据为 PDF 或 Excel
    """
    # 1. 查询数据库
    danmakus = db.get_danmakus(bvid, limit=100000)
    print(f"📥 导出请求 - BV号: {bvid}, 格式: {format}, 查到数据: {len(danmakus)} 条") # 排查Excel问题的日志
    
    if not danmakus:
        raise HTTPException(status_code=404, detail="未找到弹幕数据，请确保已用单模型分析过该视频")

    # 2. PDF 格式处理 (生成真正的分析报告)
    if format == 'pdf':
        import re
        
        def clean_text(text):
            if not text: return ''
            return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\.\,\!\?\;\:\"\'\-\_\+\=\(\)\@\#\$\%\^\&\*\[\]\{\}\/\\\<\>\~\`\，\。\！\？\；\：\“\”\‘\’\【\】\（\）\——\…\、\n]', '', str(text))

        # --- 1. 获取视频和分析结果汇总数据 ---
        video_info = db.get_video(bvid)
        analysis_res = db.get_analysis_result(bvid)
        
        title = clean_text(video_info.get('title', f'视频 {bvid}')) if video_info else f'视频 {bvid}'
        up_name = clean_text(video_info.get('up_name', '未知UP主')) if video_info else '未知UP主'
        
        total = analysis_res.get('total_danmaku', 0) or 0
        avg_score = analysis_res.get('avg_sentiment', 0) or 0
        pos_ratio = analysis_res.get('positive_ratio', 0) or 0
        neg_ratio = analysis_res.get('negative_ratio', 0) or 0
        neu_ratio = analysis_res.get('neutral_ratio', 0) or 0
        
        # 解析高潮时刻
        peaks_data = json.loads(analysis_res.get('peaks_data', '{}')) if analysis_res and analysis_res.get('peaks_data') else {}

        # --- 2. 开始绘制 PDF ---
        pdf = FPDF()
        pdf.add_page()
        font_path = '../fonts/微软雅黑.ttf'
        pdf.add_font('msyh', '', font_path, uni=True)

        # 报告标题
        pdf.set_font('msyh', '', 22)
        pdf.cell(0, 15, '弹幕情感分析报告', new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(5)
        
        # 视频基础信息
        pdf.set_font('msyh', '', 11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, f'视频标题: {title}', new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f'UP主: {up_name}    BV号: {bvid}', new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f'分析弹幕总量: {total} 条', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)
        pdf.set_text_color(0, 0, 0) # 恢复黑色字

        # --- 模块一：核心指标概览 ---
        pdf.set_fill_color(240, 248, 255)
        pdf.set_font('msyh', '', 14)
        pdf.cell(0, 10, '  一、核心指标概览', new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(5)
        
        pdf.set_font('msyh', '', 12)
        pdf.cell(90, 10, f'平均情感得分: {avg_score:.4f}', new_x="RIGHT", new_y="LAST")
        pdf.cell(90, 10, f'情感偏向: {"积极" if avg_score > 0.5 else "消极"}', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # --- 模块二：情感分布图 (用色块条形图展示) ---
        pdf.set_fill_color(255, 245, 238)
        pdf.set_font('msyh', '', 14)
        pdf.cell(0, 10, '  二、情感倾向分布', new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(5)
        
        bar_y = pdf.get_y()
        bar_max_width = 160
        
        # 积极条
        pdf.set_font('msyh', '', 11)
        pdf.cell(20, 8, '积极:')
        pdf.set_fill_color(76, 175, 80) # 绿色
        pdf.cell(pos_ratio / 100 * bar_max_width, 8, '', fill=True)
        pdf.cell(20, 8, f'{pos_ratio:.1f}%', new_x="LMARGIN", new_y="NEXT")
        
        # 中性条
        pdf.cell(20, 8, '中性:')
        pdf.set_fill_color(158, 158, 158) # 灰色
        pdf.cell(neu_ratio / 100 * bar_max_width, 8, '', fill=True)
        pdf.cell(20, 8, f'{neu_ratio:.1f}%', new_x="LMARGIN", new_y="NEXT")
        
        # 消极条
        pdf.cell(20, 8, '消极:')
        pdf.set_fill_color(244, 67, 54) # 红色
        pdf.cell(neg_ratio / 100 * bar_max_width, 8, '', fill=True)
        pdf.cell(20, 8, f'{neg_ratio:.1f}%', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)

        # --- 模块三：高潮时刻 ---
        pdf.set_fill_color(255, 243, 224)
        pdf.set_font('msyh', '', 14)
        pdf.cell(0, 10, '  三、高潮时刻分析', new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(5)
        
        pdf.set_font('msyh', '', 11)
        peak_types = [
            ('positive', '最积极时刻', '🏆'),
            ('negative', '最消极时刻', '💢'),
            ('density', '弹幕最密时刻', '🔥')
        ]
        for p_type, p_name, p_icon in peak_types:
            p_data = peaks_data.get(p_type, {})
            time_point = p_data.get('time', 0) or 0
            mins = time_point // 60
            secs = time_point % 60
            desc = clean_text(p_data.get('description', '无'))
            
            pdf.set_font('msyh', '', 11)
            pdf.cell(0, 8, f'{p_icon} {p_name}: {mins:02d}:{secs:02d} ({desc})', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)

        # --- 模块四：弹幕抽样明细 (作为附录支撑数据) ---
        pdf.set_fill_color(245, 245, 245)
        pdf.set_font('msyh', '', 14)
        pdf.cell(0, 10, '  四、弹幕数据抽样附录 (前100条)', new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.ln(3)
        
        # 表头
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font('msyh', '', 9)
        pdf.cell(20, 7, '时间(秒)', border=1, fill=True, align='C')
        pdf.cell(110, 7, '弹幕内容', border=1, fill=True, align='C')
        pdf.cell(25, 7, '得分', border=1, fill=True, align='C')
        pdf.cell(25, 7, '标签', border=1, fill=True, align='C')
        pdf.ln()
        
        # 数据行
        pdf.set_font('msyh', '', 8)
        for d in danmakus[:100]:
            t = str(int(d.get('time_point', 0)))
            c = clean_text(str(d.get('content', '')))[:50]
            s = str(round(float(d.get('sentiment_score') or 0), 2))
            tag = str(d.get('sentiment_tag', ''))
            
            pdf.cell(20, 6, t, border=1, align='C')
            pdf.cell(110, 6, c, border=1)
            pdf.cell(25, 6, s, border=1, align='C')
            pdf.cell(25, 6, tag, border=1, align='C')
            pdf.ln()

        # 导出
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={bvid}_report.pdf"}
        )
        
    # 3. Excel 格式处理
    elif format == 'excel':
        df = pd.DataFrame(danmakus)
        df = df.fillna('') # 加上这一行，防止数据库里的 NULL 导致 Excel 结构错乱
        if 'time_point' in df.columns:
            df = df.rename(columns={'time_point': '弹幕时间(秒)', 'content': '弹幕内容', 'sentiment_score': '情感得分', 'sentiment_tag': '情感标签'})
            df = df[['弹幕时间(秒)', '弹幕内容', '情感得分', '情感标签']]
            
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={bvid}_danmaku.xlsx"}
        )
        
    else:
        raise HTTPException(status_code=400, detail="不支持的导出格式")