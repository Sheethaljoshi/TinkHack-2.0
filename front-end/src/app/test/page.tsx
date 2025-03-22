"use client";
import { useState } from "react";
import axios from "axios";
import { FaPlay, FaPause } from "react-icons/fa";

export default function StoryGenerator() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [story, setStory] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);


  const generateStory = async () => {
    setIsGenerating(true);

    try {
      const response = await axios.get("http://localhost:8000/generate_story");
      const { story, audio_url, image_url } = response.data;

      setStory(story);
      setAudioUrl(audio_url);
      setImageUrl(image_url);

      const audioElement = new Audio(audio_url);
      setAudio(audioElement);
    } catch (error) {
      console.error("Error generating story:", error);
    }

    setIsGenerating(false);
  };

  const togglePlay = () => {
    if (audio) {
      if (isPlaying) {
        audio.pause();
      } else {
        audio.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-6 bg-base-100 shadow-xl rounded-2xl">
      <div className="text-2xl font-bold text-[#343232] m-3">Remember When?</div>
      
      <img
        src={imageUrl || "https://cdn.pixabay.com/photo/2025/03/09/08/26/bridge-9456745_1280.jpg"}
        alt="Generated Story"
        width={450}
        height={400}
        className="w-[400px] h-[400px] object-cover rounded-lg mb-3"
      />

      <div className="h-24 mt-4 overflow-y-auto p-2 bg-base-200 rounded-lg shadow-inner">
        <p className="text-[#343232]">{story || "Click Generate to see a memory..."}</p>
      </div>

      <div className="flex justify-center mt-4 mb-2 gap-3">
        {audioUrl && (
          <button
            onClick={togglePlay}
            className="flex justify-center px-3 py-1 bg-primary text-primary-content rounded-lg shadow-md hover:bg-primary-focus transition min-w-36"
          >
            <span className="w-4 h-4 mr-1 mt-1 text-[#343232]">
              {isPlaying ? <FaPause size={16} /> : <FaPlay size={16} />}
            </span>
            {isPlaying ? "Pause" : "Play"}
          </button>
        )}
        <button
          onClick={generateStory}
          className="flex justify-center px-3 py-1 bg-secondary text-primary-content rounded-lg shadow-md hover:bg-primary-focus transition min-w-36"
          disabled={isGenerating}
        >
          <span className="w-4 h-4 mr-1 mt-1 text-[#343232]">
            {isGenerating ? <FaPause size={16} /> : <FaPlay size={16} />}
          </span>
          {isGenerating ? "Generating..." : "Generate"}
        </button>
      </div>
    </div>
  );
}
