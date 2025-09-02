from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import List, Dict, Optional, Literal
import uuid
import re
import random

from conversation.state import ConversationState
from utils.sanitize import sanitize_query
from utils.responses import get_contextual_redirect, NON_LEGAL_RESPONSES
from utils.case_helper import handle_case_lookup, extract_case_names
from keywords.extractor import extract_keywords_from_conversation
from retrieval.section import find_relevant_sections
from scraping.kanoon import fetch_kanoon_results, fetch_cases_from_api_suggestions
from ai.gemini import generate_with_gemini, is_legal_query_gemini, generate_direct_answer

# Create router
router = APIRouter(prefix="/nyayadoot")

# Initialize conversation state
conv_state = ConversationState()

# Request and response models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    
class QueryResponse(BaseModel):
    answer: str
    references: List[Dict] = []
    cases: List[Dict] = []
    session_id: str
    conversation_stage: str = "initial"  # Added field to track conversation stage

# Define conversation stages and keyword patterns
CONVERSATION_STAGES = {
    "initial": "Ask for more details",
    "details": "Provide legal information",
    "sections": "Show legal sections",
    "cases": "Show relevant cases",
    "impact": "Explain legal impact",
    "followup": "Continue conversation"
}

# Helper to detect query intent
def detect_query_intent(query: str, conversation_history: str = "") -> str:
    """Detect the intent of the user's query based on keywords and conversation context"""
    query_lower = query.lower()
    
    # First check for specific intents regardless of conversation context
    # These explicit intents should override followup detection
    
    # Check for intent related to cases - high priority check
    case_keywords = ["case", "precedent", "ruling", "judgment", "decision", "court", "vs", "vs.", "v.", "versus"]
    has_case_keywords = any(word in query_lower for word in case_keywords)
    has_case_name = bool(extract_case_names(query))
    similar_case_phrase = "similar" in query_lower and "case" in query_lower
    like_this_phrase = "like this" in query_lower
    example_request = "example" in query_lower and "case" in query_lower
    
    if has_case_keywords or has_case_name or similar_case_phrase or like_this_phrase or example_request:
        print(f"Detected case-related query. Keywords: {has_case_keywords}, Case names: {has_case_name}, Similar phrase: {similar_case_phrase}, Like this: {like_this_phrase}")
        return "cases"
    
    # Check for intent related to impact or consequences
    impact_keywords = ["impact", "effect", "consequence", "result", "outcome", "implication", 
                      "what happens", "what will happen", "consequences", "results in", "leads to", 
                      "penalty", "punishment", "sentence"]
    has_impact_keywords = any(word in query_lower for word in impact_keywords)
    impact_phrase = any(phrase in query_lower for phrase in ["tell me the impact", "what are the consequences", 
                                                            "how does it affect", "how will it affect", 
                                                            "what is the penalty", "what punishment"])
    
    if has_impact_keywords or impact_phrase:
        print(f"Detected impact-related query. Keywords: {has_impact_keywords}, Phrases: {impact_phrase}")
        return "impact"
    
    # Check for intent related to legal sections
    if any(word in query_lower for word in ["section", "act", "ipc", "crpc", "provision", "law", "legal section"]):
        print("Detected section-related query")
        return "sections"
    
    # After specific intent checks, check if it's a follow-up
    if conversation_history:
        # If the last message was from the assistant asking for details
        if "have you" in conversation_history.lower() or "do you" in conversation_history.lower() or "could you" in conversation_history.lower():
            if len(query.split()) < 15:
                print("Detected follow-up response to our question, treating as followup")
                return "followup"
    
    # If detailed enough (long query)
    if len(query.split()) > 15:
        return "details"
        
    # Default to initial stage for short queries unless it's clearly a follow-up
    if len(query.split()) < 10 and ("yes" in query_lower or "no" in query_lower or "i did" in query_lower or "i didn't" in query_lower):
        return "followup"
        
    return "initial"

