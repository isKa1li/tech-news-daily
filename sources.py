"""
News sources. Edit this file to add or remove feeds.
Each source has: name, RSS URL, category, language.
Categories: "ai", "tech", "world"
Languages: "en", "zh"
"""

SOURCES = [
    # ===== AI / 人工智慧 =====
    {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml", "category": "ai", "lang": "en"},
    {"name": "Anthropic News", "url": "https://www.anthropic.com/news/rss.xml", "category": "ai", "lang": "en"},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml", "category": "ai", "lang": "en"},
    {"name": "MIT Tech Review - AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "category": "ai", "lang": "en"},

    # ===== Tech / 科技 =====
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "tech", "lang": "en"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "category": "tech", "lang": "en"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "tech", "lang": "en"},
    {"name": "Hacker News (Top)", "url": "https://hnrss.org/frontpage", "category": "tech", "lang": "en"},
    {"name": "iThome", "url": "https://www.ithome.com.tw/rss", "category": "tech", "lang": "zh"},
    {"name": "INSIDE", "url": "https://www.inside.com.tw/feed", "category": "tech", "lang": "zh"},

    # ===== World big news / 國際大事 =====
    {"name": "Reuters World", "url": "https://feeds.reuters.com/Reuters/worldNews", "category": "world", "lang": "en"},
    {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "category": "world", "lang": "en"},
    {"name": "AP Top News", "url": "https://feedx.net/rss/ap.xml", "category": "world", "lang": "en"},
    {"name": "中央社國際", "url": "https://feeds.feedburner.com/rsscna/intworld", "category": "world", "lang": "zh"},
]

# How many recent items to consider per source (last N entries)
MAX_ITEMS_PER_SOURCE = 8

# How many hours back to look (only include articles within this window)
LOOKBACK_HOURS = 30
