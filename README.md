# blog-post-ranking

從 Google Analytics 4 (GA4) API 取得最近 14 天（或指定天數）blog 瀏覽數 Top 10（或指定 Top N）並匯出為 Markdown 文件（for Hexo rendering）。專案背景介紹可參考〈[31，打造新版「熱門文章排名」](https://blog.kyomind.tw/weekly-review-31/)
〉。

## 目錄
- [專案簡介](#專案簡介)
- [功能](#功能)
- [安裝](#安裝)
- [使用方法](#使用方法)
- [環境變數](#環境變數)
- [程式碼結構](#程式碼結構)
- [參考](#參考)

## 專案簡介
本專案的目的是從 Google Analytics 4 取得最近 14 天的 blog 瀏覽數據，並將這些數據匯出為 Markdown 文件，方便用於 Hexo 部落格的展示。

## 功能
- 從 GA4 取得最近 14 天的頁面瀏覽數據
- 將頁面瀏覽數據匯出為 Markdown、CSV
- 支援忽略特定路徑
- 每日自動更新（需自行設定，我使用 cron job）

## 安裝
1.  clone 專案到本地：
    ```sh
    git clone https://github.com/kyomind/blog-post-ranking.git
    cd blog-post-ranking
    ```

2. 建立並啟動虛擬環境：（我使用 Python 3.11.6）
    ```sh
    python -m venv venv
    source venv/bin/activate  # Windows 使用者，請使用 `venv\Scripts\activate`
    ```

3. 安裝所需的套件：
    ```sh
    # Poetry 安裝
    poetry install
    # pip 安裝
    pip install -r requirements.txt
    ```

4. 設定環境變數（詳見下方[環境變數](#環境變數)部分）。

## 使用方法
1. 確保已設定好環境變數。
2. 執行主程式：
 ```sh
 python src/main.py
 ```
程式將會從 GA4 取得最近 28 天的頁面瀏覽數據，並匯出為 Markdown。

## 環境變數
在專案根目錄下建立一個 `.env` 文件，並設定以下環境變數：

```env
KEY_PATH=path/to/your/service/account/key.json
RESOURCE_ID=your_ga4_property_id
EXPORT_DIR=path/to/export/directory
```
- KEY_PATH：Google Service Account 的金鑰文件路徑。(JSON 格式)
- RESOURCE_ID：GA4 資源 ID。
- EXPORT_DIR：匯出 Markdown 文件的目錄路徑。沒設定的話，會匯出到專案根目錄下的 `data` 目錄。

## 程式碼結構
- `src/main.py`：主程式，從 GA4 取得數據並匯出。
- `get_processed_page_views`：函式，取得並處理頁面瀏覽數據。
- `export_accumulative_ranking_to_markdown`：函式，將頁面瀏覽數據匯出為 Markdown 文件。
- `append_trending_ranking_to_markdown`：函式，附加上升趨勢頁面數據到 Markdown 文件。
- `export_accumulative_ranking_to_csv`：函式，將頁面瀏覽數據匯出為 CSV 文件。

## 參考
- [如何使用 Google Analytics Data API](https://codingman.cc/how-to-use-google-analytics-data-api/)
