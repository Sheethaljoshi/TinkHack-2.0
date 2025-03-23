import { useState, useEffect } from 'react';

const DifficultySelector = () => {
  const [difficulty, setDifficulty] = useState(1);
  const [generated, setGenerated] = useState(false);
  const [summary, setSummary] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);

  // Map slider value to difficulty level for API
  const difficultyLevels = ["beginner", "intermediate", "advanced"];
  const pdfFilename = "people.pdf"; // Using the existing people.pdf in the repository

  const handleGenerate = async () => {
    setIsLoading(true);
    setError('');
    setSummary('');
    setAudioUrl('');
    setGenerated(false);

    try {
      // Connect to the backend endpoint
      const response = await fetch(
        `http://127.0.0.1:8000/summary/${encodeURIComponent(pdfFilename)}/${difficultyLevels[difficulty-1]}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate summary");
      }

      const data = await response.json();
      setSummary(data.summary);
      
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
      console.error("Error generating summary:", error);
      setError(`Error: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlayAudio = () => {
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

  const handleDownload = () => {
    if (!summary) return;
    
    const blob = new Blob([summary], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${pdfFilename.replace('.pdf', '')}_summary.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col p-4 bg-white shadow-lg rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Summary for people.pdf</h2>
      
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">Select level of explanation</h3>
        <input
          type="range"
          min="1"
          max="3"
          step="1"
          value={difficulty}
          onChange={(e) => setDifficulty(Number(e.target.value))}
          className="range range-primary mb-2 w-full"
        />
        <div className="flex justify-between text-sm">
          <span>Beginner</span>
          <span>Intermediate</span>
          <span>Advanced</span>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 text-red-700 p-3 rounded-md mb-4">
          {error}
        </div>
      )}
      
      <button
        onClick={handleGenerate}
        className="btn btn-primary mb-4"
        disabled={isLoading}
      >
        {isLoading ? "Generating..." : "Generate Summary"}
      </button>
      
      {generated && (
        <div className="mt-4">
          <h3 className="text-lg font-semibold mb-2">Generated Summary:</h3>
          <div className="bg-gray-100 p-3 rounded-md mb-4 max-h-60 overflow-y-auto">
            {summary}
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
              disabled={!summary}
            >
              Download Summary
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DifficultySelector;
