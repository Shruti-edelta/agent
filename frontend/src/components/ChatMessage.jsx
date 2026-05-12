import { useState, useEffect, useRef } from 'react';
import { Bot, User } from 'lucide-react';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(true);
  const thinkingRef = useRef(null);
  const hasAnswer = !!message.answer;

  // Auto-scroll thinking block as it streams
  useEffect(() => {
    if (thinkingRef.current) {
      thinkingRef.current.scrollTop = thinkingRef.current.scrollHeight;
    }
  }, [message.thinking]);

  // Auto-collapse thinking when answer starts appearing
  useEffect(() => {
    if (hasAnswer && isThinkingExpanded) {
      setIsThinkingExpanded(false);
    }
  }, [hasAnswer]);

  return (
    <div className={`message ${isUser ? 'user' : 'bot'}`}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', alignItems: 'center', opacity: 0.8 }}>
        {isUser ? <User size={14} /> : <Bot size={14} color="#38bdf8" />}
        <span style={{ fontSize: '12px', fontWeight: 500, textTransform: 'uppercase' }}>
          {isUser ? 'You' : 'Agent'}
        </span>
      </div>
      
      <div className="message-bubble">
        {isUser ? (
          <div>{message.content}</div>
        ) : (
          <div>
            {message.thinking && (
              <div className="message-thinking-container" style={{ marginBottom: '12px' }}>
                <button 
                  onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#38bdf8',
                    fontSize: '0.75em',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '0',
                    marginBottom: '4px',
                    opacity: 0.7
                  }}
                >
                  {isThinkingExpanded ? '▼ Hide Thinking' : '▶ Show Thinking Process'}
                </button>
                
                {isThinkingExpanded && (
                  <div 
                    ref={thinkingRef}
                    className="message-thinking" 
                    style={{ 
                      fontSize: '0.85em', 
                      color: '#94a3b8', 
                      fontStyle: 'italic',
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      borderLeft: '2px solid #38bdf8',
                      whiteSpace: 'pre-wrap',
                      maxHeight: '100px', // Roughly 4 lines
                      overflowY: 'auto',
                      scrollbarWidth: 'thin'
                    }}
                  >
                    {message.thinking}
                  </div>
                )}
              </div>
            )}
            
            {message.answer && (
              <div className="message-answer">{message.answer}</div>
            )}
            
            {message.error && (
              <div style={{ color: '#ef4444', marginTop: '8px' }}>{message.error}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
