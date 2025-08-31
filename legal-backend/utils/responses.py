"""
Predefined responses and templates for the legal assistant
"""

# Default responses for different scenarios
NON_LEGAL_RESPONSES = [
    "I'm designed to help with legal questions related to Indian law. Could you please ask me about a legal topic?",
    "I specialize in Indian legal matters. Please ask me about laws, legal procedures, or rights.",
    "I can assist with questions about Indian law. What legal matter can I help you with?",
    "My expertise is in Indian legal information. Could you rephrase with a legal focus?",
    "I'm your legal assistant for Indian law questions. How can I help you with a legal matter?"
]

# Context-aware non-legal responses that reference previous conversation
def get_contextual_redirect(conversation_stage="initial"):
    """Return a contextual response based on the conversation stage."""
    
    if conversation_stage == "initial":
        return "I'm designed to help with legal questions related to Indian law. Could you please rephrase your question to focus on a legal topic?"
    
    elif conversation_stage == "details":
        return "I see we were discussing legal matters. I can only help with questions related to Indian law. Could you ask something about legal aspects of your situation?"
    
    elif conversation_stage == "sections":
        return "We were discussing legal sections. To continue, could you ask a question about Indian law or legal provisions?"
        
    elif conversation_stage == "cases":
        return "I notice we were discussing legal cases. I can only answer questions about Indian law. Would you like to continue with your legal inquiry?"
    
    elif conversation_stage == "impact":
        return "We were discussing legal implications. I'm focused on providing legal information. Could you please ask a question related to Indian law?"
        
    # Default fallback
    return "I'm designed to help with legal questions related to Indian law. Could you please rephrase your question to focus on a legal topic?"
