"""
Daily Tech News Summary
- Fetches articles from RSS feeds in sources.py
- Summarizes them with Google Gemini (bilingual: Chinese + English)
- Saves JSON to docs/data/ for the GitHub Pages web view
- Pushes a notification to ntfy.sh for iPhone

Environment variables required (set as GitHub Actions secrets):
  GEMINI_API_KEY   - your Google AI Studio API key
  NTFY_TOPIC       - the ntfy.sh topic name you subscribed to on iPhone
"""

import os
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests
from dateutil import parser as date_parser
import google.generativeai as genai

from sources import SOURCES, MAX_ITEMS_PER_SOURCE, LOOKBACK_HOURS

# ---------- Config ----------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
GEMINI_MODEL = "gemini-2.5-flash"
TAIPEI_TZ = timezone(timedelta(hours=8))

DOCS_DIR = Path(__file__).parent / "docs"
DATA_DIR = DOCS_DIR / "data"


# ---------- Step 1: Fetch RSS ----------
def fetch_articles():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    articles = []

    for src in SOURCES:
        try:
            feed = feedparser.parse(src["url"])
        except Exception as e:
            print(f"  [skip] {src['name']}: {e}", file=sys.stderr)
            continue

        count = 0
        for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
            published = entry.get("published") or entry.get("updated")
            if published:
                try:
                    pub_dt = date_parser.parse(published)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass

            articles.append({
                "source": src["name"],
                "category": src["category"],
                "lang": src["lang"],
                "title": entry.get("title", "").strip(),
                "summary": (entry.get("summary") or "")[:500].strip(),
                "url": entry.get("link", ""),
            })
            count += 1

        print(f"  {src['name']}: {count} articles")

    return articles


# ---------- Step 2: Summarize with Gemini ----------
SYSTEM_PROMPT = """你是一位專業的雙語科技新聞編輯。請從以下原始新聞中篩選出今天最重要的 8-12 則新聞，並產生雙語摘要。

重點優先順序：
1. AI 與大語言模型的重大突破、新模型發布
2. 主要科技公司（Apple, Google, Microsoft, Meta, OpenAI, Anthropic, NVIDIA 等）的重要動向
3. 影響全球的科技政策、法規
4. 國際重大新聞（戰爭、經濟、選舉等）

請以 JSON 格式輸出（不要有 markdown code fence，直接輸出 JSON）：
{
  "tldr_zh": "今天科技圈一句話總結（30 字以內）",
  "tldr_en": "One-sentence TL;DR of today (under 25 words)",
  "items": [
    {
      "category": "ai" | "tech" | "world",
      "title_zh": "繁體中文標題（簡潔有力，15-25 字）",
      "title_en": "English title",
      "summary_zh": "繁體中文摘要 2-3 句，講清楚發生什麼、為什麼重要",
      "summary_en": "English summary, 2-3 sentences",
      "source": "來源媒體名稱",
      "url": "原文連結"
    }
  ]
}

注意：使用繁體中文，不要簡體。重要性排序：AI > Tech > World。同一事件只保留最權威來源那則。"""


def summarize(articles):
    if not articles:
        raise RuntimeError("No articles fetched - check RSS feeds.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    article_text = "\n\n".join(
        f"[{a['category']}/{a['source']}] {a['title']}\n{a['summary']}\nURL: {a['url']}"
        for a in articles
    )

    prompt = f"{SYSTEM_PROMPT}\n\n=== 原始新聞 ===\n{article_text}"

    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json", "temperature": 0.3},
    )

    return json.loads(response.text)


# ---------- Step 3: Save to docs/data ----------
def save_summary(summary):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    summary["date"] = today
    summary["generated_at"] = datetime.now(TAIPEI_TZ).isoformat()

    (DATA_DIR / f"{today}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA_DIR / "latest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    dates = sorted(
        [f.stem for f in DATA_DIR.glob("*.json") if f.stem not in ("latest", "index")],
        reverse=True,
    )
    (DATA_DIR / "index.json").write_text(
        json.dumps({"dates": dates}, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return today


# ---------- Step 4: Push notification ----------
CATEGORY_LABEL = {
    "ai": ("🤖 AI / 人工智慧", "🤖"),
    "tech": ("💻 科技 Tech", "💻"),
    "world": ("🌍 國際 World", "🌍"),
}


def push_notification(summary, date_str):
    if not NTFY_TOPIC:
        print("  [skip] NTFY_TOPIC not set")
        return

    title = f"📱 科技日報 {date_str}"

    lines = [
        f"📌 {summary.get('tldr_zh', '')}",
        f"📌 {summary.get('tldr_en', '')}",
    ]

    items_by_cat = {"ai": [], "tech": [], "world": []}
    for item in summary.get("items", []):
        cat = item.get("category", "tech")
        if cat in items_by_cat:
            items_by_cat[cat].append(item)

    for cat in ("ai", "tech", "world"):
        items = items_by_cat[cat]
        if not items:
            continue
        section_title, icon = CATEGORY_LABEL[cat]
        lines.append("")
        lines.append(f"━━━ {section_title} ━━━")
        for it in items:
            lines.append("")
            lines.append(f"{icon} {it.get('title_zh', '')}")
            summary_zh = it.get("summary_zh", "").strip()
            if summary_zh:
                lines.append(summary_zh)
            src = it.get("source", "")
            if src:
                lines.append(f"— {src}")

    body = "\n".join(lines)

    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=body.encode("utf-8"),
        headers={
            "Title": title.encode("utf-8"),
            "Priority": "default",
            "Tags": "newspaper,robot",
            "Click": f"https://iska1li.github.io/tech-news-daily/?date={date_str}",
        },
        timeout=15,
    )


# ---------- Main ----------
def main():
    if not GEMINI_API_KEY:
        sys.exit("ERROR: GEMINI_API_KEY environment variable is not set")

    print("Step 1: Fetching RSS feeds...")
    articles = fetch_articles()
    print(f"  Total: {len(articles)} articles\n")

    print(f"Step 2: Summarizing with {GEMINI_MODEL}...")
    summary = summarize(articles)
    print(f"  Got {len(summary.get('items', []))} summarized items\n")

    print("Step 3: Saving summary...")
    date_str = save_summary(summary)
    print(f"  Saved as {date_str}.json\n")

    print("Step 4: Pushing notification...")
    push_notification(summary, date_str)
    print("  Done!")


if __name__ == "__main__":
    main()