# Routes
@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a legal query in a conversational, step-by-step manner."""
    query = sanitize_query(request.query)
    session_id = request.session_id or str(uuid.uuid4())
    
    # Get conversation history and session
    conversation_history = conv_state.get_conversation_history(session_id)
    session = conv_state.get_session(session_id)
    
    # Get the current conversation stage from the session
    current_stage = "initial"
    if session:
        current_stage = session.get('current_stage', 'initial')
        
    # Log information for debugging
    print(f"Processing query: '{query}' with session ID: {session_id}")
    print(f"Current conversation stage: {current_stage}")
    
    # Check if it's a legal query, passing conversation history for context
    if not is_legal_query_gemini(query, conversation_history):
        # Get a contextual redirect response based on the conversation stage
        answer = get_contextual_redirect(current_stage)
        print(f"Query classified as non-legal, responding with: {answer[:30]}...")
        
        # Update conversation state
        conv_state.update(session_id, query, answer, [], [], "initial")
        return QueryResponse(answer=answer, references=[], cases=[], session_id=session_id, conversation_stage="initial")
    
    # Determine the intent of the query
    intent = detect_query_intent(query, conversation_history)
    print(f"Query intent detected as: {intent}")
    references = []
    cases = []
    
    # Handle based on intent/stage
    if intent == "followup":
        # Handle direct follow-up to questions
        # First, check if we have references from previous context
        previous_references = session.get('references', [])
        previous_cases = session.get('cases', [])
        
        # Check for specific followup types in the query
        query_lower = query.lower()
        followup_type = "details"  # Default followup type
        
        # Re-check for specific intents in the followup
        if "case" in query_lower or "like this" in query_lower:
            followup_type = "cases"
            print(f"Followup query contains case-related keywords, setting stage to: {followup_type}")
        elif "impact" in query_lower or "effect" in query_lower or "consequence" in query_lower:
            followup_type = "impact"
            print(f"Followup query contains impact-related keywords, setting stage to: {followup_type}")
        elif "section" in query_lower or "law" in query_lower or "act" in query_lower:
            followup_type = "sections"
            print(f"Followup query contains section-related keywords, setting stage to: {followup_type}")
        
        # Build context from previous information
        context_info = ""
        if previous_references:
            context_info += "Relevant legal provisions from previous conversation:\n"
            for ref in previous_references[:2]:
                context_info += f"- {ref['act']} Section {ref['section_number']}: {ref['summary'][:100]}...\n"
        
        if previous_cases and followup_type == "cases":
            context_info += "\nRelevant cases from previous conversation:\n"
            for case in previous_cases[:2]:
                title = case.get('title', 'Untitled Case')
                url = case.get('url', '')
                context_info += f"- {title} ({url})\n"
                
        # Generate a follow-up response
        prompt = f"""Based on the ongoing conversation and the user's follow-up response: '{query}', 
provide a helpful legal response that directly addresses their answer to your previous question.
Don't ask further questions unless absolutely necessary.
Focus on giving clear, concise legal advice (under 256 tokens) based on their situation.
Use the previous legal context and their newest information to give practical guidance."""
        
        answer = generate_direct_answer(prompt, context_info, conversation_history, is_followup=True, max_tokens=256)
        conversation_stage = followup_type  # Set the stage based on the detected followup type
        
    elif intent == "initial":
        # Ask for more details
        prompt = f"Based on the user's query: '{query}', create a very brief response that asks for 1-2 specific details about their legal situation to help you provide better assistance. Keep it under 256 tokens."
        answer = generate_direct_answer(prompt, "", conversation_history, is_followup=False, max_tokens=256)
        conversation_stage = "initial"
        
    elif intent == "sections" or intent == "details":
        # Provide legal sections and basic information
        references = find_relevant_sections(query, conversation_history)
        context_info = ""
        if references:
            context_info += "Relevant legal provisions:\n"
            for ref in references:
                context_info += f"- {ref['act']} Section {ref['section_number']}: {ref['summary']}\n"
                
        if intent == "sections":
            # Directly focus on explaining the sections
            prompt = f"Based on the user's query about legal sections: '{query}', explain the following legal provisions in brief. Format your answer to clearly explain each section's purpose and application:\n\n{context_info}"
        else:
            # General legal information with sections as context
            prompt = f"Based on the user's query: '{query}', provide concise legal information using these legal provisions as context. Explain how they're relevant to the situation described:\n\n{context_info}\n\nMention that they can ask about specific cases or impacts."
            
        answer = generate_direct_answer(prompt, context_info, conversation_history, is_followup=True, max_tokens=256)
        conversation_stage = "details"
        
    elif intent == "cases":
        # Check if specific case names are mentioned
        case_names = extract_case_names(query)
        
        if case_names:
            print(f"Detected specific case names: {case_names}")
            
            # Use our specialized case helper for direct case lookup
            try:
                case_response = await handle_case_lookup(query, conversation_history)
                if case_response and len(case_response) > 20:
                    # If we got a good response with case links, use it directly
                    answer = case_response
                    # Still fetch cases for the session state
                    cases = fetch_kanoon_results(query, conversation_history)
                    conversation_stage = "cases"
                    return QueryResponse(
                        answer=answer,
                        references=[],
                        cases=cases,
                        session_id=session_id,
                        conversation_stage=conversation_stage
                    )
            except Exception as e:
                print(f"Error using case helper: {e}")
                # Fall through to standard case handling
        
        # Standard case handling
        cases = fetch_kanoon_results(query, conversation_history)
        references = session.get('references', []) if session else []
        
        # Build case information including URLs
        case_info = "Relevant cases:\n"
        for case in cases[:2]:  # Limit to 2 cases for token efficiency
            title = case.get('title', 'Untitled Case')
            url = case.get('url', '')
            snippet = case.get('snippet', 'No summary available')
            
            # Include URL in the context for the AI
            case_info += f"- {title}: {snippet[:100]}...\n  URL: {url}\n"
            
        # Make sure to include the URLs in the prompt so the AI includes them
        prompt = f"""Based on the user's query about legal cases: '{query}', 
