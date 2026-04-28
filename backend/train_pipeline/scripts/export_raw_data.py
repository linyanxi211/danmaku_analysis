"""
从数据库导出有标签的弹幕数据
"""
import pandas as pd
import pymysql
from datetime import datetime

# 数据库配置（和你的 database.py 保持一致）
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Liyuxinaa123..',  # ⚠️ 改成你的密码
    'database': 'danmaku_analysis',
    'charset': 'utf8mb4'
}

def export_training_data(limit=10000, balance=False):
    """
    导出有标签的弹幕数据
    
    Args:
        limit: 最大导出条数
        balance: 是否平衡各标签数量（True会按最少类别采样）
    
    Returns:
        DataFrame: 包含 content 和 sentiment_tag 的数据
    """
    conn = pymysql.connect(**DB_CONFIG)
    
    # 只选取有情感标签且非空的数据
    sql = """
    SELECT content, sentiment_tag 
    FROM danmakus 
    WHERE sentiment_tag IS NOT NULL 
      AND sentiment_tag != ''
      AND content IS NOT NULL
      AND LENGTH(content) > 1
    """
    
    df = pd.read_sql(sql, conn)
    conn.close()
    
    print(f"📊 原始数据总量：{len(df)}条")
    print(f"标签分布：")
    print(df['sentiment_tag'].value_counts())
    
    # 限制数量
    if limit and len(df) > limit:
        df = df.sample(n=limit, random_state=42)
        print(f"\n随机采样至 {limit} 条")
    
    # 可选：平衡各标签数量
    if balance:
        min_count = df['sentiment_tag'].value_counts().min()
        df_balanced = pd.DataFrame()
        for tag in df['sentiment_tag'].unique():
            tag_df = df[df['sentiment_tag'] == tag].sample(n=min_count, random_state=42)
            df_balanced = pd.concat([df_balanced, tag_df])
        df = df_balanced
        print(f"\n平衡后各标签数量：{min_count}条")
    
    return df

if __name__ == '__main__':
    print("="*50)
    print("BERT数据导出工具")
    print("="*50)
    
    # 测试导出
    df = export_training_data(limit=5000)
    
    # 显示样本
    print("\n📝 数据样例：")
    print(df.head(10))
    
    # 保存预览
    df.to_csv('data_preview.csv', index=False)
    print("\n✅ 数据预览已保存到 data_preview.csv")