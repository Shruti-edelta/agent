import { useState, useEffect, useRef } from 'react';
import { Send, Mic, MicOff } from 'lucide-react';
import api from '../api';
import ChatMessage from '../components/ChatMessage';

export default function ChatPage() {
  const messagesEndRef = useRef(null);

  const [messages, setMessages] = useState([
    {
      role: 'bot',
      answer: "Hello! I'm Agent, your AI assistant. How can I help you today?",
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

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
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    }

    const userPrompt = input.trim();
    setInput('');
    
    // Format history for backend
    const history = messages.map(msg => ({
      role: msg.role === 'bot' ? 'assistant' : 'user',
      content: msg.role === 'bot' ? msg.answer : msg.content
    }));

    setMessages(prev => [...prev, { role: 'user', content: userPrompt }]);
    setIsTyping(true);

    try {
      const res = await api.post('/chat', { 
        prompt: userPrompt,
        messages: history 
      });
      const { answer, success, message } = res.data;

      setMessages(prev => [...prev, {
        role: 'bot',
        answer: answer,
        error: !success ? message : null
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'bot',
        error: err.response?.data?.message || err.message || 'An error occurred while generating the response.'
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="chat-layout chatbot-mode">
      <div className="chat-main">
        <header className="chat-header">
          <h1>AI Agent</h1>
        </header>

        <div className="chat-messages">
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}

          {isTyping && (
            <div className="typing-indicator">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          )}
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
              disabled={isTyping}
            />
            <button
              type="button"
              className={`mic-btn ${isListening ? 'active' : ''}`}
              onClick={toggleListen}
              disabled={isTyping}
              title={isListening ? "Stop Listening" : "Start Voice Input"}
            >
              {isListening ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
            <button
              type="submit"
              className="send-btn"
              disabled={!input.trim() || isTyping}
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
