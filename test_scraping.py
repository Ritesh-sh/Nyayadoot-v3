import sys
sys.path.append('1')  # Add the '1' directory to the path
from scraping.kanoon import fetch_kanoon_results

def test_fetch_kanoon():
    """Test the improved kanoon scraping functionality"""
    print("Testing kanoon scraping with a simple query...")
    results = fetch_kanoon_results("Theft IPC 379")
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet'][:100]}...")

if __name__ == "__main__":
    test_fetch_kanoon()
