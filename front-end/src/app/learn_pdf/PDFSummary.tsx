"use client";
import { useState, useEffect } from "react";
import { FaPlay, FaPause, FaDownload } from "react-icons/fa";

export default function PDFSummary() {
  const [pdfFiles, setPdfFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [difficulty, setDifficulty] = useState<string>("beginner");
  const [summary, setSummary] = useState<string>("");
  const [audioUrl, setAudioUrl] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);
  const [error, setError] = useState<string>("");

  // Fetch available PDF files on component mount
  useEffect(() => {
    fetchPdfFiles();
  }, []);

  // Select Newtons_Laws.pdf if available
  useEffect(() => {
    if (pdfFiles.includes("Newtons_Laws.pdf")) {
      setSelectedFile("Newtons_Laws.pdf");
    }
  }, [pdfFiles]);

  const fetchPdfFiles = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/list_pdf_files");
      const data = await response.json();
      setPdfFiles(data.files || []);
    } catch (error) {
      console.error("Error fetching PDF files:", error);
      setError("Failed to load PDF files. Please make sure the server is running.");
    }
  };

  const generateSummary = async () => {
    if (!selectedFile) {
      setError("Please select a PDF file first");
      return;
    }

    setIsLoading(true);
    setError("");
    setSummary("");
    setAudioUrl("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/summary/${encodeURIComponent(selectedFile)}/${difficulty}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate summary");
      }

      const data = await response.json();
      setSummary(data.summary);
      
      if (data.audio_path) {
        // Convert to full URL
        const fullAudioUrl = `http://127.0.0.1:8000${data.audio_path}`;
        setAudioUrl(fullAudioUrl);
        
        // Create audio element
        const audioElement = new Audio(fullAudioUrl);
        audioElement.addEventListener("ended", () => setIsPlaying(false));
        setAudio(audioElement);
      }
    } catch (error) {
      console.error("Error generating summary:", error);
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

  const downloadSummary = () => {
    if (!summary) return;

    const blob = new Blob([summary], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedFile.replace(".pdf", "")}_summary.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">PDF Summary Generator</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Select PDF File</label>
        <select
          className="w-full p-2 border rounded-md"
          value={selectedFile}
          onChange={(e) => setSelectedFile(e.target.value)}
          disabled={isLoading}
        >
          <option value="">-- Select a PDF file --</option>
          {pdfFiles.map((file) => (
            <option key={file} value={file}>
              {file}
            </option>
          ))}
        </select>
      </div>
      
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Difficulty Level</label>
        <div className="flex space-x-2">
          {["beginner", "intermediate", "advanced"].map((level) => (
            <button
              key={level}
              className={`px-3 py-1 rounded ${
                difficulty === level 
                  ? "bg-blue-500 text-white" 
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
              onClick={() => setDifficulty(level)}
              disabled={isLoading}
            >
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </button>
          ))}
        </div>
      </div>
      
      <button
        className="w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 disabled:bg-gray-400 mb-4"
        onClick={generateSummary}
        disabled={isLoading || !selectedFile}
      >
        {isLoading ? "Generating..." : "Generate Summary"}
      </button>
      
      {summary && (
        <div className="mt-4">
          <h2 className="text-xl font-semibold mb-2">Summary</h2>
          <div className="bg-gray-100 p-4 rounded-md max-h-60 overflow-y-auto mb-4">
            {summary}
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
              onClick={downloadSummary}
              disabled={!summary}
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