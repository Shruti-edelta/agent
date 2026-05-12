import { useState, useEffect, useRef } from 'react';
import { Send, Mic, MicOff, Plus, MessageSquare, Bot, Trash2 } from 'lucide-react';
import api from '../api';
import ChatMessage from '../components/ChatMessage';

export default function ChatPage() {
  const messagesEndRef = useRef(null);

  const initialGreeting = {
    role: 'bot',
    answer: "Hello! I'm Agent, your AI assistant. How can I help you today?",
  };

  // Load from sessionStorage on init
  const [chats, setChats] = useState(() => {
    const savedChats = sessionStorage.getItem('agent_chats');
    return savedChats ? JSON.parse(savedChats) : [
      {
        id: Date.now(),
        title: 'New Chat',
        messages: [initialGreeting]
      }
    ];
  });

  const [activeChatId, setActiveChatId] = useState(() => {
    const savedActiveId = sessionStorage.getItem('agent_active_chat_id');
    return savedActiveId ? parseInt(savedActiveId) : chats[0].id;
  });

  const [input, setInput] = useState('');
  const [typingChatId, setTypingChatId] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  // Persistence logic
  useEffect(() => {
    sessionStorage.setItem('agent_chats', JSON.stringify(chats));
  }, [chats]);

  useEffect(() => {
    sessionStorage.setItem('agent_active_chat_id', activeChatId.toString());
  }, [activeChatId]);

  const activeChat = chats.find(c => c.id === activeChatId) || chats[0];
  const messages = activeChat.messages;

  useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0])
          .map(result => result.transcript)
          .join('');
        setInput(transcript);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
      };
    }
  }, []);

  const toggleListen = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      if (recognitionRef.current) {
        setInput('');
        try {
          recognitionRef.current.start();
          setIsListening(true);
        } catch (e) {
          console.error("Failed to start listening:", e);
        }
      } else {
        alert('Your browser does not support Speech Recognition. Please try Chrome, Edge, or Safari.');
      }
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typingChatId]); // Scroll when typing indicator changes for active chat

  const handleNewChat = () => {
    const newChat = {
      id: Date.now(),
      title: 'New Chat',
      messages: [initialGreeting]
    };
    setChats(prev => [newChat, ...prev]);
    setActiveChatId(newChat.id);
    setInput('');
  };

  const deleteChat = (id, e) => {
    e.stopPropagation();
    if (chats.length === 1) {
      handleNewChat();
      setChats(prev => prev.filter(c => c.id !== id));
      return;
    }
    const newChats = chats.filter(c => c.id !== id);
    setChats(newChats);
    if (activeChatId === id) {
      setActiveChatId(newChats[0].id);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    }

    const currentChatId = activeChatId; // Store the ID at the moment of sending
    const userPrompt = input.trim();
    setInput('');
    
    // Update title if it's the first message
    if (messages.length === 1) {
      setChats(prev => prev.map(c => 
        c.id === currentChatId ? { ...c, title: userPrompt.substring(0, 30) + (userPrompt.length > 30 ? '...' : '') } : c
      ));
    }

    // Format history for backend
    const history = messages.map(msg => ({
      role: msg.role === 'bot' ? 'assistant' : 'user',
      content: msg.role === 'bot' ? msg.answer : msg.content
    }));

    // Optimistically update UI
    setChats(prev => prev.map(c => 
      c.id === currentChatId ? { ...c, messages: [...c.messages, { role: 'user', content: userPrompt }] } : c
    ));
    setTypingChatId(currentChatId); // Set typing for this specific chat

    try {
      const response = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userPrompt, messages: history })
      });

      if (!response.ok) throw new Error('Failed to connect to assistant');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let fullAnswer = '';
      let fullThinking = '';

      // Initialize the bot message in the chat
      setChats(prev => prev.map(c => 
        c.id === currentChatId ? { 
          ...c, 
          messages: [...c.messages, {
            role: 'bot',
            answer: '',
            thinking: '',
          }] 
        } : c
      ));

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.error) throw new Error(data.error);

              fullAnswer += (data.content || '');
              fullThinking += (data.thinking || '');

              setChats(prev => prev.map(c => 
                c.id === currentChatId ? { 
                  ...c, 
                  messages: c.messages.map((m, idx) => 
                    idx === c.messages.length - 1 ? { ...m, answer: fullAnswer, thinking: fullThinking } : m
                  )
                } : c
              ));
            } catch (e) {
              console.error("Error parsing stream chunk:", e);
            }
          }
        }
      }
    } catch (err) {
      setChats(prev => prev.map(c => 
        c.id === currentChatId ? { 
          ...c, 
          messages: [...c.messages, {
            role: 'bot',
            error: err.message || 'An error occurred while generating the response.'
          }] 
        } : c
      ));
    } finally {
      setTypingChatId(null);
    }
  };

  return (
    <div className="chat-layout chatbot-mode">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="agent-title">
            <Bot size={20} color="#38bdf8" />
            <h1>AI Agent</h1>
          </div>
          <button className="new-chat-btn" onClick={handleNewChat}>
            <Plus size={18} />
            <span>New Chat</span>
          </button>
        </div>
        <div className="sidebar-content">
          {chats.map(chat => (
            <div 
              key={chat.id} 
              className={`history-item ${chat.id === activeChatId ? 'active' : ''}`}
              onClick={() => setActiveChatId(chat.id)}
            >
              <div className="history-item-left">
                <MessageSquare size={16} />
                <span className="chat-title">{chat.title}</span>
              </div>
              <div className="history-item-right">
                {typingChatId === chat.id && <div className="typing-dot"></div>}
                <button className="delete-chat-btn" onClick={(e) => deleteChat(chat.id, e)}>
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </aside>

      <div className="chat-main">
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-area" onSubmit={handleSend}>
          <div className="input-wrapper">
            <input
              type="text"
              className="chat-input"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={typingChatId === activeChatId}
            />
            <button
              type="button"
              className={`mic-btn ${isListening ? 'active' : ''}`}
              onClick={toggleListen}
              disabled={typingChatId === activeChatId}
              title={isListening ? "Stop Listening" : "Start Voice Input"}
            >
              {isListening ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
            <button
              type="submit"
              className="send-btn"
              disabled={!input.trim() || typingChatId === activeChatId}
              title="Send Message"
            >
              <Send size={18} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