explain how these cases are relevant to their situation. 
For each case, include the URL as a Markdown link.
Keep your response under 256 tokens, but make sure to include the case URLs:

{case_info}

Format your response to include each case with its URL using this EXACT format:
"[Case Name](URL)" - Brief explanation of relevance.

Example: "[Lalita Kumari v. Govt of UP](https://indiankanoon.org/doc/123456789/) - Established mandatory FIR registration."

DO NOT describe the format; just use it."""
            
        answer = generate_direct_answer(prompt, case_info, conversation_history, is_followup=True, max_tokens=256)
        conversation_stage = "cases"
        
    elif intent == "impact":
        # Explain practical impact
        references = session.get('references', []) if session else []
        cases = session.get('cases', []) if session else []
        
        # Compile context from both sections and cases - more focused for impact
        context_info = ""
        if references:
            context_info += "Key legal provisions:\n"
            for ref in references[:1]:  # More focused - just use the most relevant one
                context_info += f"- {ref['act']} Section {ref['section_number']}: {ref['summary'][:50]}...\n"
        
        if cases:
            context_info += "\nKey case precedent:\n"
            for case in cases[:1]:  # Just one case
                title = case.get('title', 'Untitled Case')
                url = case.get('url', '')
                # Shorter case title for token efficiency
                short_title = title.split(' vs')[0] if ' vs' in title else title
                # Include URL in markdown format, but with shorter case name
                context_info += f"- [{short_title}]({url})\n"
                
        # More focused prompt specifically for impact
        prompt = f"""The user is asking about legal impact: '{query}'
Explain ONLY the practical implications in under 200 tokens. 
Focus on these points:
1. Immediate consequences
2. Legal penalties or remedies
3. Next steps the person should take

Be extremely concise and focused on impact only.
When referring to cases, use format: [Case Name](URL)

Context:
{context_info}"""
        
        # Use a lower token count for more focused response
        answer = generate_direct_answer(prompt, context_info, conversation_history, is_followup=True, max_tokens=200)
        conversation_stage = "impact"
    
    # Update conversation state with the current stage
    conv_state.update(session_id, query, answer, references, cases, conversation_stage)
    
    return QueryResponse(
        answer=answer,
        references=references if intent in ["sections", "details"] else [],
        cases=cases if intent == "cases" else [],
        session_id=session_id,
        conversation_stage=conversation_stage
    )

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a given session."""
    try:
        session = conv_state.get_session(session_id)
        return {"history": session['history']}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {e}")

@router.get("/keywords")
async def get_keywords(query: str, session_id: Optional[str] = None):
    """Extract keywords from a query with optional conversation context."""
    conversation_history = ""
    if session_id:
        conversation_history = conv_state.get_conversation_history(session_id)
    keywords = extract_keywords_from_conversation(conversation_history, query)
    return {"keywords": keywords}

@router.get("/sections")
async def get_sections(query: str, session_id: Optional[str] = None):
    """Find relevant legal sections for a query."""
    conversation_history = ""
    if session_id:
        conversation_history = conv_state.get_conversation_history(session_id)
    sections = find_relevant_sections(query, conversation_history)
    return {"sections": sections}

@router.get("/cases")
async def get_cases(query: str, session_id: Optional[str] = None):
    """Get relevant case law for a query."""
    conversation_history = ""
    if session_id:
        conversation_history = conv_state.get_conversation_history(session_id)
    cases = fetch_kanoon_results(query, conversation_history)
    return {"cases": cases}