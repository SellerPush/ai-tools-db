import json
import requests
from datetime import datetime
import os

# Configuration
MASTER_FILE = "ai-tools.json"
SOURCES = {
    "toolify": "https://www.toolify.ai/api/best-ai-tools", # Example API endpoint
    "futurepedia": "https://www.futurepedia.io/api/tools?limit=50&sort=popular",
    "huggingface": "https://huggingface.co/api/models?pipeline_tag=text-generation&sort=downloads"
}

def load_existing():
    if os.path.exists(MASTER_FILE):
        with open(MASTER_FILE, 'r') as f: return json.load(f)
    return []

def scrape_new_discoveries():
    # Placeholder for actual API/Scraping logic for tools like zchat.ai, 365 AI, etc.
    new_tools = [
        {"tool": "zchat.ai", "category": "AI Search / RAG", "url": "https://zchat.ai", "description": "AI-powered real-time search and chat platform.", "score": 8.5},
        {"tool": "365 AI", "category": "General Assistant", "url": "https://www.365ai.com", "description": "Versatile productivity AI for the Chinese market.", "score": 8.2},
        {"tool": "Llama 3 (Meta)", "category": "Open LLM", "url": "https://ai.meta.com/llama/", "description": "Meta's state-of-the-art open source large language model.", "score": 9.5}
    ]
    return new_tools

def update_directory():
    existing = load_existing()
    existing_dict = {t["tool"].lower(): t for t in existing}
    
    # Merge new tools
    for tool in scrape_new_discoveries():
        key = tool["tool"].lower()
        tool["lastUpdated"] = datetime.utcnow().strftime('%Y-%m-%d')
        existing_dict[key] = tool # This updates existing or adds new

    # Sort by score and save
    updated_list = sorted(existing_dict.values(), key=lambda x: x.get('score', 0), reverse=True)
    with open(MASTER_FILE, 'w') as f:
        json.dump(updated_list, f, indent=2)

if __name__ == "__main__":
    update_directory()
