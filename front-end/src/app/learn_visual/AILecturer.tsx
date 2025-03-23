"use client"
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const AILecturer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentTopic, setCurrentTopic] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [apiError, setApiError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Start the lecture stream when component mounts
    startLecture();
  }, []);

  const startLecture = async () => {
    try {
      setIsStreaming(true);
      setApiError(false);
      setIsLoading(true);
      
      // Create a CancelToken for the request
      const source = axios.CancelToken.source();
      const timeoutId = setTimeout(() => {
        source.cancel('Timeout exceeded');
      }, 15000); // 15 second timeout
      
      const response = await axios.post('http://localhost:8000/start-lecture/', {}, {
        cancelToken: source.token
      });
      
      clearTimeout(timeoutId);
      
      console.log("API Response:", response.data);
      
      // Check if response has data
      if (response.data) {
        // Set topic and video URL
        if (response.data.topic) {
          setCurrentTopic(response.data.topic);
        }
        
        if (response.data.video_url) {
          // Add autoplay=1 parameter
          const videoWithAutoplay = addAutoplayToUrl(response.data.video_url);
          setVideoUrl(videoWithAutoplay);
          
          // Add a welcome message
          setMessages([{ 
            role: 'assistant', 
            content: `Welcome to the lecture on ${response.data.topic}! I'm your AI assistant. Feel free to ask me any questions about this topic, and I'll do my best to answer them.`
          }]);
        } else {
          throw new Error('No video URL in response');
        }
      } else {
        throw new Error('Empty response from server');
      }
    } catch (error: any) {
      console.error('Error starting lecture:', error);
      setApiError(true);
      
      // Set a default topic when API fails
      setCurrentTopic('Artificial Intelligence and Modern Applications');
      
      // Create a more specific error message
      let errorMessage = 'Welcome to the AI lecture! It seems our lecture service is currently unavailable. ';
      
      if (error.message.includes('Network Error')) {
        errorMessage += 'There was a network error connecting to the backend server. ';
      } else if (error.message.includes('timeout')) {
        errorMessage += 'The request to the server timed out. ';
      } else {
        errorMessage += `Error details: ${error.message}. `;
      }
      
      errorMessage += "\n\nPlease check:\n\n" +
        "1. Is the backend server running at http://localhost:8000?\n" +
        "2. Do you have an internet connection?\n\n" +
        "You can still ask me questions about any intellectual topic you're interested in.";
      
      setMessages([{ 
        role: 'assistant', 
        content: errorMessage
      }]);
      
      // Set a fallback video even in error case - add autoplay
      setVideoUrl(addAutoplayToUrl("https://www.youtube.com/embed/kCc8FmEb1nY"));
    } finally {
      setIsLoading(false);
    }
  };

  // Function to add autoplay parameter to a URL
  const addAutoplayToUrl = (url: string) => {
    if (!url) return url;
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}autoplay=1&mute=1`;  // Mute=1 is required for autoplay to work
  };

  // Detect if message contains a topic request
  const isTopicRequest = (message: string) => {
    // Check if it's a direct topic mention (single word or short phrase)
    if (message.trim().split(/\s+/).length <= 3) {
      console.log("Direct topic detected:", message.trim());
      return true;
    }

    // Check for topic patterns
    const topicPatterns = [
      /talk about (.*)/i,
      /can you discuss (.*)/i,
      /tell me about (.*)/i,
      /lecture on (.*)/i,
      /explain (.*)/i,
      /i want to learn about (.*)/i,
      /switch to (.*)/i,
      /change topic to (.*)/i,
      /show me (.*)/i,
      /teach me (.*)/i,
      /information on (.*)/i,
      /what is (.*)/i,
      /how does (.*) work/i
    ];

    for (const pattern of topicPatterns) {
      if (pattern.test(message)) {
        return true;
      }
    }
    return false;
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMessage = inputMessage;
    setInputMessage('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    // Set a temporary loading message
    const tempMessageId = Date.now();
    setMessages(prev => [...prev, { 
      role: 'assistant', 
      content: 'Searching for relevant information...' 
    }]);

    try {
      // Check if it's potentially a topic change request
      const isRequestingTopic = isTopicRequest(userMessage);
      
      // If it's a topic request, prioritize changing the video
      if (isRequestingTopic) {
        // Update loading message to be more specific
        setMessages(prev => {
          const updated = [...prev];
          // Replace the last loading message
          updated[updated.length - 1] = {
            role: 'assistant',
            content: `Looking for information about "${userMessage.trim()}"...`
          };
          return updated;
        });
        
        try {
          // First try to get a video on the topic
          const videoResponse = await axios.post('http://localhost:8000/update-lecture-video/', {
            text: userMessage
          });
          
          // Get the old topic to compare if it's actually changed
          const oldTopic = currentTopic;
          
          // If we got a topic in the response, update it
          if (videoResponse.data.topic) {
            setCurrentTopic(videoResponse.data.topic);
          }
          
          // If we got a new video URL, update it with autoplay
          if (videoResponse.data.video_url) {
            setVideoUrl(addAutoplayToUrl(videoResponse.data.video_url));
            
            // Replace the loading message with confirmation about topic change
            setMessages(prev => {
              const updated = [...prev];
              // Replace the last message (the loading message)
              updated[updated.length - 1] = {
                role: 'assistant',
                content: `I've found a lecture on "${videoResponse.data.topic}". What would you like to know about this topic?`
              };
              return updated;
            });
            
            // Get initial response from lecturer about this topic
            const response = await axios.post('http://localhost:8000/chat-with-lecturer/', {
              message: `Give me a brief introduction to ${userMessage}`
            });
            
            // Add the introduction as a new message
            setMessages(prev => [...prev, { 
              role: 'assistant', 
              content: response.data.response 
            }]);
          }
        } catch (error) {
          console.error('Error updating video:', error);
          // If we can't get a new video, fall back to regular chat response
          // Replace the loading message with an error
          setMessages(prev => {
            const updated = [...prev];
            // Remove the loading message
            updated.pop();
            return updated;
          });
          
          const response = await axios.post('http://localhost:8000/chat-with-lecturer/', {
            message: userMessage
          });
          
          setMessages(prev => [...prev, { 
            role: 'assistant', 
            content: response.data.response 
          }]);
        }
      } else {
        // Regular chat message flow
        try {
          const response = await axios.post('http://localhost:8000/chat-with-lecturer/', {
            message: userMessage
          });

          // Replace loading message with actual response
          setMessages(prev => {
            const updated = [...prev];
            // Replace the last message (the loading message)
            updated[updated.length - 1] = {
              role: 'assistant',
              content: response.data.response
            };
            return updated;
          });

          // Subtly update the video based on the conversation
          try {
            const videoResponse = await axios.post('http://localhost:8000/update-lecture-video/', {
              text: response.data.response
            });
            
            // If we got a new video URL that's different, update it with autoplay
            if (videoResponse.data.video_url && 
                videoUrl.replace(/[?&]autoplay=1&mute=1/, '') !== videoResponse.data.video_url) {
              setVideoUrl(addAutoplayToUrl(videoResponse.data.video_url));
              
              // Only add a notification message if the topic actually changed
              if (videoResponse.data.topic && videoResponse.data.topic !== currentTopic) {
                setCurrentTopic(videoResponse.data.topic);
                setMessages(prev => [...prev, { 
                  role: 'assistant', 
                  content: `I've switched to a video about "${videoResponse.data.topic}" that seems relevant to our conversation.` 
                }]);
              }
            }
          } catch (error) {
            console.error('Error updating video:', error);
            // If we can't get a new video, don't mark as API error, just keep current video
          }
        } catch (error) {
          console.error('Error in chat response:', error);
          // Replace loading message with error
          setMessages(prev => {
            const updated = [...prev];
            // Replace the last message (the loading message)
            updated[updated.length - 1] = {
              role: 'assistant',
              content: "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please make sure the backend server is running."
            };
            return updated;
          });
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Replace loading message with error
      setMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1].role === 'assistant') {
          // Replace the last message if it's from assistant
          updated[updated.length - 1] = {
            role: 'assistant',
            content: "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please make sure the backend server is running at http://localhost:8000."
          };
        } else {
          // Add new error message
          updated.push({
            role: 'assistant',
            content: "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please make sure the backend server is running at http://localhost:8000."
          });
        }
        return updated;
      });
      
      // Try to find a fallback video based on the user's query
      try {
        const videoResponse = await axios.post('http://localhost:8000/update-lecture-video/', {
          text: userMessage
        });
        if (videoResponse.data.video_url) {
          setVideoUrl(addAutoplayToUrl(videoResponse.data.video_url));
          setCurrentTopic(videoResponse.data.topic);
        }
      } catch (e) {
        // If even that fails, set a default video
        setVideoUrl(addAutoplayToUrl("https://www.youtube.com/embed/kCc8FmEb1nY"));
      }
    }
  };

  const handleRetryConnection = () => {
    setIsLoading(true);
    startLecture();
  };

  return (
    <div className="h-[70vh] w-full flex flex-col bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="flex-1 flex flex-col md:flex-row gap-4 overflow-hidden">
        {/* Video Section - Fixed height on mobile */}
        <div className="md:w-2/3 h-[300px] md:h-full bg-black">
          {videoUrl ? (
            <iframe
              src={videoUrl}
              className="w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          ) : apiError ? (
            <div className="w-full h-full flex flex-col items-center justify-center">
              <div className="text-center text-white">
                <svg className="w-16 h-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <p className="text-lg mb-4">Video stream unavailable</p>
                <div className="flex flex-col gap-2 items-center">
                  <button 
                    onClick={handleRetryConnection}
                    className="btn btn-primary btn-sm"
                  >
                    Retry Connection
                  </button>
                  <p className="text-sm mt-2 max-w-md px-4">
                    Make sure the backend server is running with: <br/>
                    <code className="bg-gray-800 px-2 py-1 rounded text-xs">python text.py</code>
                  </p>
                </div>
              </div>
            </div>
          ) : isLoading ? (
            <div className="w-full h-full flex items-center justify-center">
              <div className="text-center text-white">
                <div className="loading loading-spinner loading-lg"></div>
                <p className="mt-2">Loading lecture video...</p>
              </div>
            </div>
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center">
              <div className="text-center text-white">
                <svg className="w-16 h-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p className="text-lg mb-4">Connection error</p>
                <button 
                  onClick={handleRetryConnection}
                  className="btn btn-primary btn-sm"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Chat Section - Always scrollable */}
        <div className="md:w-1/3 flex flex-col bg-base-200 overflow-hidden flex-shrink-0">
          <div className="p-2 border-b">
            <h3 className="font-semibold">Current Topic: {currentTopic || 'Loading...'}</h3>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2 space-y-2 max-h-[calc(70vh-120px)] md:max-h-none">
            {messages.length > 0 ? (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`chat ${
                    message.role === 'user' ? 'chat-end' : 'chat-start'
                  }`}
                >
                  <div className={`chat-bubble ${
                    message.role === 'user' ? 'chat-bubble-primary' : 'chat-bubble-secondary'
                  }`}>
                    {message.content}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-4">
                {apiError ? 
                  "The backend server may not be running. Start it and retry the connection." :
                  "Ask a question to start the conversation"
                }
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSendMessage} className="p-2 border-t">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask a question..."
                className="input input-bordered flex-1"
              />
              <button
                type="submit"
                className="btn btn-primary btn-sm"
                disabled={!inputMessage.trim()}
              >
                Send
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AILecturer; 