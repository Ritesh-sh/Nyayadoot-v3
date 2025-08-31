from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal
import uuid
import re

from conversation.state import ConversationState
from scraping.kanoon import fetch_kanoon_results, fetch_specific_case_from_kanoon

# Function to extract case names from text
def extract_case_names(text: str) -> List[str]:
    """Extract potential case names from text."""
    # Pattern to look for "X v. Y" or "X vs Y" patterns
    vs_pattern = re.compile(r'([A-Za-z\s\.]+)\s+(?:v\.?|vs\.?)\s+([A-Za-z\s\.]+)')
    matches = vs_pattern.findall(text)
    
    case_names = []
    for match in matches:
        # Combine both parts of the case name
        full_name = f"{match[0].strip()} vs. {match[1].strip()}"
        case_names.append(full_name)
    
    return case_names

# Function to handle specific case lookup requests
async def handle_case_lookup(query: str, conversation_history: str = ""):
    """Handle requests specifically looking for case information."""
    
    # Extract case names from the query
    case_names = extract_case_names(query)
    
    # If no case names found in the direct format, search using the query
    if not case_names:
        # Use general search
        results = fetch_kanoon_results(query, conversation_history)
        if results:
            # Format the response with proper links
            response_parts = []
            for case in results[:3]:
                title = case.get('title', 'Untitled Case')
                url = case.get('url', '')
                snippet = case.get('snippet', '')
                
                # Format as markdown link with brief description
                case_text = f"[{title}]({url}) - {snippet[:100]}..."
                response_parts.append(case_text)
                
            # Combine into final response
            if response_parts:
                return "\n\n".join(response_parts)
    else:
        # Look up specific cases
        results = []
        for case_name in case_names[:2]:  # Limit to 2 for token efficiency
            case = fetch_specific_case_from_kanoon(case_name)
            if case and case.get('url'):
                title = case.get('title', case_name)
                url = case.get('url', '')
                snippet = case.get('snippet', '')
                
                # Format as markdown link
                case_text = f"[{title}]({url}) - {snippet[:100]}..."
                results.append(case_text)
                
        if results:
            return "\n\n".join(results)
                
    # If no results or extraction failed
    return "I couldn't find specific case information. Please try rephrasing your query with more details about the case."
