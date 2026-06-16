# 科技日報 Tech Daily

每天早上自動推播全球科技時事與 AI 新聞的雙語摘要到你的 iPhone。

## 它做什麼

1. 每天早上 8:30（台北時間）由 cron-job.org 觸發 GitHub Actions 執行
2. 從 Reuters、BBC、The Verge、TechCrunch、OpenAI Blog、Anthropic 等高公信力來源抓取 RSS
3. 用 Claude AI（Haiku 4.5 模型）生成中英文雙語摘要
4. 推播到你 iPhone 上的 ntfy App
5. 同時更新 GitHub Pages 網頁（加到 iPhone 主畫面後像 App 一樣使用）

## 怎麼開始

請打開 [SETUP.md](SETUP.md) 照著一步步操作。

## 怎麼修改

- **新增/移除新聞來源**：編輯 `sources.py`
- **改變推播時間**：到 [cron-job.org](https://console.cron-job.org) 編輯「Tech News Daily」這個工作的執行時間
- **調整摘要風格**：編輯 `main.py` 裡的 `SYSTEM_PROMPT`
- **改網頁樣式**：編輯 `docs/index.html`

## 如果某天沒收到推播

> 💡 程式生成失敗時會主動推播一則「⚠️ 科技日報生成失敗」的通知並附上錯誤原因，所以通常你會直接知道出了什麼事。

1. 先到 [GitHub Actions 頁面](https://github.com/isKa1li/tech-news-daily/actions) 看當天有沒有執行紀錄
2. **沒有執行紀錄** → 到 [cron-job.org](https://console.cron-job.org) 點「Tech News Daily」→「歷史」，看觸發是否失敗（常見：GitHub Token 過期或被撤銷）
3. **有執行紀錄但是紅色 ❌** → 點進該筆紀錄看錯誤訊息（常見：Anthropic API 餘額用完、某個 RSS 來源暫時掛掉）

## 架構

```
RSS Feeds → GitHub Actions (Python) → Claude API → JSON file → GitHub Pages
                                                  ↓
                                              ntfy.sh → iPhone push
```

成本：除了 Claude API 之外全部免費
- GitHub Actions：公開 repo 免費 2000 分鐘/月
- Claude API（Haiku 4.5）：付費，一天 1 次、約每月 US$1 以內（用量可在 [console.anthropic.com](https://console.anthropic.com) 查）
- ntfy.sh：完全免費
- GitHub Pages：免費
