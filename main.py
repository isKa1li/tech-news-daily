"""
Daily Tech News Summary
- Fetches articles from RSS feeds in sources.py
- Summarizes them with Claude (bilingual: Chinese + English)
- Saves JSON to docs/data/ for the GitHub Pages web view
- Pushes a notification to ntfy.sh for iPhone

Environment variables required (set as GitHub Actions secrets):
  ANTHROPIC_API_KEY - your Anthropic API key (console.anthropic.com)
  NTFY_TOPIC        - the ntfy.sh topic name you subscribed to on iPhone
"""

import os
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests
from dateutil import parser as date_parser
import anthropic

from sources import SOURCES, MAX_ITEMS_PER_SOURCE, LOOKBACK_HOURS

# ---------- Config ----------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
CLAUDE_MODEL = "claude-haiku-4-5"  # cheapest; plenty for news summarization
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


# ---------- Step 2: Summarize with Claude ----------
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


# JSON schema so Claude always returns valid, parseable output (no markdown fences).
SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "tldr_zh": {"type": "string"},
        "tldr_en": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["ai", "tech", "world"]},
                    "title_zh": {"type": "string"},
                    "title_en": {"type": "string"},
                    "summary_zh": {"type": "string"},
                    "summary_en": {"type": "string"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": [
                    "category", "title_zh", "title_en",
                    "summary_zh", "summary_en", "source", "url",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["tldr_zh", "tldr_en", "items"],
    "additionalProperties": False,
}


def summarize(articles):
    if not articles:
        raise RuntimeError("No articles fetched - check RSS feeds.")

    # max_retries gives us automatic backoff on transient rate limits / 5xx errors.
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=4)

    article_text = "\n\n".join(
        f"[{a['category']}/{a['source']}] {a['title']}\n{a['summary']}\nURL: {a['url']}"
        for a in articles
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"=== 原始新聞 ===\n{article_text}"}],
        output_config={"format": {"type": "json_schema", "schema": SUMMARY_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


# ---------- Step 3: Save to docs/data ----------
def save_summary(summary):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    summary["date"] = today
    summary["generated_at"] = datetime.now(TAIPEI_TZ).isoformat()

    # Save dated file
    (DATA_DIR / f"{today}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Update latest.json
    (DATA_DIR / "latest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Update index of all dates
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

    # Group items by category, then list each with zh summary
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


# ---------- Failure notification ----------
def push_failure(err):
    """Send a heads-up to your phone when generation fails, so silence is never ambiguous."""
    if not NTFY_TOPIC:
        return
    today = datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=f"今天 ({today}) 的科技日報生成失敗 😢\n錯誤：{err}".encode("utf-8"),
            headers={
                "Title": "⚠️ 科技日報生成失敗".encode("utf-8"),
                "Priority": "high",
                "Tags": "warning",
            },
            timeout=15,
        )
    except Exception:
        pass  # don't let the failure notice itself crash


# ---------- Main ----------
def main():
    if not ANTHROPIC_API_KEY:
        sys.exit("ERROR: ANTHROPIC_API_KEY environment variable is not set")

    try:
        print("Step 1: Fetching RSS feeds...")
        articles = fetch_articles()
        print(f"  Total: {len(articles)} articles\n")

        print(f"Step 2: Summarizing with {CLAUDE_MODEL}...")
        summary = summarize(articles)
        print(f"  Got {len(summary.get('items', []))} summarized items\n")

        print("Step 3: Saving summary...")
        date_str = save_summary(summary)
        print(f"  Saved as {date_str}.json\n")

        print("Step 4: Pushing notification...")
        push_notification(summary, date_str)
        print("  Done!")
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        push_failure(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
