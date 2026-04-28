<h1 align="center">Bilibili Sentiment Analysis</h1>
<p align="center"><strong>基于B站弹幕评论的舆情分析，B站的弹幕的获取，情感分析和词云图</strong></p>

## 一、代码示例

```python
from main import main

# Set parameters
url = 'https://www.bilibili.com/video/BV1wq4y1s7S5/?spm_id_from=333.337.search-card.all.click&vd_source=1d24f52164a3ed510e0b7386c010cc2e'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Apple\
           WebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}
resultpath = './result'

# Run the main function
main(
    url=url,
    headers=headers,
    segment=15,
    save_fig=True,
    resultpath=resultpath
)
```

>   [!IMPORTANT]
>
>   ***如果遇到有关代码的问题或是其他需求，请提 `Issues` 或 `PR` ，我会尽快解决！***

>   [!WARNING]
>
>   ***本项目仅用于学习使用！！！***
>
>   ***本项目仅用于学习使用！！！***
>
>   ***本项目仅用于学习使用！！！***


## 二、思路

### （一）数据获取

-   使用`API接口`获取弹幕数据。

-   获取数据格式为`XML`格式。

### （二）数据分析

#### 1. 视频播放中弹幕发出时间和数量

1.   提取获得的`XML`文件中的节点，得到评论发出时的**视频播放时长**。
2.   分箱，获得某一时段内的弹幕的数量。
3.   可视化。
4.   对弹幕数量最多的部分进行进一步分析。
     -   视频中的内容的分析
         -   文字解释
     -   该段时间的弹幕内容的分析
         -   关键词提取 `(TextRank)`

#### 2. 弹幕实际发出的时间

1.   提取获得的`XML`文件中的节点，得到评论发出时的**实际时间**。**（`XML`格式提取的格式为时间戳）**

2.   根据不同时间节点的弹幕的数量和内容，可结合该时点的新闻或发布的政策等进行分析。

#### 3. 弹幕内容

1.   情感分析
     -   所有弹幕的情感倾向
     -   情感趋势图
2.   关键词提取
3.   词云图

#### 4. 挖掘潜在信息

1.   弹幕与视频内容之间的关联性。
2.   用户在特定事件（如视频中的某个情节）发生时的弹幕行为。
3.   用户之间的互动行为，如回复、@等。


