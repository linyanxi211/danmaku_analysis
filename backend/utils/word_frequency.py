"""
词频与关键词提取工具模块 (基于 TextRank 与词频双重策略)
"""
import jieba
import jieba.analyse
import os
from collections import Counter

# 初始化时加载自定义字典（防止把弹幕特有词切错）
# dict_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'user_dict.txt')
# if os.path.exists(dict_path): jieba.load_userdict(dict_path)

def count_word_frequency(texts, top_n=20):
    """
    基础方法：基于词频(TF)的简单统计（用于基础对比或词云绘制）
    """
    stopwords_path = os.path.join(os.path.dirname(__file__), '..', '..', 'stopwords.txt')
    stopwords = set()
    try:
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            for line in f:
                stopwords.add(line.strip())
    except Exception as e:
        print(f"加载停用词表失败: {e}")

    words = []
    for text in texts:
        if not text: continue
        seg_list = jieba.lcut(str(text))
        for word in seg_list:
            if len(word) >= 2 and word not in stopwords and word.encode('utf-8').isalpha():
                words.append(word)
                
    return Counter(words).most_common(top_n)


def extract_keywords_by_textrank(texts, top_n=15, window_size=5):
    """
    核心方法：基于 TextRank 图排序算法提取关键词（用于报告和高级分析）
    :param texts: 弹幕文本列表
    :param top_n: 返回关键词数量
    :param window_size: 共现窗口大小
    :return: 列表，如 [('关键词1', 0.1534), ('关键词2', 0.1098)] (带权重得分)
    """
    # 1. 将所有弹幕拼接为一个长字符串（解决短文本共现稀疏问题）
    full_text = " ".join([str(t) for t in texts if t])
    
    # 2. 加载停用词（TextRank 允许传入 stop_words 集合进行过滤）
    stopwords_path = os.path.join(os.path.dirname(__file__), '..', '..', 'stopwords.txt')
    stopwords = set()
    try:
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            for line in f:
                stopwords.add(line.strip())
    except: pass

    # 3. 调用 jieba 内置的 TextRank 算法
    # allowPOS 限定只提取名词(n)、名动词(vn)、动词，这是弹幕主题提取的核心
    keywords_with_weights = jieba.analyse.textrank(
        full_text, 
        topK=top_n, 
        withWeight=True, 
        allowPOS=('n', 'vn', 'v'),
        stopWords=stopwords
    )
    
    return keywords_with_weights