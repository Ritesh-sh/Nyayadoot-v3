import google.generativeai as genai
import os
import re

def gemini_generate(prompt: str, max_tokens: int = None, temperature: float = 0.7) -> str:
    """Generate text using Google's Gemini API with API key from environment."""
    # Implement the actual Gemini API call
    # This is a placeholder - implement with actual API logic
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        generation_config = {
            "temperature": temperature,
            "top_p": 1,
            "top_k": 1,
        }
        
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        model = genai.GenerativeModel('gemini-2.0-flash-lite', generation_config=generation_config)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "Error generating response"

def generate_with_gemini(prompt: str) -> str:
    """Generate text using Gemini API with fallback."""
    try:
        if len(prompt) > 1000:
            prompt_lines = prompt.split('\n')
            if len(prompt_lines) > 20:
                prompt = '\n'.join(prompt_lines[:10] + ['\n...[content trimmed]...\n'] + prompt_lines[-10:])
        if len(prompt) > 6000:
            prompt = prompt[:1500] + "\n...[content trimmed]...\n" + prompt[-1500:]
        print(f"Prompt length: {len(prompt)} characters")
        return gemini_generate(prompt)
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm having trouble connecting to my knowledge source. For legal matters, it's always best to consult with a qualified attorney who can provide personalized advice."

def is_legal_query_gemini(query: str, conversation_history: str = "") -> bool:
    """Uses Gemini to determine if the query is legal in nature, considering conversation context."""
    # Check if the query itself is too short to be meaningful
    if len(query.strip()) < 5:
        return True  # Assume it's part of a legal conversation
    
    # If we have conversation history, always treat follow-up messages as part of the legal conversation
    if conversation_history:
        # Check if this is likely a direct follow-up to a question about details
        if "have you" in conversation_history.lower() or "do you" in conversation_history.lower() or "could you" in conversation_history.lower() or "please provide" in conversation_history.lower():
            if "yes" in query.lower() or "no" in query.lower() or "i did" in query.lower() or "i didn't" in query.lower() or "i have" in query.lower() or "i don't" in query.lower():
                print("Detected follow-up response to a question, treating as LEGAL")
                return True
        
        # Check if the conversation history contains obvious legal topics
        legal_keywords = ["law", "legal", "police", "fir", "complaint", "court", "theft", "stolen", "insurance", "section", "ipc", "crpc"]
        for keyword in legal_keywords:
            if keyword in conversation_history.lower():
                # If legal keywords are in history and this is a short response, it's likely continuing the legal conversation
                if len(query.split()) < 15:
                    print(f"Detected short follow-up to legal topic containing '{keyword}', treating as LEGAL")
                    return True
                    
        # Extract a brief summary for context
        if len(conversation_history) > 200:
            history_parts = conversation_history.split("\n\n")
            conversation_context = history_parts[-1] if history_parts else conversation_history[:200]
        else:
            conversation_context = conversation_history
            
        prompt = f"""You are a classifier. Decide if this user query is either a legal question OR a follow-up to a previous legal discussion.
Consider the conversation context carefully. If the user is answering a question about a legal situation, classify as LEGAL.
Reply with only 'LEGAL' or 'NOT LEGAL'.

Conversation context: {conversation_context}

Query: "{query}"
"""
    else:
        # No conversation history, just evaluate the query directly
        prompt = f"""You are a classifier. Decide if the following user query is a legal question (about laws, rights, legal procedures, court cases, contracts, etc).
Reply with only 'LEGAL' or 'NOT LEGAL'.

Query: "{query}"
"""
    try:
        result = gemini_generate(prompt, max_tokens=5, temperature=0.0).strip().upper()
        return result == "LEGAL"
    except Exception as e:
        print(f"Error in legal query classification: {e}")
        return True  # Default to assuming it's legal if we can't classify

