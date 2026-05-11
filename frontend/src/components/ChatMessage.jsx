import { Bot, User } from 'lucide-react';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

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
