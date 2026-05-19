# 科技日報 Tech Daily

每天早上自動推播全球科技時事與 AI 新聞的雙語摘要到你的 iPhone。

## 它做什麼

1. 每天早上 7:00（台北時間）由 GitHub Actions 自動執行
2. 從 Reuters、BBC、The Verge、TechCrunch、OpenAI Blog、Anthropic 等高公信力來源抓取 RSS
3. 用 Google Gemini AI 生成中英文雙語摘要
4. 推播到你 iPhone 上的 ntfy App
5. 同時更新 GitHub Pages 網頁（加到 iPhone 主畫面後像 App 一樣使用）

## 怎麼開始

請打開 [SETUP.md](SETUP.md) 照著一步步操作。

## 怎麼修改

- **新增/移除新聞來源**：編輯 `sources.py`
- **改變推播時間**：編輯 `.github/workflows/daily.yml` 裡的 `cron` 設定
- **調整摘要風格**：編輯 `main.py` 裡的 `SYSTEM_PROMPT`
- **改網頁樣式**：編輯 `docs/index.html`

## 架構

```
RSS Feeds → GitHub Actions (Python) → Gemini API → JSON file → GitHub Pages
                                                  ↓
                                              ntfy.sh → iPhone push
```

完全免費：
- GitHub Actions：公開 repo 免費 2000 分鐘/月
- Gemini API：免費版每天 1500 次請求（你一天只用 1 次）
- ntfy.sh：完全免費
- GitHub Pages：免費
