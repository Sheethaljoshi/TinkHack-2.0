"use client"
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { FaMicrophone, FaMicrophoneSlash } from "react-icons/fa";
import { IoSend } from "react-icons/io5";
import { RiRobot2Fill } from "react-icons/ri";
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  message: string;
  timestamp: Date;
}

interface TalkToRemiProps {
  isVisible: boolean;
  onClose: () => void;
}

const TalkToRemi: React.FC<TalkToRemiProps> = ({ isVisible, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [recognition, setRecognition] = useState<any>(null);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // @ts-ignore
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        const recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = true;
        recognitionInstance.interimResults = true;
        recognitionInstance.lang = 'en-US';
        
        recognitionInstance.onresult = (event: any) => {
          const transcript = Array.from(event.results)
            .map((result: any) => result[0])
            .map((result) => result.transcript)
            .join('');
          
          setNewMessage(transcript);
        };
        
        recognitionInstance.onerror = (event: any) => {
          console.error('Speech recognition error', event.error);
          setIsRecording(false);
        };
        
        setRecognition(recognitionInstance);
      } else {
        console.error('Speech recognition not supported in this browser');
      }
    }
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch chat history when the modal opens
  useEffect(() => {
    if (isVisible) {
      getChatHistory();
    }
  }, [isVisible]);

  const getChatHistory = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/get_chat_history', {
        params: { email: 'sh33thal24@gmail.com' }
      });
      
      // Convert the response data to our Message format with timestamps
      const chatHistory = response.data.chat.map((message: any, index: number) => ({
        id: index,
        role: message.role,
        message: message.message,
        timestamp: new Date()
      }));
      
      setMessages(chatHistory);
    } catch (error) {
      console.error("Error fetching chat history:", error);
      // Add a default welcome message if we can't fetch history
      setMessages([{
        id: 0,
        role: 'assistant',
        message: "Hello! I'm Remi, your personal AI assistant. How can I help you today?",
        timestamp: new Date()
      }]);
    }
  };

  const handleClearChat = async () => {
    try {
      await axios.delete("http://127.0.0.1:8000/clear_chat/", {
        params: { email: "sh33thal24@gmail.com" }
      });
      
      // Add welcome message after clearing
      setMessages([{
        id: 0,
        role: 'assistant',
        message: "Chat history cleared. How else can I assist you?",
        timestamp: new Date()
      }]);
    } catch (error) {
      console.error("Error clearing chat:", error);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      recognition.stop();
      // Submit the recorded message if it's not empty
      if (newMessage.trim()) {
        handleSubmit();
      }
    } else {
      setNewMessage('');
      recognition.start();
    }
    setIsRecording(!isRecording);
  };

  const handleSubmit = async () => {
    if (!newMessage.trim()) return;
    
    // Stop recording if active
    if (isRecording) {
      recognition.stop();
      setIsRecording(false);
    }
    
    const userMsg = newMessage.trim();
    setNewMessage('');
    setIsProcessing(true);
    
    // Add user message immediately
    const userMessage = { 
      id: messages.length + 1, 
      role: "user", 
      message: userMsg,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      // Use the chat-with-lecturer endpoint for better responses
      const response = await axios.post('http://127.0.0.1:8000/chat-with-lecturer/', {
        message: userMsg
      });
      
      const assistantResponse = response.data.response;
      
      // Add assistant message when response arrives
      const assistantMessage = { 
        id: messages.length + 2, 
        role: "assistant", 
        message: assistantResponse,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Save the chat message to database
      try {
        await axios.post('http://127.0.0.1:8000/save-remi-chat/', {
          message: userMsg,
          response: assistantResponse,
          email: 'sh33thal24@gmail.com'
        });
      } catch (saveError) {
        console.error("Error saving chat:", saveError);
      }
      
      // Optional: Text-to-speech for the response
      if ('speechSynthesis' in window) {
        const speech = new SpeechSynthesisUtterance(assistantResponse);
        speech.lang = 'en-US';
        window.speechSynthesis.speak(speech);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      
      // Add error message
      const errorMessage = { 
        id: messages.length + 2, 
        role: "assistant", 
        message: "I'm sorry, I'm having trouble connecting to the server. Please try again later.",
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className='fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex justify-center items-center z-50'
      onClick={(e) => {
        // Close when clicking the backdrop
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className='w-[95%] max-w-[700px] max-h-[90vh] rounded-2xl overflow-hidden shadow-2xl'
      >
        <div className='bg-base-200 flex flex-col h-[80vh]'>
          {/* Header */}
          <div className='bg-primary text-white p-4 flex justify-between items-center'>
            <div className='flex items-center'>
              <RiRobot2Fill className="w-8 h-8 mr-2" />
              <h2 className='text-xl font-bold'>Talk to Remi</h2>
            </div>
            <div className='flex gap-2'>
              <button
                className="btn btn-sm btn-ghost text-white"
                onClick={handleClearChat}
              >
                Reset Chat
              </button>
              <button
                className="btn btn-sm btn-circle btn-ghost text-white"
                onClick={onClose}
              >
                ✕
              </button>
            </div>
          </div>
          
          {/* Messages Container */}
          <div className="flex-1 p-4 overflow-y-auto bg-base-100">
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={`${message.id}-${index}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className={`chat ${message.role === 'user' ? 'chat-end' : 'chat-start'} mb-4`}
                >
                  <div className={`chat-bubble ${
                    message.role === 'user' 
                      ? 'bg-primary text-white' 
                      : 'bg-base-200'
                  } shadow-md`}>
                    {message.message}
                  </div>
                  <div className="chat-footer opacity-50 text-xs">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={messagesEndRef} />
            
            {/* Typing indicator */}
            {isProcessing && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="chat chat-start"
              >
                <div className="chat-bubble bg-base-200 flex gap-1 items-center">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0s" }}></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                </div>
              </motion.div>
            )}
          </div>
          
          {/* Input Area */}
          <div className="p-4 bg-base-200 border-t border-base-300">
            <div className="join w-full bg-base-100 rounded-full shadow-md">
              <input
                className="input flex-1 input-bordered join-item rounded-l-full w-full focus:outline-none bg-transparent"
                placeholder={isRecording ? "Listening..." : "Type your message..."}
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isRecording}
              />
              <button 
                className={`btn join-item ${isRecording ? 'btn-error' : 'btn-primary'} rounded-r-full`}
                onClick={toggleRecording}
              >
                {isRecording ? <FaMicrophoneSlash size={20} /> : <FaMicrophone size={20} />}
              </button>
              <button 
                className="btn btn-primary rounded-full ml-2"
                onClick={handleSubmit}
                disabled={!newMessage.trim() || isProcessing}
              >
                <IoSend size={20} />
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default TalkToRemi; 