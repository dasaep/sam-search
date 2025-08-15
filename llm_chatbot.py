"""
LLM Chatbot using Ollama for natural language queries about opportunities
"""

import logging
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

log = logging.getLogger("llm_chatbot")


class OpportunityChatbot:
    def __init__(
        self,
        db,
        graph_rag,
        ollama_url: str = "http://localhost:11434",
        model: str = "llama2"
    ):
        self.db = db
        self.graph_rag = graph_rag
        self.ollama_url = ollama_url
        self.model = model
        self.conversation_history = []
    
    def _query_ollama(self, prompt: str, context: str = "") -> str:
        """Send query to Ollama API"""
        
        try:
            # Prepare the full prompt with context
            full_prompt = f"""You are an AI assistant helping with government contracting opportunities from SAM.gov.
            
Context: {context}

User Question: {prompt}

Please provide a helpful, accurate response based on the context provided. If you need more information, ask clarifying questions."""
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                log.error(f"Ollama API error: {response.status_code}")
                return "I'm sorry, I couldn't process your request at this time."
                
        except Exception as e:
            log.error(f"Error querying Ollama: {e}")
            return "I'm having trouble connecting to the language model. Please try again later."
    
    def _extract_intent(self, user_input: str) -> Dict[str, Any]:
        """Extract intent and entities from user input"""
        
        # Simple intent detection (can be enhanced with NLP)
        user_input_lower = user_input.lower()
        
        intent = {
            "type": "unknown",
            "entities": {}
        }
        
        # Detect intent patterns
        if any(word in user_input_lower for word in ["find", "search", "show", "list"]):
            intent["type"] = "search"
            
            # Extract entities
            if "agency" in user_input_lower:
                intent["entities"]["filter"] = "agency"
            elif "naics" in user_input_lower:
                intent["entities"]["filter"] = "naics"
            elif "recent" in user_input_lower or "latest" in user_input_lower:
                intent["entities"]["filter"] = "recent"
            elif "high match" in user_input_lower or "best match" in user_input_lower:
                intent["entities"]["filter"] = "high_match"
                
        elif any(word in user_input_lower for word in ["similar", "like", "related"]):
            intent["type"] = "similarity"
            
        elif any(word in user_input_lower for word in ["analyze", "evaluate", "assess"]):
            intent["type"] = "analysis"
            
        elif any(word in user_input_lower for word in ["status", "stage", "pipeline"]):
            intent["type"] = "crm_status"
            
        elif any(word in user_input_lower for word in ["statistics", "summary", "count", "how many"]):
            intent["type"] = "statistics"
            
        elif any(word in user_input_lower for word in ["help", "what can you do", "capabilities"]):
            intent["type"] = "help"
        
        return intent
    
    def _get_context_data(self, intent: Dict[str, Any]) -> str:
        """Fetch relevant context data based on intent"""
        
        context_parts = []
        
        if intent["type"] == "search":
            # Get recent opportunities
            opportunities = self.db.get_opportunities(limit=5)
            if opportunities:
                context_parts.append("Recent opportunities:")
                for opp in opportunities:
                    context_parts.append(
                        f"- {opp.get('title')} (Agency: {opp.get('agency')}, "
                        f"Due: {opp.get('due_date')})"
                    )
        
        elif intent["type"] == "statistics":
            # Get statistics
            stats = self.db.get_statistics()
            context_parts.append(f"Database statistics: {json.dumps(stats, indent=2)}")
        
        elif intent["type"] == "crm_status":
            # Get pipeline summary
            from crm_workflow import CRMWorkflow
            crm = CRMWorkflow(self.db)
            pipeline = crm.get_pipeline_summary()
            context_parts.append(f"Pipeline summary: {json.dumps(pipeline, indent=2)}")
        
        return "\n".join(context_parts)
    
    def chat(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """Process user chat input and return response"""
        
        # Extract intent
        intent = self._extract_intent(user_input)
        
        # Get relevant context
        context = self._get_context_data(intent)
        
        # Handle specific intents with direct responses
        if intent["type"] == "help":
            response = self._get_help_message()
        elif intent["type"] == "statistics":
            response = self._get_statistics_response()
        elif intent["type"] == "search" and intent["entities"].get("filter") == "high_match":
            response = self._get_high_matches_response()
        else:
            # Use LLM for complex queries
            response = self._query_ollama(user_input, context)
        
        # Store conversation history
        self.conversation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "user_input": user_input,
            "intent": intent,
            "response": response
        })
        
        # Store in database for persistence
        if session_id:
            self.db.db.chat_sessions.update_one(
                {"session_id": session_id},
                {
                    "$push": {
                        "messages": {
                            "timestamp": datetime.utcnow(),
                            "role": "user",
                            "content": user_input
                        }
                    },
                    "$set": {"last_activity": datetime.utcnow()}
                },
                upsert=True
            )
            
            self.db.db.chat_sessions.update_one(
                {"session_id": session_id},
                {
                    "$push": {
                        "messages": {
                            "timestamp": datetime.utcnow(),
                            "role": "assistant",
                            "content": response
                        }
                    }
                }
            )
        
        return {
            "response": response,
            "intent": intent,
            "suggestions": self._get_suggestions(intent)
        }
    
    def _get_help_message(self) -> str:
        """Return help message"""
        
        return """I can help you with:
        
1. **Search Opportunities**: Find opportunities by agency, NAICS code, or recent postings
2. **Analyze Matches**: Show high-matching opportunities based on your capabilities
3. **Similar Opportunities**: Find opportunities similar to a specific one
4. **Statistics**: Get counts and summaries of opportunities in the database
5. **CRM Status**: Check opportunity pipeline and stages
6. **Document Analysis**: Information about attached documents

Example questions:
- "Show me recent opportunities from the Department of Defense"
- "Find opportunities with high capability matches"
- "What opportunities are in the proposal stage?"
- "How many opportunities do we have in total?"
- "Find opportunities similar to [opportunity ID]"
"""
    
    def _get_statistics_response(self) -> str:
        """Get formatted statistics response"""
        
        stats = self.db.get_statistics()
        
        return f"""Current Database Statistics:

📊 **Opportunities**: {stats.get('total_opportunities', 0)} total
🎯 **Capabilities**: {stats.get('active_capabilities', 0)} active
🔗 **Matches**: {stats.get('total_matches', 0)} total
⭐ **High Matches** (>70%): {stats.get('high_matches', 0)}
📅 **Recent Opportunities**: {stats.get('recent_opportunities', 0)} today

Would you like more details about any specific area?"""
    
    def _get_high_matches_response(self) -> str:
        """Get high matching opportunities"""
        
        matches = self.db.get_high_matches(threshold=70, limit=5)
        
        if not matches:
            return "No high-matching opportunities found. You may need to run capability analysis first."
        
        response_parts = ["Here are the top matching opportunities:\n"]
        
        for i, match in enumerate(matches, 1):
            opp = match.get("opportunity", {})
            cap = match.get("capability", {})
            
            response_parts.append(
                f"{i}. **{opp.get('title', 'Unknown')}**\n"
                f"   - Match Score: {match.get('match_percentage', 0):.0f}%\n"
                f"   - Capability: {cap.get('name', 'Unknown')}\n"
                f"   - Agency: {opp.get('agency', 'Unknown')}\n"
                f"   - Due Date: {opp.get('due_date', 'Unknown')}\n"
            )
        
        return "\n".join(response_parts)
    
    def _get_suggestions(self, intent: Dict[str, Any]) -> List[str]:
        """Get suggested follow-up questions"""
        
        suggestions = []
        
        if intent["type"] == "search":
            suggestions = [
                "Can you analyze these opportunities for capability matches?",
                "Show me more details about the first opportunity",
                "Find similar opportunities to these"
            ]
        elif intent["type"] == "statistics":
            suggestions = [
                "Show me opportunities with high matches",
                "What's the status of our opportunity pipeline?",
                "List recent opportunities"
            ]
        else:
            suggestions = [
                "What can you help me with?",
                "Show me statistics",
                "Find recent opportunities"
            ]
        
        return suggestions
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get chat history for a session"""
        
        session = self.db.db.chat_sessions.find_one({"session_id": session_id})
        
        if session:
            return session.get("messages", [])
        
        return []