import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict
from keywords.extractor import extract_keywords_from_conversation
from ai.gemini import generate_with_gemini

def fetch_kanoon_results(query: str, conversation_history: str = "") -> List[Dict]:
    """Fetch case law results from Indian Kanoon using a Gemini-generated search phrase and filter for relevance. Retry on timeout."""
    # Improve Gemini prompt for more relevant case law search
    context = f"Query: {query}\nHistory: {conversation_history}" if conversation_history else query
    prompt = (
        "You are a legal assistant for Indian law. Given the user's question and context, generate a search phrase that will find the most relevant and diverse Indian case law on Indian Kanoon. Focus on legal principles, parties, and jurisdiction. Only output the search phrase, no extra text.\n\n"
        f"{context}"
    )
    
    # Extract potential legal terms from the query first
    legal_terms = []
    query_words = query.split()
    
    # Look for patterns like "IPC 379" or "Section 420"
    for i, word in enumerate(query_words):
        if word.upper() in ["IPC", "CRPC", "SECTION"] and i+1 < len(query_words) and query_words[i+1].isdigit():
            legal_terms.append(f"{word} {query_words[i+1]}")
    
    try:
        search_phrase = generate_with_gemini(prompt)
        print(f"Gemini search phrase: {search_phrase}")
        # Fallback to original query if Gemini output is too generic or short
        if not search_phrase or len(search_phrase.strip()) < 5 or search_phrase == "Error generating response":
            if legal_terms:
                search_phrase = " ".join(legal_terms) + " " + query
            else:
                search_phrase = query
    except Exception as e:
        print(f"Gemini search phrase error: {e}")
        # If Gemini fails, use extracted legal terms if available, otherwise use original query
        if legal_terms:
            search_phrase = " ".join(legal_terms)
        else:
            # Extract key legal terms if possible
            search_terms = []
            for word in query.split():
                if word.upper() in ["IPC", "CRPC", "SECTION", "ACT", "THEFT", "FIR", "POLICE", "CRIMINAL"] or word.isdigit():
                    search_terms.append(word)
            
            # If we found legal terms, use them, otherwise use the full query
            if search_terms:
                search_phrase = " ".join(search_terms)
            else:
                search_phrase = query
        
    # Format the search phrase to be more Indian Kanoon friendly
    # Remove quotes and excessive operators that might be causing zero results
    search_phrase = search_phrase.replace('"', '').replace('\n', ' ').strip()
    # If search phrase is very long, try to truncate it to essential keywords
    if len(search_phrase.split()) > 10:
        # Keep only the most significant terms
        important_words = [word for word in search_phrase.split() if len(word) > 3 or word.upper() in ["IPC", "FIR", "CrPC"]]
        search_phrase = " ".join(important_words[:8])  # Limit to 8 important terms
    
    print(f"[DEBUG] Simplified search phrase: {search_phrase}")
    url = f"https://indiankanoon.org/search/?formInput={requests.utils.quote(search_phrase)}"
    max_retries = 2
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    for attempt in range(max_retries + 1):
        try:
            print(f"[DEBUG] Fetching URL: {url}")
            resp = requests.get(url, headers=headers, timeout=20)
            print(f"[DEBUG] Response status code: {resp.status_code}")
            print(f"[DEBUG] First 500 chars of response:\n{resp.text[:500]}")
            
            # Ensure we got a valid response
            if resp.status_code != 200 or not resp.text:
                print(f"[DEBUG] Invalid response: status={resp.status_code}, content_length={len(resp.text)}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                else:
                    return [{
                        "title": "Indian Kanoon is currently unavailable",
                        "url": "https://indiankanoon.org/",
                        "snippet": f"Sorry, we could not retrieve case law results. Status code: {resp.status_code}"
                    }]
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Try the primary selector
            case_elements = soup.select("div.result_title > a")
            print(f"[DEBUG] Number of case elements found: {len(case_elements)}")
            
            # If no results, try alternative selectors
            if len(case_elements) == 0:
                print("[DEBUG] Looking for results with different selectors")
                
                # Check for result containers
                result_divs = soup.select('div.result')
                print(f"[DEBUG] Result divs found: {len(result_divs)}")
                
                if len(result_divs) > 0:
                    # Extract case elements from result divs
                    case_elements = []
                    for div in result_divs:
                        links = div.select('div.result_title > a')
                        if links:
                            case_elements.extend(links)
                
                # If still no results, try direct link selector
                if len(case_elements) == 0:
                    case_elements = soup.select('a[href*="/doc/"]')
                    print(f"[DEBUG] Using doc links selector: {len(case_elements)} results")
            
            case_results = []
            seen_titles = set()
            seen_urls = set()
            
            for element in case_elements:
                title = element.get_text(strip=True)
                case_url = element.get("href")
                if case_url and not case_url.startswith("http"):
                    case_url = f"https://indiankanoon.org{case_url}"
                
                # Find snippet - look in parent result div
                snippet = ""
                parent_result = element.find_parent("div", class_="result")
                if parent_result:
                    headline = parent_result.select_one("div.headline")
                    if headline:
                        snippet = headline.get_text(strip=True)
                
                # Fall back to looking for snippet directly
                if not snippet:
                    snippet_element = None
                    if element.find_parent("div", class_="result_title"):
                        snippet_element = element.find_parent("div", class_="result_title").find_next_sibling("div", class_="snippet") or \
                                          element.find_parent("div", class_="result_title").find_next_sibling("div", class_="headline")
                    
                    if snippet_element:
                        snippet = snippet_element.get_text(strip=True)
                    else:
                        snippet = title
                
                # Filter out duplicate cases by title and URL
                title_key = title.lower().replace("...", "").strip()
                if title_key in seen_titles or (case_url and case_url in seen_urls):
                    continue
                
                case_results.append({
                    "title": title[:80],
                    "url": case_url,
                    "snippet": snippet[:250] if snippet else ""
                })
                seen_titles.add(title_key)
                if case_url:
                    seen_urls.add(case_url)
                if len(case_results) == 3:
                    break
                    
            if case_results:
                return case_results
            else:
                if attempt < max_retries:
                    time.sleep(2)
                    # If this is the last retry and we're using a complex search phrase
                    # Try with a simpler search query by extracting key terms
                    if attempt == max_retries - 1 and " " in search_phrase:
                        print("[DEBUG] No results with complex query, trying with simpler keywords")
                        # Extract key legal terms like IPC sections, Acts, etc.
                        key_terms = []
                        for word in search_phrase.split():
                            if any(term in word.upper() for term in ["IPC", "CRPC", "ACT", "SECTION"]):
                                key_terms.append(word)
                        # Add a few other important words if we have less than 3 key terms
                        if len(key_terms) < 3:
                            non_key_terms = [w for w in search_phrase.split() if w not in key_terms and len(w) > 4]
                            key_terms.extend(non_key_terms[:3])
                        
                        # If we found key terms, retry with them
                        if key_terms:
                            simple_query = " ".join(key_terms[:5])  # Use top 5 key terms
                            url = f"https://indiankanoon.org/search/?formInput={requests.utils.quote(simple_query)}"
                            print(f"[DEBUG] Retrying with simplified query: {simple_query}")
                else:
                    # Try one last desperate attempt with just the most important keywords
                    # This is outside the retry loop as a last resort
                    try:
                        # Extract potential IPC sections or legal codes
                        legal_codes = []
                        original_query = query.upper()
                        
                        # Look for IPC sections
                        if "IPC" in original_query or "SECTION" in original_query:
                            ipc_terms = [word for word in original_query.split() if word.isdigit() and len(word) == 3]
                            if ipc_terms:
                                last_query = f"IPC {ipc_terms[0]}"
                                print(f"[DEBUG] Last resort query: {last_query}")
                                last_url = f"https://indiankanoon.org/search/?formInput={requests.utils.quote(last_query)}"
                                last_resp = requests.get(last_url, headers=headers, timeout=10)
                                if last_resp.status_code == 200:
                                    last_soup = BeautifulSoup(last_resp.text, "html.parser")
                                    last_elements = last_soup.select("div.result_title > a") or last_soup.select('a[href*="/doc/"]')
                                    if last_elements and len(last_elements) > 0:
                                        # Process these results as a last resort
                                        element = last_elements[0]
                                        title = element.get_text(strip=True)
                                        url = element.get("href")
                                        if url and not url.startswith("http"):
                                            url = f"https://indiankanoon.org{url}"
                                        return [{
                                            "title": title[:80],
                                            "url": url,
                                            "snippet": f"Related to {last_query}. Note: This result is based on simplified search terms."
                                        }]
                    except Exception as e:
                        print(f"[DEBUG] Last resort search failed: {e}")
                        
                    # If all else fails, return the standard error message
                    return [{
                        "title": "Indian Kanoon is currently unavailable",
                        "url": "https://indiankanoon.org/",
                        "snippet": "Sorry, we could not retrieve case law results at this time. Please try again later."
                    }]
        except requests.exceptions.Timeout:
            print(f"Kanoon timeout on attempt {attempt+1}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                return [{
                    "title": "Indian Kanoon is currently unavailable",
                    "url": "https://indiankanoon.org/",
                    "snippet": "Sorry, we could not retrieve case law results due to a timeout. Please try again later."
                }]
        except Exception as e:
            print(f"Kanoon error: {e}")
            return [{
                "title": "Indian Kanoon is currently unavailable",
                "url": "https://indiankanoon.org/",
                "snippet": "Sorry, we could not retrieve case law results due to a technical error. Please try again later."
            }]

