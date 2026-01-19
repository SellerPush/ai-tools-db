import json
import asyncio
from datetime import datetime
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
import requests

MASTER_FILE = "ai-tools.json"
TAAFT_URLS = [
    "https://theresanaiforthat.com/trending/",
    "https://theresanaiforthat.com/ai-agents/"
]
HF_MODELS_API = "https://huggingface.co/api/models?sort=downloads&direction=-1&limit=30&pipeline_tag=text-generation"
GITHUB_SEARCH_API = "https://api.github.com/search/repositories?q=artificial-intelligence+OR+llm+OR+agents+language:JavaScript+stars:%3E100&sort=stars&order=desc&per_page=20"

# Ethical scraping: Add user-agent and delay
HEADERS = {'User-Agent': 'AI-Tools-Curator/1.0 (contact: your.email@example.com)'}

def load_existing():
    try:
        with open(MASTER_FILE, 'r') as f:
            return {t['tool'].lower(): t for t in json.load(f)}
    except FileNotFoundError:
        return {}

def save_tools(tools_list):
    with open(MASTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(tools_list, f, indent=2, ensure_ascii=False)

async def fetch_taaft_via_crawlee():
    crawler = PlaywrightCrawler(headless=True, request_handler_timeout_secs=60)
    tools = []

    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        page = context.page
        await page.wait_for_selector('.tool-item', timeout=30000)
        elements = await page.locator('.tool-item').all()

        for el in elements:
            try:
                name_elem = el.locator('.tool-name')
                name = await name_elem.inner_text(timeout=5000)
                url = await name_elem.get_attribute('href')
                full_url = f"https://theresanaiforthat.com{url}" if url else ""
                desc = await el.locator('.tool-description').inner_text(timeout=5000)
                cat_elem = el.locator('.tool-category')
                category = await cat_elem.inner_text(timeout=5000) if await cat_elem.count() > 0 else "General"
                tags_str = await el.locator('.tool-tags').inner_text(timeout=5000) if await el.locator('.tool-tags').count() > 0 else ""
                rating_str = await el.locator('.tool-rating').inner_text(timeout=5000) if await el.locator('.tool-rating').count() > 0 else "[0,0,0]"

                parts = rating_str.strip('[]').split(',')
                score = float(parts[-1].strip()) if len(parts) > 2 and parts[-1].strip() else 7.0

                keywords = [tag.strip('[]') for tag in tags_str.split()] if tags_str else []
                if "generative" in desc.lower() or "agent" in desc.lower():
                    keywords.append("generative" if "generative" in desc.lower() else "agents")

                if "agents" in category.lower() or "generative" in keywords or "agent" in keywords or "2026" in desc:
                    tools.append({
                        "tool": name.strip(),
                        "url": full_url,
                        "description": desc.strip(),
                        "category": category.strip(),
                        "keywords": keywords,
                        "score": score,
                        "lastUpdated": datetime.utcnow().isoformat(),
                        "source": "TAAFT"
                    })
            except Exception as e:
                print(f"Error parsing tool: {e}")

    for url in TAAFT_URLS:
        await crawler.run([url], request_handler=request_handler, request_headers=HEADERS)
        await asyncio.sleep(5)  # Polite delay

    return [t for t in tools if t["tool"] and t["url"]]

def fetch_huggingface():
    try:
        resp = requests.get(HF_MODELS_API, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        tools = []
        for i, m in enumerate(data):
            tags = m.get("tags", [])
            description = m.get("cardData", {}).get("description", "Hugging Face model")
            tools.append({
                "tool": m["id"],
                "category": "Open LLM (HF)",
                "keywords": tags[:4],
                "description": description,
                "score": 7.0 + (30 - i) / 10,
                "url": f"https://huggingface.co/{m['id']}",
                "lastUpdated": datetime.utcnow().isoformat(),
                "source": "Hugging Face"
            })
        return tools
    except Exception as e:
        print(f"Error fetching Hugging Face: {e}")
        return []

def fetch_github():
    try:
        resp = requests.get(GITHUB_SEARCH_API, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        tools = []
        for i, item in enumerate(items):
            tools.append({
                "tool": item["name"],
                "category": "GitHub AI Repo",
                "keywords": item.get("topics", [])[:4],
                "description": item.get("description", ""),
                "score": min(10, item.get("stargazers_count", 0) / 1000),
                "url": item["html_url"],
                "lastUpdated": datetime.utcnow().isoformat(),
                "source": "GitHub"
            })
        return tools
    except Exception as e:
        print(f"Error fetching GitHub: {e}")
        return []

# Optional: Add more sources (e.g., Toolify scrape)
def fetch_toolify():
    try:
        resp = requests.get("https://www.toolify.ai/best-ai-tools", headers=HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        tools = []
        for item in soup.select('.tool-card'):  # Adjust based on site structure (inspect element)
            name = item.select_one('.tool-name').text.strip()
            url = item.select_one('a')['href']
            desc = item.select_one('.tool-desc').text.strip()
            tools.append({
                "tool": name,
                "url": f"https://www.toolify.ai{url}",
                "description": desc,
                "source": "Toolify",
                "lastUpdated": datetime.utcnow().isoformat()
            })
        return tools[:30]
    except Exception as e:
        print(f"Error fetching Toolify: {e}")
        return []

async def main():
    existing = load_existing()

    new_items = []
    new_items.extend(await fetch_taaft_via_crawlee())
    new_items.extend(fetch_huggingface())
    new_items.extend(fetch_github())
    new_items.extend(fetch_toolify())  # Add this for more tools

    for tool in new_items:
        key = tool["tool"].lower()
        if key in existing:
            existing[key].update(tool)
        else:
            existing[key] = tool

    updated_list = list(existing.values())
    updated_list.sort(key=lambda x: x.get("score", 0) + (2 if "agents" in x.get("category", "").lower() or "generative" in str(x.get("keywords", "")) else 0), reverse=True)

    for i, t in enumerate(updated_list, 1):
        t["rank"] = i

    save_tools(updated_list)
    print(f"Saved {len(updated_list)} tools (focused on agents & generative AI)")

if __name__ == "__main__":
    asyncio.run(main())
