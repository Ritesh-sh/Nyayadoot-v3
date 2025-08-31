import re
import html
from collections import Counter
from typing import Set

# Define common stopwords
STOPWORDS: Set[str] = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
            'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as', 'of',
            'can', 'could', 'would', 'should', 'will', 'shall', 'may', 'might',
            'must', 'have', 'has', 'had', 'do', 'does', 'did', 'am', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'i', 'me', 'my', 'mine', 'myself',
            'you', 'your', 'yours', 'yourself', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'we', 'us',
            'our', 'ours', 'ourselves', 'they', 'them', 'their', 'theirs', 'themselves',
            'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at',
            'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up',
            'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
            'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain',
            'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven',
            'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn',
            'wasn', 'weren', 'won', 'wouldn', 'could', 'would', 'shall',
            'should', 'will', 'may', 'might', 'must', 'ought', 'able'}

# Define legal terms
LEGAL_TERMS = ['law', 'legal', 'right', 'duty', 'obligation', 'liability', 'contract', 
              'agreement', 'court', 'judge', 'judgment', 'case', 'precedent', 'statute',
              'act', 'section', 'clause', 'provision', 'regulation', 'rule']

def sanitize_query(query: str) -> str:
    """Sanitize and normalize user query for safe processing."""
    query = html.escape(query.strip())
    return re.sub(r'\s+', ' ', query)

def extract_keywords_from_conversation(conversation_history: str, query: str) -> str:
    """Extract keywords with a focus on legal relevance from conversation and query."""
    # Combine conversation and query
    all_text = f"{conversation_history} {query}".lower()
    
    # Split the text into words and filter out stopwords
    words = all_text.split()
    filtered_words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Get common words as keywords
    common_keywords = [word for word, count in word_counts.most_common(10) if count > 1]
    
    # Add legal-specific terms if found in the text
    legal_keywords = [term for term in LEGAL_TERMS if term in all_text]
    
    # Combine all keywords
    all_keywords = legal_keywords + common_keywords
    
    unique_keywords = list(set(all_keywords))
    
    if not unique_keywords:
        return "legal rights obligations duties"
    
    return ", ".join(unique_keywords[:15])