def fetch_specific_case_from_kanoon(case_name: str) -> Dict:
    """Search for a specific case name on Indian Kanoon and return the most relevant result."""
    print(f"Searching for specific case: {case_name}")
    try:
        search_query = f'"{case_name}"'
        url = f"https://indiankanoon.org/search/?formInput={requests.utils.quote(search_query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        print(f"[DEBUG] Fetching URL: {url}")
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"[DEBUG] Response status code: {resp.status_code}")
        print(f"[DEBUG] First 500 chars of response:\n{resp.text[:500]}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Try different selectors to find case elements
        case_elements = soup.select("div.result_title > a")
        print(f"[DEBUG] Number of case elements found: {len(case_elements)}")
        
        # If no results with original selector, try alternative approaches
        if len(case_elements) == 0:
            # Try checking result divs first
            result_divs = soup.select('div.result')
            print(f"[DEBUG] Result divs found: {len(result_divs)}")
            
            if len(result_divs) > 0:
                # Extract case elements from result divs
                for div in result_divs:
                    links = div.select('div.result_title > a')
                    if links:
                        case_elements = links
                        break
            
            # If still no results, try direct link selector
            if len(case_elements) == 0:
                case_elements = soup.select('a[href*="/doc/"]')
                print(f"[DEBUG] Using doc links selector: {len(case_elements)} results")
        
        if case_elements:
            element = case_elements[0]
            title = element.get_text(strip=True)
            case_url = element.get("href")
            if case_url and not case_url.startswith("http"):
                case_url = f"https://indiankanoon.org{case_url}"
            
            # Find snippet - look in parent result div
            snippet = ""
            parent_result = element.find_parent("div", class_="result")
            if parent_result:
                headline = parent_result.select_one("div.headline")
                if headline:
                    snippet = headline.get_text(strip=True)
            
            # Fall back to looking for snippet directly
            if not snippet:
                snippet_element = None
                if element.find_parent("div", class_="result_title"):
                    snippet_element = element.find_parent("div", class_="result_title").find_next_sibling("div", class_="snippet") or \
                                      element.find_parent("div", class_="result_title").find_next_sibling("div", class_="headline")
                
                if snippet_element:
                    snippet = snippet_element.get_text(strip=True)
                else:
                    snippet = title
            
            return {
                "title": title[:80],
                "url": case_url,
                "snippet": snippet[:250] if snippet else "",
                "case_name": case_name
            }
        else:
            # Try without quotes if no results found
            url = f"https://indiankanoon.org/search/?formInput={requests.utils.quote(case_name)}"
            print(f"[DEBUG] Trying without quotes. Fetching URL: {url}")
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"[DEBUG] Response status code: {resp.status_code}")
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Try the same selector hierarchy as above
            case_elements = soup.select("div.result_title > a")
            print(f"[DEBUG] Number of case elements found: {len(case_elements)}")
            
            if len(case_elements) == 0:
                # Try checking result divs first
                result_divs = soup.select('div.result')
                if result_divs:
                    for div in result_divs:
                        links = div.select('div.result_title > a')
                        if links:
                            case_elements = links
                            break
                
                # If still no results, try direct link selector
                if len(case_elements) == 0:
                    case_elements = soup.select('a[href*="/doc/"]')
                    print(f"[DEBUG] Using doc links selector: {len(case_elements)} results")
            
            if case_elements:
                element = case_elements[0]
                title = element.get_text(strip=True)
                case_url = element.get("href")
                if case_url and not case_url.startswith("http"):
                    case_url = f"https://indiankanoon.org{case_url}"
                
                # Find snippet - look in parent result div
                snippet = ""
                parent_result = element.find_parent("div", class_="result")
                if parent_result:
                    headline = parent_result.select_one("div.headline")
                    if headline:
                        snippet = headline.get_text(strip=True)
                
                # Fall back to looking for snippet directly
                if not snippet:
                    snippet_element = None
                    if element.find_parent("div", class_="result_title"):
                        snippet_element = element.find_parent("div", class_="result_title").find_next_sibling("div", class_="snippet") or \
                                          element.find_parent("div", class_="result_title").find_next_sibling("div", class_="headline")
                    
                    if snippet_element:
                        snippet = snippet_element.get_text(strip=True)
                    else:
                        snippet = title
                
                return {
                    "title": title[:80],
                    "url": case_url,
                    "snippet": snippet[:250] if snippet else "",
                    "case_name": case_name
                }
                
        # If all attempts failed, return a fallback
        return {
            "title": f"Case: {case_name}",
            "url": f"https://indiankanoon.org/search/?formInput={case_name.replace(' ', '+')}",
            "snippet": f"This case was mentioned in the legal analysis but couldn't be found directly on Indian Kanoon.",
            "case_name": case_name
        }
    except Exception as e:
        print(f"Error searching for specific case: {e}")
        return {
            "title": f"Case: {case_name}",
            "url": f"https://indiankanoon.org/search/?formInput={case_name.replace(' ', '+')}",
            "snippet": "Could not retrieve case details due to technical issues.",
            "case_name": case_name
        }

def fetch_cases_from_api_suggestions(api_response: str) -> List[Dict]:
    """Use extracted keywords to fetch top 3 cases from Indian Kanoon."""
    # Extract keywords from the API response
    keywords = extract_keywords_from_conversation("", api_response)
    print(f"[DEBUG] Extracted keywords for case search: {keywords}")
    # Fetch top 3 cases using keyword search
    results = fetch_kanoon_results(keywords)
    return results[:3]  # Return up to 3 results
