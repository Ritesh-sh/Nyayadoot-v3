from typing import List, Dict

class ConversationState:
    """Manages conversation sessions and histories for each user."""
    def __init__(self):
        self.sessions = {}
        
    def get_session(self, session_id: str):
        """Retrieve or create a session by session_id."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'current_context': None,
                'current_stage': 'initial',
                'references': None,
                'cases': None,
                'history': []
            }
        return self.sessions[session_id]

    def update(self, session_id: str, query: str, answer: str, references: List[Dict], cases: List[Dict], stage: str = None):
        """Update session with new query, answer, references, and cases."""
        session = self.get_session(session_id)
        session['current_context'] = {
            'query': query,
            'answer': answer,
            'references': references,
            'cases': cases
        }
        if stage:
            session['current_stage'] = stage
        session['references'] = references
        session['cases'] = cases
        session['history'].append(('user', query))
        session['history'].append(('assistant', answer))
        
    def get_conversation_history(self, session_id: str, max_turns: int =9) -> str:
        """Get formatted conversation history for context."""
        session = self.get_session(session_id)
        history = session['history']
        
        # Get the most recent turns (limited by max_turns)
        recent_history = history[-max_turns*2:] if history else []
        
        formatted_history = ""
        for i in range(0, len(recent_history), 2):
            if i+1 < len(recent_history):
                user_msg = recent_history[i][1]
                assistant_msg = recent_history[i+1][1]
                
                # Truncate very long messages to prevent context overflow
                if len(assistant_msg) > 500:
                    assistant_msg = assistant_msg[:500] + "..."
                
                formatted_history += f"User: {user_msg}\nAssistant: {assistant_msg}\n\n"
        
        return formatted_history.strip()
