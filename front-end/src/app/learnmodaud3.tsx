import { useState, useEffect } from 'react';

const StoryTellingComponent = () => {
  const [story, setStory] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [generated, setGenerated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);
  
  // Use people.pdf as the existing file in the repository
  const pdfFilename = "people.pdf";

  const handleGenerate = async () => {
    setIsLoading(true);
    setError('');
    setStory('');
    setAudioUrl('');
    setGenerated(false);

    try {
      // Connect to the backend endpoint
      const response = await fetch(
        `http://127.0.0.1:8000/story/${encodeURIComponent(pdfFilename)}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate story");
      }

      const data = await response.json();
      setStory(data.story);
      
      if (data.audio_path) {
        // Get the actual audio URL
        const audioResponse = await fetch(`http://127.0.0.1:8000${data.audio_path}`);
        if (!audioResponse.ok) {
          throw new Error("Failed to retrieve audio file information");
        }
        
        const audioData = await audioResponse.json();
        
        // Use the direct audio URL
        const fullAudioUrl = `http://127.0.0.1:8000${audioData.audio_url}`;
        setAudioUrl(fullAudioUrl);
        
        // Create audio element
        const audioElement = new Audio(fullAudioUrl);
        audioElement.addEventListener("ended", () => setIsPlaying(false));
        setAudio(audioElement);
      }
      
      setGenerated(true);
    } catch (error) {
      console.error("Error generating story:", error);
      setError(`Error: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlayAudio = () => {
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play().catch(err => {
        console.error("Error playing audio:", err);
        setError(`Could not play audio: ${err.message}`);
      });
      setIsPlaying(true);
    }
  };

  const handleDownload = () => {
    if (!story) return;
    
    const blob = new Blob([story], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${pdfFilename.replace('.pdf', '')}_story.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col p-4 bg-white shadow-lg rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Story for {pdfFilename}</h2>
      
      {error && (
        <div className="bg-red-100 text-red-700 p-3 rounded-md mb-4">
          {error}
        </div>
      )}
      
      {!generated ? (
        <button
          onClick={handleGenerate}
          className="btn btn-primary mb-4"
          disabled={isLoading}
        >
          {isLoading ? "Generating Story..." : "Generate Story"}
        </button>
      ) : (
        <>
          <div className="bg-gray-100 p-3 rounded-md mb-4 max-h-60 overflow-y-auto">
            {story}
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={handlePlayAudio}
              className="btn btn-success"
              disabled={!audioUrl}
            >
              {isPlaying ? "Pause" : "Play Audio"}
            </button>
            
            <button
              onClick={handleDownload}
              className="btn btn-secondary"
              disabled={!story}
            >
              Download Story
            </button>
          </div>
          
          {/* Audio Debug Info */}
          <div className="mt-4 p-3 bg-gray-100 rounded">
            <h4 className="text-md font-semibold mb-2">Audio Player:</h4>
            {audioUrl && (
              <audio controls src={audioUrl} className="w-full mt-1">
                Your browser does not support the audio element.
              </audio>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default StoryTellingComponent;