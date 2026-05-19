# 部署教學 — 從零到收到第一則推播

預計時間：**30-40 分鐘**。完全不用寫程式。

---

## 第一步：在 iPhone 安裝 ntfy 並選一個頻道名稱（5 分鐘）

1. 打開 App Store，搜尋 **ntfy**，下載這個圖示是橘色喇叭的 App（開發者：Philipp Heckel）
2. 打開 ntfy App，點右上角 **+**
3. 在 Topic 欄位輸入一個**只有你自己知道的頻道名稱**
   - ⚠️ ntfy 公開頻道任何人猜到名字都能訂閱看到你的新聞，所以名稱越獨特越好
   - 建議格式：`kai-tech-2026-` 後面加一串隨機字（例如打開 https://www.random.org/strings/ 產生）
   - 範例：`kai-tech-2026-x7k9m2qp`
   - **記下這個頻道名**，等下要用
4. Server 保持預設 `https://ntfy.sh`，點 **Subscribe**

## 第二步：把這個資料夾上傳到 GitHub（15 分鐘）

### 2-1. 建立新的 GitHub repository

1. 打開 https://github.com/new
2. Repository name：`tech-news-daily`
3. ✅ Public（公開——這樣 GitHub Actions 才免費）
4. **不要勾** "Add a README file"（我們已經有了）
5. 點 **Create repository**
6. 暫時不要關閉這個頁面，待會會用到

### 2-2. 把本地檔案上傳

打開 **終端機**（Terminal，在啟動台搜尋「終端機」），複製貼上以下指令一行一行執行：

```bash
cd "/Users/lamperouge/Documents/VS Code/Technology News"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/isKa1li/tech-news-daily.git
git push -u origin main
```

> 如果跳出登入視窗，用你的 GitHub 帳號登入即可。
> 如果說 git 沒安裝，照著彈出的提示安裝 Xcode Command Line Tools 即可。

完成後重新整理 GitHub 頁面，應該可以看到所有檔案都上去了。

## 第三步：在 GitHub 設定兩個秘密（5 分鐘）

這一步是把你的 Gemini API key 和 ntfy 頻道名稱告訴 GitHub Actions，讓它跑程式時可以用。

1. 進入你的 repo 頁面：https://github.com/isKa1li/tech-news-daily
2. 點上方 **Settings**
3. 左邊選單往下找到 **Secrets and variables → Actions**
4. 點綠色按鈕 **New repository secret**，新增兩個 secret：

| Name | Secret 內容 |
|---|---|
| `GEMINI_API_KEY` | 貼上你 Google AI Studio 的 API key（`AIzaSy...` 開頭那串）|
| `NTFY_TOPIC` | 貼上你剛才在 ntfy 設定的頻道名稱（例如 `kai-tech-2026-x7k9m2qp`）|

⚠️ 兩個 secret 名稱要**完全一樣**（含大小寫底線）。

## 第四步：開啟 GitHub Pages（讓網頁可以看）（2 分鐘）

1. 同樣在 repo 的 **Settings**
2. 左邊選單找到 **Pages**
3. Source 選 **Deploy from a branch**
4. Branch 選 **main**，資料夾選 **/docs**
5. 點 **Save**
6. 等 1-2 分鐘，頁面上會出現網址：`https://iska1li.github.io/tech-news-daily/`
   - 一開始打開會說「尚無資料」，這是正常的，要等第一次 Actions 跑完才有資料

## 第五步：手動觸發第一次執行（測試用）（3 分鐘）

排程預設是每天台北時間早上 7:00，但我們不想等到明天，所以手動觸發一次：

1. 在 repo 點上方 **Actions** 標籤
2. 如果跳出 "Workflows aren't being run on this repository"，點 **I understand my workflows, go ahead and enable them**
3. 左邊選 **Daily Tech News Summary**
4. 右邊點 **Run workflow** 下拉 → 再點綠色 **Run workflow**
5. 等 1-2 分鐘，重新整理頁面，應該會看到綠色勾勾 ✅

**這時候你的 iPhone 應該會收到第一則推播！** 🎉

如果失敗了（紅色 X），點進去看錯誤訊息給我，我幫你診斷。

## 第六步：把網頁加到 iPhone 主畫面（1 分鐘）

1. 用 iPhone 的 **Safari** 打開 `https://iska1li.github.io/tech-news-daily/`
2. 點底部分享按鈕（中間那個方塊向上箭頭）
3. 往下滑找到 **加入主畫面**
4. 名稱保持「科技日報」，點 **加入**

主畫面上會出現一個有自訂圖示的「科技日報」方塊，點開全螢幕顯示，跟 App 一樣。

---

## 完成後你每天會經歷什麼

🌅 早上 7:00 — iPhone 鎖定畫面跳出推播：
```
科技日報 2026-05-20
📌 今日 OpenAI 發布 GPT-5...
📌 Today OpenAI announced GPT-5...
• 第一則新聞標題
• 第二則新聞標題
...
```

📱 點推播 → 進入 ntfy App 看完整摘要
📱 點主畫面圖示 → 進入網頁版，可以看歷史每一天

---

## 常見問題

**Q：沒收到推播？**
A：檢查 ntfy App 的通知權限有開、頻道名稱跟 secret 完全一樣（大小寫敏感）。

**Q：想改推播時間？**
A：編輯 `.github/workflows/daily.yml` 裡的 `cron: "0 23 * * *"`。格式是 `分 時 * * *`（UTC 時間），台北時間要 -8 小時。例如想要早上 8:00 推播 → UTC 是 0:00 → `cron: "0 0 * * *"`。

**Q：想加新的新聞來源？**
A：編輯 `sources.py`，加一行新的進去。RSS 網址通常在媒體網站的「RSS」或「訂閱」連結。

**Q：摘要太多/太少？**
A：編輯 `main.py` 裡的 `SYSTEM_PROMPT`，把「8-12 則」改成你想要的數字。

**Q：用一陣子超過 Gemini 免費額度怎麼辦？**
A：免費版每天 1500 次請求，你一天用 1 次，理論上永遠用不完。如果真的超過會有提示。