```
bilibili_sentiment_analysis
├─ backend
│  ├─ 0.26.0
│  ├─ api
│  │  ├─ analysis.py
│  │  ├─ danmaku.py
│  │  ├─ history.py
│  │  ├─ model.py
│  │  ├─ report.py
│  │  └─ video.py
│  ├─ app.py
│  ├─ archive
│  │  ├─ 0
│  │  ├─ 137649199
│  │  │  ├─ barrage_keywords.csv
│  │  │  ├─ barrage_num.png
│  │  │  ├─ real_time_barrage.csv
│  │  │  ├─ sentiment_trend.csv
│  │  │  ├─ sentiment_trend.png
│  │  │  ├─ top_segment_barrage.csv
│  │  │  ├─ top_segment_keywords.txt
│  │  │  └─ word_cloud.png
│  │  ├─ get_barrage.py
│  │  ├─ main.py
│  │  ├─ run.py
│  │  └─ visualize.py
│  ├─ data
│  │  ├─ bert_llm_v1_20260409_210058.csv
│  │  ├─ bert_llm_v1_20260409_210058.pkl
│  │  ├─ bert_llm_v1_stats.json
│  │  ├─ labeled_result.jsonl
│  │  └─ unlabeled_20260409_155005.jsonl
│  ├─ database
│  │  └─ models.py
│  ├─ export
│  ├─ models
│  │  ├─ bert_finetuned_20260317_175043
│  │  │  ├─ config.json
│  │  │  ├─ model.safetensors
│  │  │  ├─ model_config.json
│  │  │  ├─ special_tokens_map.json
│  │  │  ├─ tokenizer_config.json
│  │  │  ├─ training_report.txt
│  │  │  └─ vocab.txt
│  │  ├─ bert_model.py
│  │  ├─ bert_sentiment
│  │  │  ├─ checkpoint-241
│  │  │  │  ├─ config.json
│  │  │  │  ├─ model.safetensors
│  │  │  │  ├─ optimizer.pt
│  │  │  │  ├─ rng_state.pth
│  │  │  │  ├─ scheduler.pt
│  │  │  │  ├─ trainer_state.json
│  │  │  │  └─ training_args.bin
│  │  │  ├─ checkpoint-482
│  │  │  │  ├─ config.json
│  │  │  │  ├─ model.safetensors
│  │  │  │  ├─ optimizer.pt
│  │  │  │  ├─ rng_state.pth
│  │  │  │  ├─ scheduler.pt
│  │  │  │  ├─ trainer_state.json
│  │  │  │  └─ training_args.bin
│  │  │  ├─ checkpoint-723
│  │  │  │  ├─ config.json
│  │  │  │  ├─ model.safetensors
│  │  │  │  ├─ optimizer.pt
│  │  │  │  ├─ rng_state.pth
│  │  │  │  ├─ scheduler.pt
│  │  │  │  ├─ trainer_state.json
│  │  │  │  └─ training_args.bin
│  │  │  ├─ config.json
│  │  │  ├─ model.safetensors
│  │  │  ├─ model_config.json
│  │  │  ├─ special_tokens_map.json
│  │  │  ├─ tokenizer_config.json
│  │  │  ├─ training_args.bin
│  │  │  ├─ training_result.json
│  │  │  └─ vocab.txt
│  │  └─ sentiment.py
│  ├─ report.html
│  ├─ report.json
│  ├─ requirements.txt
│  ├─ run.sh
│  ├─ scripts
│  │  ├─ data
│  │  │  ├─ test.csv
│  │  │  ├─ train.csv
│  │  │  └─ val.csv
│  │  ├─ export_raw_data.py
│  │  ├─ label_with_llm.py
│  │  ├─ models
│  │  │  └─ bert_ai_challenger_finetuned
│  │  │     ├─ config.json
│  │  │     ├─ model.safetensors
│  │  │     ├─ model_config.json
│  │  │     ├─ special_tokens_map.json
│  │  │     ├─ tokenizer_config.json
│  │  │     └─ vocab.txt
│  │  └─ train_bert.py
│  ├─ tmp_trainer
│  ├─ utils
│  │  ├─ crawler.py
│  │  ├─ database.py
│  │  ├─ dataset.py
│  │  ├─ helpers.py
│  │  ├─ utils.py
│  │  ├─ visualize.py
│  │  └─ word_frequency.py
│  └─ websocket.py
├─ fonts
│  ├─ 华文中宋.ttf
│  ├─ 华文仿宋.ttf
│  ├─ 华文彩云.ttf
│  ├─ 华文新魏.ttf
│  ├─ 华文楷体.ttf
│  ├─ 华文琥珀.ttf
│  ├─ 华文细黑.ttf
│  ├─ 华文行楷.ttf
│  ├─ 华文隶体.ttf
│  ├─ 微软雅黑.ttf
│  └─ 微软雅黑粗体.ttf
├─ frontend
│  ├─ index.html
│  ├─ package-lock.json
│  ├─ package.json
│  ├─ public
│  │  ├─ favicon.ico
│  │  └─ images
│  │     └─ logo.png
│  ├─ src
│  │  ├─ api
│  │  │  ├─ index.js
│  │  │  └─ modules
│  │  │     ├─ analysis.js
│  │  │     ├─ danmaku.js
│  │  │     ├─ export.js
│  │  │     ├─ model.js
│  │  │     ├─ reports.js
│  │  │     └─ video.js
│  │  ├─ App.vue
│  │  ├─ assets
│  │  │  ├─ images
│  │  │  └─ styles
│  │  │     └─ main.css
│  │  ├─ components
│  │  │  ├─ analysis
│  │  │  │  └─ PeakMoments.vue
│  │  │  ├─ chart
│  │  │  │  ├─ CompareChart.vue
│  │  │  │  ├─ Heatmap.vue
│  │  │  │  ├─ SentimentCurve.vue
│  │  │  │  └─ WordCloud.vue
│  │  │  ├─ common
│  │  │  │  ├─ AppHeader.vue
│  │  │  │  ├─ AppSidebar.vue
│  │  │  │  └─ Loading.vue
│  │  │  ├─ danmaku
│  │  │  │  ├─ DanmakuDrawer.test.vue
│  │  │  │  ├─ DanmakuDrawer.vue
│  │  │  │  ├─ DanmakuList.vue
│  │  │  │  └─ DanmakuStream.vue
│  │  │  ├─ export
│  │  │  │  └─ ExportButton.vue
│  │  │  ├─ model
│  │  │  │  ├─ ConfusionMatrix.vue
│  │  │  │  ├─ ModelCompare.vue
│  │  │  │  ├─ ModelSelector.vue
│  │  │  │  └─ TrainingMonitor.vue
│  │  │  └─ video
│  │  │     └─ VideoPlayer.vue
│  │  ├─ composables
│  │  │  ├─ useExport.js
│  │  │  ├─ useHeatmap.js
│  │  │  ├─ useMockWebSocket.js
│  │  │  ├─ useVideo.js
│  │  │  └─ useWebsocket.js
│  │  ├─ main.js
│  │  ├─ mock
│  │  │  └─ index.js
│  │  ├─ router
│  │  │  └─ index.js
│  │  ├─ stores
│  │  │  ├─ analysis.js
│  │  │  ├─ compare.js
│  │  │  ├─ danmaku.js
│  │  │  ├─ model.js
│  │  │  ├─ reports.js
│  │  │  ├─ video.js
│  │  │  └─ websocket.js
│  │  ├─ utils
│  │  │  ├─ color.js
│  │  │  ├─ format.js
│  │  │  ├─ pdfGenerators.js
│  │  │  └─ storge.js
│  │  └─ views
│  │     ├─ Compare.vue
│  │     ├─ History.vue
│  │     ├─ Home.vue
│  │     ├─ HomeBuilder.vue
│  │     ├─ ModelLab.vue
│  │     └─ Report.vue
│  └─ vite.config.js
├─ LICENSE
├─ models
├─ output
│  └─ reports
├─ README.md
└─ stopwords.txt

```
```
bilibili_sentiment_analysis
├─ backend
│  ├─ api
│  │  ├─ analysis.py
│  │  ├─ danmaku.py
│  │  ├─ history.py
│  │  ├─ model.py
│  │  ├─ report.py
│  │  └─ video.py
│  ├─ app.py
│  ├─ data
│  │  ├─ bert_llm_v1_20260409_210058.csv
│  │  ├─ bert_llm_v1_20260409_210058.pkl
│  │  ├─ bert_llm_v1_stats.json
│  │  ├─ labeled_result.jsonl
│  │  └─ unlabeled_20260409_155005.jsonl
│  ├─ models
│  │  ├─ bert_model.py
│  │  ├─ bert_sentiment
│  │  │  ├─ config.json
│  │  │  ├─ model.safetensors
│  │  │  ├─ model_config.json
│  │  │  ├─ special_tokens_map.json
│  │  │  ├─ tokenizer_config.json
│  │  │  ├─ training_args.bin
│  │  │  ├─ training_result.json
│  │  │  └─ vocab.txt
│  │  └─ sentiment.py
│  ├─ requirements.txt
│  ├─ run.sh
│  ├─ scripts
│  │  ├─ export_raw_data.py
│  │  ├─ label_with_llm.py
│  │  ├─ models
│  │  └─ train_bert.py
│  ├─ utils
│  │  ├─ crawler.py
│  │  ├─ database.py
│  │  ├─ helpers.py
│  │  └─ utils.py
│  └─ websocket.py
├─ fonts
│  ├─ 华文中宋.ttf
│  ├─ 华文仿宋.ttf
│  ├─ 华文彩云.ttf
│  ├─ 华文新魏.ttf
│  ├─ 华文楷体.ttf
│  ├─ 华文琥珀.ttf
│  ├─ 华文细黑.ttf
│  ├─ 华文行楷.ttf
│  ├─ 华文隶体.ttf
│  ├─ 微软雅黑.ttf
│  └─ 微软雅黑粗体.ttf
├─ frontend
│  ├─ index.html
│  ├─ package-lock.json
│  ├─ package.json
│  ├─ public
│  │  ├─ favicon.ico
│  │  └─ images
│  │     └─ logo.png
│  ├─ src
│  │  ├─ api
│  │  │  ├─ index.js
│  │  │  └─ modules
│  │  │     ├─ analysis.js
│  │  │     ├─ danmaku.js
│  │  │     ├─ export.js
│  │  │     ├─ model.js
│  │  │     ├─ reports.js
│  │  │     └─ video.js
│  │  ├─ App.vue
│  │  ├─ assets
│  │  │  ├─ images
│  │  │  └─ styles
│  │  │     └─ main.css
│  │  ├─ components
│  │  │  ├─ analysis
│  │  │  │  └─ PeakMoments.vue
│  │  │  ├─ chart
│  │  │  │  ├─ CompareChart.vue
│  │  │  │  ├─ Heatmap.vue
│  │  │  │  ├─ SentimentCurve.vue
│  │  │  │  └─ WordCloud.vue
│  │  │  ├─ common
│  │  │  │  ├─ AppHeader.vue
│  │  │  │  ├─ AppSidebar.vue
│  │  │  │  └─ Loading.vue
│  │  │  ├─ danmaku
│  │  │  │  ├─ DanmakuDrawer.test.vue
│  │  │  │  ├─ DanmakuDrawer.vue
│  │  │  │  ├─ DanmakuList.vue
│  │  │  │  └─ DanmakuStream.vue
│  │  │  ├─ export
│  │  │  │  └─ ExportButton.vue
│  │  │  ├─ model
│  │  │  │  ├─ ConfusionMatrix.vue
│  │  │  │  ├─ ModelCompare.vue
│  │  │  │  ├─ ModelSelector.vue
│  │  │  │  └─ TrainingMonitor.vue
│  │  │  └─ video
│  │  │     └─ VideoPlayer.vue
│  │  ├─ composables
│  │  │  ├─ useExport.js
│  │  │  ├─ useHeatmap.js
│  │  │  ├─ useMockWebSocket.js
│  │  │  ├─ useVideo.js
│  │  │  └─ useWebsocket.js
│  │  ├─ main.js
│  │  ├─ mock
│  │  │  └─ index.js
│  │  ├─ router
│  │  │  └─ index.js
│  │  ├─ stores
│  │  │  ├─ analysis.js
│  │  │  ├─ compare.js
│  │  │  ├─ danmaku.js
│  │  │  ├─ model.js
│  │  │  ├─ reports.js
│  │  │  ├─ video.js
│  │  │  └─ websocket.js
│  │  ├─ utils
│  │  │  ├─ color.js
│  │  │  ├─ format.js
│  │  │  ├─ pdfGenerators.js
│  │  │  └─ storge.js
│  │  └─ views
│  │     ├─ Compare.vue
│  │     ├─ History.vue
│  │     ├─ Home.vue
│  │     ├─ HomeBuilder.vue
│  │     ├─ ModelLab.vue
│  │     └─ Report.vue
│  └─ vite.config.js
├─ LICENSE
├─ models
├─ output
│  └─ reports
├─ README.md
└─ stopwords.txt

```