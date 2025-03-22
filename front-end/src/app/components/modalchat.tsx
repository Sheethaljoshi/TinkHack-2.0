import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { RiHeartAdd2Line } from "react-icons/ri";
import { IconContext } from "react-icons";
import { FcAssistant } from "react-icons/fc";
import MessUser from './messageuser';
import MessAssi from './messageassi';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  message: string;
}

interface ModalProps {
  isVisible: boolean;
  onClose: () => void;
}

const Modalchat: React.FC<ModalProps> = ({ isVisible, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');

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
      
      setMessages(response.data.chat);
    } catch (error) {
      console.error("Error fetching chat history:", error);
    }
  };

  const handleClearChat = async () => {
    try {
      await axios.delete("http://127.0.0.1:8000/clear_chat/", {
        params: { email: "sh33thal24@gmail.com" }
      });
      setMessages([]); 
    } catch (error) {
      console.error("Error clearing chat:", error);
    }
  };

  const handleSubmit = async () => {
    const url = `http://127.0.0.1:8000/get_answer?email=sh33thal24@gmail.com&first_name=Sheethal&last_name=Joshi%20Thomas&question=${newMessage}`;
    const response = await axios.post(url);
    const assistantMessage: Message = { id: messages.length + 1, role: "assistant", message: response.data.answer };
    setMessages([...messages, { id: messages.length + 1, role: "user", message: newMessage }, assistantMessage]);
    setNewMessage('');
  };

  if (!isVisible) return null;

  return (
    <div className='fixed inset-0 bg-black bg-opacity-45 backdrop-blur flex justify-center items-center z-50'>
      <div className='w-[600px]'>
        <div className='bg-base-200 p-7 rounded-3xl flex flex-col'>
          <div className='mb-7 mt-2 text-lg flex justify-between'>
            <div className='flex'>
              <div className='mr-2'>
                <IconContext.Provider value={{ size: 40 }}>
                  <FcAssistant />
                </IconContext.Provider>
              </div>
              <div className='font-extrabold mt-2 text-2xl'>Your Personal Assistant</div>
              <button className="btn w-64 bg-warning mr-6 mt-4" onClick={handleClearChat}>Reset Chat</button>
            </div>
            <div className="card-actions justify-end">
              <button className="btn btn-square btn-sm" onClick={onClose}>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          <div className="card w-full bg-base-100 h-80 overflow-y-auto">
            <div className="card-body">
                          {messages.map((mess, index) => (
                mess.role === "assistant" ? (
                  <MessAssi key={`${mess.id}-${index}`} {...mess} />
                ) : (
                  <MessUser key={`${mess.id}-${index}`} {...mess} />
                )
              ))}
            </div>
          </div>
          <div className="join w-full bg-base-100 shadow-2xl mt-8">
            <input
              className="card w-full bg-base-100 pl-5 input-bordered input join-item"
              placeholder="Enter message"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
            />
            <button className="btn join-item rounded-r-full bg-warning input-bordered" onClick={handleSubmit}>Send</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Modalchat;
