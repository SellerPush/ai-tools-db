# update_ai_tools.py
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup  # pip install beautifulsoup4 requests

# ── CONFIG ───────────────────────────────────────────────────────────────
MASTER_FILE = "ai-tools.json"
SOURCES = {
    "toolify": {
        "url": "https://www.toolify.ai/best-ai-tools",
        "method": "scrape",  # or "api"
        "category_map": {"LLM Platform": "Chatbot", ...}
    },
    "futurepedia": {
        "url": "https://www.futurepedia.io/api/tools?limit=50&sort=popular",
        "method": "api"
    },
    # Add more...
}

def load_existing():
    try:
        with open(MASTER_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_tools(tools):
    with open(MASTER_FILE, 'w') as f:
        json.dump(tools, f, indent=2)

def fetch_toolify():
    # Example: simple scrape (respect robots.txt!)
    headers = {'User-Agent': 'AI-Tools-Curator/1.0 (your.email@example.com)'}
    resp = requests.get("https://www.toolify.ai/best-ai-tools", headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')

    tools = []
    for item in soup.select('.tool-card'):  # Adjust selector after inspecting page
        name = item.select_one('.tool-name').text.strip()
        url = item.select_one('a')['href']
        desc = item.select_one('.tool-desc').text.strip()
        tools.append({
            "tool": name,
            "url": f"https://www.toolify.ai{url}",
            "description": desc,
            "source": "toolify",
            "lastUpdated": datetime.utcnow().isoformat()
        })
    return tools[:30]  # top 30

def fetch_futurepedia():
    try:
        resp = requests.get(SOURCES["futurepedia"]["url"])
        data = resp.json()
        return [{
            "tool": item["name"],
            "url": item["url"],
            "description": item.get("description", ""),
            "source": "futurepedia",
            "lastUpdated": datetime.utcnow().isoformat()
        } for item in data.get("tools", [])[:30]]
    except:
        return []

# ── MAIN ─────────────────────────────────────────────────────────────────
existing = load_existing()
existing_dict = {t["tool"].lower(): t for t in existing}

new_tools = []
new_tools.extend(fetch_toolify())
new_tools.extend(fetch_futurepedia())
# Add more fetchers...

# Merge: update existing, add new ones
for tool in new_tools:
    key = tool["tool"].lower()
    if key in existing_dict:
        # Update fields
        existing_dict[key].update(tool)
    else:
        existing_dict[key] = tool

# Re-sort by score or rank (you can add logic here)
updated_list = list(existing_dict.values())
updated_list.sort(key=lambda x: x.get("score", 0), reverse=True)

# Re-assign ranks
for i, tool in enumerate(updated_list, 1):
    tool["rank"] = i

save_tools(updated_list)

print(f"Updated {len(updated_list)} tools → {MASTER_FILE}")
