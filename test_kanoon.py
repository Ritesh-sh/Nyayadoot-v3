import requests
from bs4 import BeautifulSoup

def test_kanoon_structure():
    url = "https://indiankanoon.org/search/?formInput=Theft"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Testing URL: {url}")
    resp = requests.get(url, headers=headers)
    print(f"Status code: {resp.status_code}")
    
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Check page title
        print(f"Page title: {soup.title.text if soup.title else 'No title'}")
        
        # Check original selectors
        result_title_links = soup.select("div.result_title > a")
        print(f"Original selector 'div.result_title > a': {len(result_title_links)}")
        
        # Try alternative selectors
        print("\nTrying alternative selectors:")
        selectors_to_check = [
            "div.result_title",
            "div.docTitle",
            "div.res_blck",
            ".docTitle",
            ".res_itm",
            ".resTitle",
            "div.result",
            ".result a",
            ".search_result",
            ".search_results div",
            "div.search_result a",
            "a[href*='/doc/']"
        ]
        
        for selector in selectors_to_check:
            elements = soup.select(selector)
            print(f"'{selector}': {len(elements)}")
            if len(elements) > 0:
                print(f"  First match: {elements[0]}")
        
        # Save a sample of the HTML for inspection
        with open("kanoon_sample.html", "w", encoding="utf-8") as f:
            f.write(str(soup.select("body")[0]) if soup.select("body") else "No body found")
        print("\nSaved HTML sample to kanoon_sample.html for inspection")
    else:
        print(f"Failed to fetch the page. Status code: {resp.status_code}")

if __name__ == "__main__":
    test_kanoon_structure()
