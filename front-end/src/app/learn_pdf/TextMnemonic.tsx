"use client";
import { useState } from "react";
import { FaPlay, FaPause, FaDownload } from "react-icons/fa";

export default function TextMnemonic() {
  const [inputText, setInputText] = useState<string>("");
  const [mnemonic, setMnemonic] = useState<string>("");
  const [audioUrl, setAudioUrl] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);
  const [error, setError] = useState<string>("");

  const generateMnemonic = async () => {
    if (!inputText.trim()) {
      setError("Please enter some text first");
      return;
    }

    setIsLoading(true);
    setError("");
    setMnemonic("");
    setAudioUrl("");
    
    if (audio) {
      audio.pause();
      setAudio(null);
      setIsPlaying(false);
    }

    try {
      console.log("Submitting text:", inputText);
      const formData = new FormData();
      formData.append("input_text", inputText);

      const response = await fetch("http://127.0.0.1:8000/generate-mnemonic", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = "Failed to generate mnemonic";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (parseError) {
          console.error("Error parsing error response:", parseError);
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log("Response data:", data);
      
      if (!data.mnemonic) {
        throw new Error("No mnemonic returned from server");
      }
      
      setMnemonic(data.mnemonic);
      
      if (data.audio_url) {
        // Convert to full URL if needed
        const fullAudioUrl = data.audio_url.startsWith("http") 
          ? data.audio_url 
          : `http://127.0.0.1:8000${data.audio_url}`;
        
        console.log("Audio URL:", fullAudioUrl);
        setAudioUrl(fullAudioUrl);
        
        // Create audio element
        const audioElement = new Audio(fullAudioUrl);
        
        // Add event listeners
        audioElement.addEventListener("ended", () => setIsPlaying(false));
        audioElement.addEventListener("canplaythrough", () => console.log("Audio ready to play"));
        audioElement.addEventListener("error", (e) => {
          console.error("Audio error:", e);
          const audioError = e.target as HTMLAudioElement;
          let errorMsg = "Failed to load audio";
          
          if (audioError.error) {
            errorMsg += `: ${audioError.error.message}`;
          }
          
          setError(errorMsg);
        });
        
        setAudio(audioElement);
      }
    } catch (error) {
      console.error("Error generating mnemonic:", error);
      setError(`Error: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsLoading(false);
    }
  };

  const togglePlay = () => {
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play().catch(err => {
        console.error("Error playing audio:", err);
        setError(`Could not play audio: ${err.message}`);
      });
    }
    setIsPlaying(!isPlaying);
  };

  const downloadMnemonic = () => {
    if (!mnemonic) return;

    const blob = new Blob([mnemonic], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "mnemonic.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Text-based Mnemonic Generator</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Enter text to create a mnemonic:</label>
        <textarea
          className="w-full p-2 border rounded-md h-32"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Enter the text you want to create a mnemonic for..."
          disabled={isLoading}
        />
      </div>
      
      <button
        className="w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 disabled:bg-gray-400 mb-4 flex items-center justify-center"
        onClick={generateMnemonic}
        disabled={isLoading || !inputText.trim()}
      >
        {isLoading ? (
          <>
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Generating...
          </>
        ) : (
          "Generate Mnemonic"
        )}
      </button>
      
      {mnemonic && (
        <div className="mt-4">
          <h2 className="text-xl font-semibold mb-2">Memory Aid</h2>
          <div className="bg-gray-100 p-4 rounded-md max-h-60 overflow-y-auto mb-4">
            {mnemonic}
          </div>
          
          <div className="flex space-x-2">
            {audioUrl && (
              <button
                className="flex items-center px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
                onClick={togglePlay}
              >
                {isPlaying ? <FaPause className="mr-2" /> : <FaPlay className="mr-2" />}
                {isPlaying ? "Pause" : "Play"}
              </button>
            )}
            
            <button
              className="flex items-center px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600"
              onClick={downloadMnemonic}
              disabled={!mnemonic}
            >
              <FaDownload className="mr-2" />
              Download
            </button>
          </div>
        </div>
      )}
    </div>
  );
}