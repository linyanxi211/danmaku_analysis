"""
使用大模型API对弹幕进行批量情感打标
"""
import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI

# ================= 配置区 =================
API_KEY = "deepseek-KEY"
BASE_URL = "https://api.deepseek.com/v1"  
MODEL_NAME = "deepseek-chat"              

INPUT_FILE = "./data/unlabeled_20260409_155005.jsonl"  # 【注意】改成你实际的导出文件名
OUTPUT_FILE = "./data/labeled_result.jsonl"
BATCH_SIZE = 30 
# ==========================================

# 【更新后的提示词：要求返回 content，并加入理性陈述的判定规则】
SYSTEM_PROMPT = """你是一位深谙中文互联网弹幕文化、拥有极高情商的数据标注专家。你的任务是判断**观众发送弹幕那一刻的主观情绪状态**，而不是判断弹幕文字描述的事件本身是否负面。

请将弹幕分为以下三类：
1. positive（积极）：表达赞美、喜爱、激动、搞笑、共鸣、认可。包括被逗笑、觉得牛逼、同情视频里的弱者等。
2. negative（消极）：表达反感、嘲讽（阴阳怪气针对视频/UP主）、无聊、愤怒、失望。**核心特征是：观众当前处于不爽、生气、厌恶的心理状态。**
3. neutral（中性）：
   - 客观陈述、单纯提问。
   - **【重点】理性的观点输出、对宏大叙事/社会现象/历史事件的客观评价（如“封建制度必将灭亡”、“宗教忽悠不住年轻人”、“这游戏策划太蠢了”），即使包含负面词汇，只要观众不是在发泄对当前视频的不满，均视为中性探讨。**
   - 无意义的感叹词（如“哈哈哈哈”）、刷屏词。

【标注原则】
- 时刻问自己：“发这条弹幕的人，现在是在生气/难受，还是在平静地打字表达观点？”如果是后者，标 neutral。
- 弹幕通常没有主语，请结合语境体会其核心情绪。
- 对于极度阴阳怪气的弹幕（如“就这？”、“太牛了（反语）”），请果断标为 negative。

请严格以JSON格式输出一个列表，不要输出任何多余的解释。**必须包含 id, content, sentiment 三个字段，且 content 必须与输入完全一致。** 格式如下：
[{"id": 1, "content": "弹幕原文", "sentiment": "positive"}, {"id": 2, "content": "弹幕原文", "sentiment": "negative"}]
"""

def batch_annotate():
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ 找不到待标注文件: {INPUT_FILE}")
        print("请先运行 dataset.py 中的 export_unlabeled_for_llm 方法生成文件！")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_data = [json.loads(line) for line in f]
    
    print(f"🚀 开始标注，共 {len(all_data)} 条弹幕，每次处理 {BATCH_SIZE} 条...")

    results = []
    
    for i in range(0, len(all_data), BATCH_SIZE):
        batch = all_data[i:i+BATCH_SIZE]
        
        # 直接把包含 id 和 content 的字典列表发给大模型
        prompt_data = [{"id": item["id"], "content": item["content"]} for item in batch]
        user_msg = json.dumps(prompt_data, ensure_ascii=False)
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                response_format={ "type": "json_object" },
                temperature=0.1
            )
            
            res_json = json.loads(response.choices[0].message.content)
            
            # 解析结果
            if isinstance(res_json, list):
                results.extend(res_json)
            elif isinstance(res_json, dict):
                for key, value in res_json.items():
                    if isinstance(value, list):
                        results.extend(value)
                        
            print(f"   ✅ 进度: {min(i+BATCH_SIZE, len(all_data))}/{len(all_data)}")
            time.sleep(1) 
            
        except Exception as e:
            print(f"   ❌ 第 {i} 批处理出错: {e}")
            error_file = f"./data/error_batch_{i}.json"
            with open(error_file, 'w', encoding='utf-8') as ef:
                json.dump(prompt_data, ef, ensure_ascii=False, indent=2)
            print(f"      -> 错误数据已保存至 {error_file}，跳过继续...")
            continue

    # 保存结果（现在结果里包含了文本，可以直接用来人工校验）
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    print(f"\n🎉 标注完成！共得到 {len(results)} 条结果。")
    print(f"📄 结果保存在: {OUTPUT_FILE}")
    print("💡 提示：请直接打开该文件进行人工抽检，确认无误后再导入数据库！")


if __name__ == '__main__':
    batch_annotate()
