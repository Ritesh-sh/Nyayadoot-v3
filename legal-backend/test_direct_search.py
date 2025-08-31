from scraping.kanoon import fetch_kanoon_results
import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict

def test_direct_search():
    """Test direct search without using Gemini API at all"""
    print("\n=== Testing direct search with specific IPC term ===")
    query = "IPC 379"
    print(f"Searching for: '{query}'")
    
    url = f"https://indiankanoon.org/search/?formInput={requests.utils.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    resp = requests.get(url, headers=headers, timeout=20)
    print(f"Response status code: {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, "html.parser")
    case_elements = soup.select("div.result_title > a")
    print(f"Number of case elements found: {len(case_elements)}")
    
    if case_elements:
        element = case_elements[0]
        title = element.get_text(strip=True)
        case_url = element.get("href")
        if case_url and not case_url.startswith("http"):
            case_url = f"https://indiankanoon.org{case_url}"
        print(f"First result title: {title}")
        print(f"URL: {case_url}")
    else:
        print("No results found")

def main():
    """Test searching directly with Indian Kanoon"""
    print("Testing direct search...")
    test_direct_search()

if __name__ == "__main__":
    main()
