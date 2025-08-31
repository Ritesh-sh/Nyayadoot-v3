from typing import List, Dict
from ai.gemini import generate_with_gemini

def find_relevant_sections(query: str, conversation_history: str = "") -> List[Dict]:
    """Use Gemini to suggest relevant Act/Section pairs directly (no local mapping)."""
    try:
        context = f"Previous: {conversation_history}\n" if conversation_history else ""
        prompt = (
            "You are a legal assistant for Indian law. Given the user's question, "
            "suggest up to 3 highly relevant statute sections as ActName|SectionNumber|Why.\n"
            "Only output lines in this exact pipe-delimited format, no extra text.\n"
            f"{context}Question: {query}"
        )
        raw = generate_with_gemini(prompt)
        lines = [l.strip() for l in raw.split('\n') if '|' in l]

        suggestions = []
        for line in lines:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 2:
                act_s, sec_s = parts[0], parts[1]
                why = parts[2] if len(parts) >= 3 else "Relevant legal provision"
                suggestions.append((act_s, sec_s, why))

        results: List[Dict] = []
        for act_s, sec_s, why in suggestions:
            results.append({
                'act': act_s,
                'section_number': sec_s,
                'summary': why
            })
            if len(results) >= 3:
                break
                
        return results
    except Exception as e:
        print(f"Gemini section retrieval error: {e}")
        return []
