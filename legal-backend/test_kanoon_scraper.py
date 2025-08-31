from scraping.kanoon import fetch_kanoon_results
from ai.gemini import generate_with_gemini

def test_direct_search():
    """Test the Indian Kanoon scraping directly without Gemini API"""
    print("\n=== Testing direct kanoon search without Gemini API ===")
    print("Searching for: 'Theft IPC 379'")
    
    # This bypasses the Gemini API by directly passing a query that would be used for searching
    results = fetch_kanoon_results("Theft IPC 379")
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet'][:100]}...")
    
    return len(results) > 0

def test_complex_search():
    """Test searching with a complex query string (similar to what Gemini might generate)"""
    print("\n=== Testing complex search query handling ===")
    complex_query = '"theft of motor vehicle FIR CrPC 154 IPC 379 Motor Vehicles Act 158 insurance claim police investigation"'
    print(f"Complex search query: {complex_query}")
    
    results = fetch_kanoon_results(complex_query)
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet'][:100]}...")
    
    return len(results) > 0

def main():
    """Test the improved kanoon scraping functionality"""
    print("Testing kanoon scraping with updated code...")
    
    # Test direct search first
    direct_search_success = test_direct_search()
    
    # Test complex search
    complex_search_success = test_complex_search()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Direct search success: {direct_search_success}")
    print(f"Complex search success: {complex_search_success}")

if __name__ == "__main__":
    main()
