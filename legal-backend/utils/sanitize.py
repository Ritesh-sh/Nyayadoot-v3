import html
import re

def sanitize_query(query: str) -> str:
    """Sanitize and normalize user query for safe processing."""
    query = html.escape(query.strip())
    return re.sub(r'\s+', ' ', query)
