"""
数据库操作模块 - MySQL版本
"""
import pymysql
import pymysql.cursors
import json
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import pandas as pd

# 数据库配置 - 请确认这里的密码正确
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Liyuxinaa123..',  # 改成你的实际密码
    'database': 'danmaku_analysis',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: dict = None):
        self.config = config or DB_CONFIG
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            conn = pymysql.connect(**self.config)
            conn.close()
            return True, "连接成功"
        except Exception as e:
            return False, str(e)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = None
        try:
            conn = pymysql.connect(**self.config)
            yield conn
        except Exception as e:
            print(f"数据库连接错误: {e}")
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self):
        """获取数据库游标"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"数据库操作错误: {e}")
                raise e
            finally:
                cursor.close()
    
    # ==================== 视频相关操作 ====================
    
    def save_video(self, video_data: Dict) -> int:
        """保存视频信息"""
        sql = """
        INSERT INTO videos (bvid, title, up_name, duration, cover_url)
        VALUES (%(bvid)s, %(title)s, %(up_name)s, %(duration)s, %(cover_url)s)
        ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        up_name = VALUES(up_name),
        duration = VALUES(duration),
        cover_url = VALUES(cover_url)
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, video_data)
                return cursor.lastrowid
        except Exception as e:
            print(f"保存视频失败: {e}")
            return 0
    
    def get_video(self, bvid: str) -> Optional[Dict]:
        """获取视频信息"""
        sql = "SELECT * FROM videos WHERE bvid = %s"
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, (bvid,))
                return cursor.fetchone()
        except Exception as e:
            print(f"获取视频失败: {e}")
            return None
    
    # ==================== 弹幕相关操作 ====================
    
    def save_danmakus(self, bvid: str, danmakus: pd.DataFrame, sentiments: pd.DataFrame):
        """保存弹幕数据（先删除旧的）"""
        if len(danmakus) == 0:
            return
        
        try:
            # 先删除该视频的所有旧弹幕
            with self.get_cursor() as cursor:
                cursor.execute("DELETE FROM danmakus WHERE bvid = %s", (bvid,))
                print(f"🗑️ 已删除 {cursor.rowcount} 条旧弹幕")
            
            # 再插入新弹幕
            sql = """
            INSERT INTO danmakus (bvid, time_point, content, sentiment_score, sentiment_tag)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            data = []
            for i in range(len(danmakus)):
                sentiment_score = float(sentiments.iloc[i]['score']) if i < len(sentiments) else 0.5
                sentiment_tag = sentiments.iloc[i]['tag'] if i < len(sentiments) else 'neutral'
                
                data.append((
                    bvid,
                    float(danmakus.iloc[i]['time']),
                    str(danmakus.iloc[i]['content'])[:500],
                    sentiment_score,
                    sentiment_tag
                ))
            
            with self.get_cursor() as cursor:
                cursor.executemany(sql, data)
                print(f"✅ 成功保存 {len(data)} 条新弹幕")
                
        except Exception as e:
            print(f"保存弹幕失败: {e}")
    
    def get_danmakus(self, bvid: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """获取弹幕列表（分页）"""
        sql = """
        SELECT * FROM danmakus 
        WHERE bvid = %s 
        ORDER BY time_point 
        LIMIT %s OFFSET %s
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, (bvid, limit, offset))
                return cursor.fetchall()
        except Exception as e:
            print(f"获取弹幕失败: {e}")
            return []
    
    # ==================== 分析结果操作 ====================
    
    def save_analysis_result(self, bvid: str, result: Dict):
        """保存分析结果"""
        # 先检查是否已存在
        existing = self.get_analysis_result(bvid)
        
        # 提取统计数据
        sentiment_stats = result.get('sentiment_stats', {})
        
        if existing:
            sql = """
            UPDATE analysis_results SET
            total_danmaku = %s,
            avg_sentiment = %s,
            positive_ratio = %s,
            neutral_ratio = %s,
            negative_ratio = %s,
            heatmap_data = %s,
            curve_data = %s,
            peaks_data = %s,
            keywords_data = %s,
            analyzed_at = CURRENT_TIMESTAMP
            WHERE bvid = %s
            """
            # params 已经包含 bvid，直接使用
            params = (
                result.get('total_danmaku', 0),
                sentiment_stats.get('avg_score', 0),
                sentiment_stats.get('positive_ratio', 0),
                sentiment_stats.get('neutral_ratio', 0),
                sentiment_stats.get('negative_ratio', 0),
                json.dumps(result.get('heatmap_data', []), ensure_ascii=False),
                json.dumps(result.get('curve_data', []), ensure_ascii=False),
                json.dumps(result.get('peaks', {}), ensure_ascii=False),
                json.dumps(result.get('keywords', {}), ensure_ascii=False),
                bvid
            )
        else:
            sql = """
            INSERT INTO analysis_results 
            (bvid, total_danmaku, avg_sentiment, positive_ratio, neutral_ratio, 
             negative_ratio, heatmap_data, curve_data, peaks_data, keywords_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                bvid,
                result.get('total_danmaku', 0),
                sentiment_stats.get('avg_score', 0),
                sentiment_stats.get('positive_ratio', 0),
                sentiment_stats.get('neutral_ratio', 0),
                sentiment_stats.get('negative_ratio', 0),
                json.dumps(result.get('heatmap_data', []), ensure_ascii=False),
                json.dumps(result.get('curve_data', []), ensure_ascii=False),
                json.dumps(result.get('peaks', {}), ensure_ascii=False),
                json.dumps(result.get('keywords', {}), ensure_ascii=False)
            )
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, params)
                print(f"分析结果保存成功: {bvid}")
        except Exception as e:
            print(f"保存分析结果失败: {e}")
    
    def get_analysis_result(self, bvid: str) -> Optional[Dict]:
        """获取分析结果"""
        sql = "SELECT * FROM analysis_results WHERE bvid = %s"
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, (bvid,))
                result = cursor.fetchone()
                if result:
                    # 解析JSON字段
                    return result
                return None
        except Exception as e:
            print(f"获取分析结果失败: {e}")
            return None
    
    # ==================== 任务相关操作 ====================
    
    def create_task(self, task_id: str, bvid: str) -> int:
        """创建任务记录"""
        sql = """
        INSERT INTO analysis_tasks (task_id, bvid, status, progress, message)
        VALUES (%s, %s, 'pending', 0, '等待开始')
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, (task_id, bvid))
                return cursor.lastrowid
        except Exception as e:
            print(f"创建任务失败: {e}")
            return 0
    
    def update_task(self, task_id: str, status: str, progress: int, message: str):
        """更新任务状态"""
        sql = """
        UPDATE analysis_tasks 
        SET status = %s, progress = %s, message = %s
        WHERE task_id = %s
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, (status, progress, message, task_id))
        except Exception as e:
            print(f"更新任务失败: {e}")
    
    def complete_task(self, task_id: str):
        """完成任务"""
        sql = """
        UPDATE analysis_tasks 
        SET status = 'completed', progress = 100, completed_at = CURRENT_TIMESTAMP
        WHERE task_id = %s
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, (task_id,))
        except Exception as e:
            print(f"完成任务失败: {e}")
    
    def fail_task(self, task_id: str, error_msg: str):
        """任务失败"""
        sql = """
        UPDATE analysis_tasks 
        SET status = 'failed', message = %s, completed_at = CURRENT_TIMESTAMP
        WHERE task_id = %s
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, (error_msg, task_id))
        except Exception as e:
            print(f"标记任务失败: {e}")
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        sql = "SELECT * FROM analysis_tasks WHERE task_id = %s"
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, (task_id,))
                return cursor.fetchone()
        except Exception as e:
            print(f"获取任务失败: {e}")
            return None

# 创建全局数据库管理器实例
db = DatabaseManager()

# 测试连接
success, message = db.test_connection()
print(f"数据库连接测试: {message}")