def generate_direct_answer(query: str, context: str = "", conversation_history: str = "", is_followup: bool = False, max_tokens: int = 256) -> str:
    """Generate a direct answer with simplified context to reduce tokens."""
    # Always use conversation history to be more context-aware
    
    # Limit conversation history to reduce tokens
    if conversation_history and len(conversation_history) > 300:
        # Extract just the last exchange or two - more focused context
        parts = conversation_history.split("\n\n")
        if len(parts) > 2:
            conversation_history = "\n\n".join(parts[-2:])
    
    # Check for impact queries to use a more focused system prompt
    is_impact_query = "impact" in query.lower() or "consequence" in query.lower() or "effect" in query.lower()
    
    # Build the prompt
    if is_impact_query:
        system_prompt = (
            "You are an Indian legal assistant specializing in practical legal impacts. "
            "Focus ONLY on consequences, penalties, and next steps. "
            "Be extremely concise (max 200 tokens). "
            "Your response should be structured as a short list of practical points. "
            "For impact queries, never discuss legal theory - focus on practical consequences only."
        )
    else:
        system_prompt = (
            "You are an Indian legal assistant powered by a large language model. "
            "You answer ONLY questions about Indian law. "
            "Be extremely concise (max 256 tokens). "
            "Don't provide disclaimers unless absolutely necessary. "
            "When case URLs are provided in your context, ALWAYS include them in your answer. "
            "Format case references as: [Case Name](URL). "
            "Preserve ALL URLs exactly as provided. "
            "For non-legal questions, politely redirect to legal topics only."
        )
    
    # Extract and preserve case URLs
    preserved_urls = []
    url_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    url_matches = url_pattern.findall(context)
    for case_name, url in url_matches:
        preserved_urls.append((case_name, url))
    
    # Optimize context to focus on most relevant information
    if context and len(context) > 400:
        context_lines = context.split('\n')
        context = '\n'.join(context_lines[:5])  # Only use most important context
        
    # Add a special instruction for preserved URLs
    if preserved_urls:
        context += "\n\nIMPORTANT: Include these case references with exact URLs:\n"
        for case_name, url in preserved_urls:
            context += f"- [{case_name}]({url})\n"
    
    context_part = f"\nRelevant context:\n{context}" if context else ""
    history_part = f"\nPrevious conversation:\n{conversation_history}" if conversation_history else ""
    
    # Check if this is an impact query to use a more specific format
    if "impact" in query.lower() or "consequence" in query.lower() or "effect" in query.lower():
        prompt = f"""{system_prompt}{context_part}{history_part}

Question: {query}

Answer with only the practical impact and next steps, under {max_tokens} tokens:
1. Immediate consequences: 
2. Legal remedies: 
3. Next steps:"""
    else:
        prompt = f"{system_prompt}{context_part}{history_part}\n\nQuestion: {query}\n\nAnswer (be concise, under {max_tokens} tokens):"
    
    # Generate answer with strict token limit
    try:
        answer = gemini_generate(prompt, max_tokens=max_tokens, temperature=0.5)
        
        # If non-legal question is detected and no context available, use standard response
        if "rephrase your question" in answer.lower() or "focus on a legal topic" in answer.lower():
            non_legal_response = (
                "I'm designed to help with legal questions related to Indian law. "
                "Could you please ask me about Indian laws, legal procedures, rights, or related topics?"
            )
            return non_legal_response
            
        # Check for truncated URLs and fix them
        if "](http" in answer and ")" not in answer.split("](http")[-1]:
            # URL got truncated, let's fix by regenerating with lower token limit
            print("URL truncation detected, regenerating with lower token limit")
            reduced_tokens = max(100, max_tokens - 50)  # Reduce by 50 tokens or set to 100 minimum
            answer = gemini_generate(prompt, max_tokens=reduced_tokens, temperature=0.5)
            
        # Fall back to simpler prompt if failed or result is too short
        if not answer or len(answer) < 20:
            simpler_prompt = f"Answer this legal question about Indian law in {max_tokens} tokens or less: {query}"
            answer = gemini_generate(simpler_prompt, max_tokens=max_tokens)
            
        return answer
    except Exception as e:
        print(f"Error in generating direct answer: {e}")
        return "I'm unable to generate a response at the moment. Please try again later."
