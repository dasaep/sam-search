import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './ChatInterface.css';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Generate session ID
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    
    // Add welcome message
    setMessages([{
      id: 1,
      role: 'assistant',
      content: 'Hello! I\'m your SAM.gov opportunity assistant. I can help you search for opportunities, analyze matches, check statistics, and more. How can I assist you today?',
      timestamp: new Date()
    }]);
    
    setSuggestions([
      'Show me recent opportunities',
      'What are the statistics?',
      'Find high-matching opportunities',
      'Help me understand what you can do'
    ]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (message = inputMessage) => {
    if (!message.trim()) return;

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setSuggestions([]);

    try {
      const response = await axios.post('/api/chat', {
        message: message,
        session_id: sessionId
      });

      // Add assistant response
      const assistantMessage = {
        id: messages.length + 2,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update suggestions
      if (response.data.suggestions && response.data.suggestions.length > 0) {
        setSuggestions(response.data.suggestions);
      }
    } catch (error) {
      console.error('Chat error:', error);
      
      const errorMessage = {
        id: messages.length + 2,
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again later.',
        timestamp: new Date(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>SAM.gov Opportunity Assistant</h3>
        <span className="session-id">Session: {sessionId}</span>
      </div>

      <div className="chat-messages">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.role} ${message.isError ? 'error' : ''}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">
                {message.content.split('\n').map((line, index) => (
                  <React.Fragment key={index}>
                    {line}
                    {index < message.content.split('\n').length - 1 && <br />}
                  </React.Fragment>
                ))}
              </div>
              <div className="message-timestamp">
                {formatTimestamp(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message assistant loading">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {suggestions.length > 0 && (
        <div className="suggestions">
          <div className="suggestions-label">Suggestions:</div>
          <div className="suggestion-chips">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-chip"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message here..."
          rows="2"
          disabled={isLoading}
        />
        <button
          className="send-button"
          onClick={() => sendMessage()}
          disabled={isLoading || !inputMessage.trim()}
        >
          {isLoading ? '⏳' : '📤'}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;