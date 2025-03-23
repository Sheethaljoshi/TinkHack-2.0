"use client";
import { useState, useEffect, useRef } from "react";
import { BsChatLeftHeart } from "react-icons/bs";
import { FaMicrophone, FaMicrophoneSlash } from "react-icons/fa";
import { IconContext } from "react-icons";

const VoiceAssistant: React.FC = () => {
  const [isMounted, setIsMounted] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [connectionStatus, setConnectionStatus] = useState<string>("disconnected");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [sessionId, setSessionId] = useState<string>("");
  
  const modalRef = useRef<HTMLDialogElement | null>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const webSocketRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    setIsMounted(true);
    
    // Create audio element to play model responses
    const audioEl = document.createElement("audio");
    audioEl.autoplay = true;
    audioElementRef.current = audioEl;
    
    return () => {
      // Cleanup on component unmount
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
      }
      
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
      }

      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
    };
  }, []);

  const getSession = async () => {
    try {
      setConnectionStatus("connecting");
      setErrorMessage("");

      console.log("Fetching session from API...");
      const response = await fetch('/api/realtime', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      // Log the status and response details
      console.log(`API response status: ${response.status}`);
      
      if (!response.ok) {
        let errorMsg = `API error: ${response.status}`;
        
        try {
          const errorData = await response.json();
          errorMsg = errorData.error || errorMsg;
        } catch (parseError) {
          console.error("Failed to parse error response:", parseError);
          
          // Try to get the text response if JSON parsing fails
          try {
            const textResponse = await response.text();
            console.error("Raw response:", textResponse);
            errorMsg = `API error (${response.status}): ${textResponse || "No response body"}`;
          } catch (textError) {
            console.error("Failed to get response text:", textError);
          }
        }
        
        throw new Error(errorMsg);
      }

      // Try to parse the JSON response
      let data;
      try {
        data = await response.json();
        console.log("Session data:", data);
      } catch (parseError) {
        console.error("Failed to parse JSON response:", parseError);
        
        // Try to get the text response if JSON parsing fails
        const textResponse = await response.text();
        console.error("Raw response:", textResponse);
        throw new Error(`Invalid JSON response: ${textResponse || "Empty response"}`);
      }

      // Check if the session data contains the required fields
      if (!data || !data.id) {
        console.error("Invalid session data:", data);
        throw new Error("Received invalid session data from API");
      }

      // Create a WebSocket URL if not provided by the API
      if (!data.socket_url) {
        const sessionId = data.id;
        setSessionId(sessionId);
        
        // Use the sessionId to construct a WebSocket URL
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        data.socket_url = `${wsProtocol}//${host}/api/ws/realtime?session=${sessionId}`;
        console.log("Created WebSocket URL:", data.socket_url);
      } else {
        setSessionId(data.id);
      }
      
      return data;
    } catch (error) {
      console.error("Error getting session:", error);
      setConnectionStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Failed to create session");
      throw error;
    }
  };
  
  const setupRealtime = async () => {
    try {
      const sessionData = await getSession();
      console.log("Session created:", sessionData);

      // Create WebSocket connection to the session
      const ws = new WebSocket(sessionData.socket_url);
      webSocketRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connection established");
        setConnectionStatus("connected");
      };

      ws.onclose = () => {
        console.log("WebSocket connection closed");
        setConnectionStatus("disconnected");
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setConnectionStatus("error");
        setErrorMessage("WebSocket connection error");
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleServerEvent(data);
      };

      // Request microphone access and stream audio to server
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      localStreamRef.current = mediaStream;

      // Connect the audio stream with websocket
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(mediaStream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);

      source.connect(processor);
      processor.connect(audioContext.destination);

      processor.onaudioprocess = (e) => {
        if (isListening && ws.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          const audio = convertFloat32ToBase64(inputData);
          
          // Send audio data to server
          ws.send(JSON.stringify({
            type: "input_audio_buffer.append",
            audio: audio
          }));
        }
      };

      setConnectionStatus("ready");
    } catch (error) {
      console.error("Error setting up realtime:", error);
      setConnectionStatus("error");
      setErrorMessage(error instanceof Error ? error.message : "Failed to set up realtime connection");
    }
  };

  const convertFloat32ToBase64 = (buffer: Float32Array) => {
    // Convert Float32Array to Int16Array (16-bit PCM)
    const pcm = new Int16Array(buffer.length);
    for (let i = 0; i < buffer.length; i++) {
      pcm[i] = Math.max(-1, Math.min(1, buffer[i])) * 0x7FFF;
    }
    
    // Convert to Base64
    const pcmBytes = new Uint8Array(pcm.buffer);
    let binary = '';
    for (let i = 0; i < pcmBytes.length; i++) {
      binary += String.fromCharCode(pcmBytes[i]);
    }
    return btoa(binary);
  };
  
  const handleServerEvent = (event: any) => {
    console.log("Received server event:", event);
    
    switch (event.type) {
      case "session.created":
      case "session.updated":
        console.log("Session ready:", event);
        break;
        
      case "input_audio_buffer.speech_started":
        setIsListening(true);
        break;
        
      case "input_audio_buffer.speech_stopped":
        setIsListening(false);
        break;
      
      case "response.audio_transcript.delta":
        if (event.delta && event.delta.text) {
          setTranscript(prev => prev + event.delta.text);
        }
        break;
        
      case "response.text.delta":
        if (event.delta && event.delta.text) {
          setResponse(prev => prev + event.delta.text);
        }
        break;
        
      case "response.done":
        // Response completed
        console.log("Response completed:", event);
        break;
        
      case "error":
        console.error("API error:", event);
        setErrorMessage("API error: " + (event.message || "Unknown error"));
        break;
        
      default:
        // Handle other events as needed
        break;
    }
  };
  
  const toggleListening = () => {
    if (connectionStatus !== "ready") {
      // Initialize if not already connected
      setupRealtime();
      return;
    }
    
    // Toggle microphone on/off
    if (localStreamRef.current) {
      const audioTracks = localStreamRef.current.getAudioTracks();
      
      if (audioTracks.length > 0) {
        audioTracks[0].enabled = !audioTracks[0].enabled;
        setIsListening(audioTracks[0].enabled);
        
        // Notify server about speech started/stopped
        if (webSocketRef.current && webSocketRef.current.readyState === WebSocket.OPEN) {
          if (audioTracks[0].enabled) {
            // Speech started - no need to notify as audio buffer will detect it
          } else {
            // Speech stopped - notify server
            webSocketRef.current.send(JSON.stringify({
              type: "input_audio_buffer.commit"
            }));
            
            // Generate response
            webSocketRef.current.send(JSON.stringify({
              type: "response.create"
            }));
          }
        }
      }
    }
  };
  
  const handleStartConversation = () => {
    modalRef.current?.showModal();
    
    // Reset conversation state
    setTranscript("");
    setResponse("");
    setErrorMessage("");
    
    // Set up connection
    setupRealtime();
  };
  
  const handleCloseModal = () => {
    modalRef.current?.close();
    
    // Clean up connections
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
    }
    
    if (webSocketRef.current) {
      webSocketRef.current.close();
      webSocketRef.current = null;
    }
    
    setConnectionStatus("disconnected");
    setIsListening(false);
  };

  if (!isMounted) return null; // Avoid hydration errors

  return (
    <div className="max-w-3xl mx-auto p-14 bg-base-100 shadow-xl rounded-full">
      <div className="text-2xl font-extrabold text-[#343232] mb-4 text-center">
        Having a bad day?
      </div>

      <div className="flex justify-center">
        <button 
          className="btn btn-lg btn-primary px-6 py-3 text-xl flex items-center gap-3" 
          onClick={handleStartConversation}
        >
          Talk to Remi 
          <IconContext.Provider value={{ color: "black", className: "global-class-name", size:"1.8em" }}>
            <div>
              <BsChatLeftHeart />
            </div>
          </IconContext.Provider>
        </button>
      </div>

      {/* Enhanced Conversation Modal */}
      <dialog ref={modalRef} id="my_modal_4" className="modal">
        <div className="modal-box w-full max-w-3xl p-8">
          <h3 className="font-bold text-2xl mb-4">Chat with Remi</h3>
          
          <div className="flex flex-col gap-4">
            {/* Connection status indicator */}
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                connectionStatus === "connected" || connectionStatus === "ready" 
                  ? "bg-green-500" 
                  : connectionStatus === "connecting" 
                    ? "bg-yellow-500" 
                    : "bg-red-500"
              }`}></div>
              <span className="text-sm capitalize">{connectionStatus}</span>
              {sessionId && <span className="text-xs ml-2 opacity-50">Session: {sessionId.slice(0, 8)}...</span>}
            </div>
            
            {/* Error message display */}
            {errorMessage && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                <span className="block sm:inline">{errorMessage}</span>
              </div>
            )}
            
            {/* Transcript display */}
            <div className="bg-base-200 p-4 rounded-lg min-h-28 max-h-60 overflow-y-auto">
              {transcript ? (
                <p className="text-sm font-medium">You: {transcript}</p>
              ) : (
                <p className="text-sm opacity-50">Your speech will appear here...</p>
              )}
            </div>
            
            {/* Response display */}
            <div className="bg-primary/10 p-4 rounded-lg min-h-28 max-h-60 overflow-y-auto">
              {response ? (
                <p className="text-sm">Remi: {response}</p>
              ) : (
                <p className="text-sm opacity-50">Remi&apos;s response will appear here...</p>
              )}
            </div>
            
            {/* Microphone button */}
            <div className="flex justify-center mt-4">
              <button 
                className={`btn btn-circle btn-lg ${isListening ? 'btn-error' : 'btn-primary'}`}
                onClick={toggleListening}
              >
                {isListening ? (
                  <FaMicrophoneSlash size={24} />
                ) : (
                  <FaMicrophone size={24} />
                )}
              </button>
            </div>
            <p className="text-xs text-center opacity-70">
              {isListening ? "Listening... Click to pause" : "Click to start speaking"}
            </p>
          </div>
          
          <div className="modal-action">
            <button className="btn btn-lg" onClick={handleCloseModal}>Close</button>
          </div>
        </div>
      </dialog>
    </div>
  );
};

export default VoiceAssistant;