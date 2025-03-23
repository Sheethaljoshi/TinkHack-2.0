import { useState } from 'react';

const StoryTellingComponent = () => {
  const [transcript, setTranscript] = useState("Once upon a time...");
  const [audio, setAudio] = useState("/sample_audio.mp3");
  const [generated, setGenerated] = useState(false);

  const handleGenerate = () => {
    setGenerated(true);
    // Add logic to generate story and audio
  };

  const handlePlayAudio = () => {
    const audioElement = new Audio(audio);
    audioElement.play();
  };

  return (
    <div className="flex flex-col items-center p-4 bg-white shadow-lg rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Story Telling Component</h2>
      <textarea
        className="textarea textarea-primary w-full h-full mb-4"
        rows={4}
        value={transcript}
        readOnly
      />
      {!generated ? (
        <button
          onClick={handleGenerate}
          className="btn btn-primary mt-4"
        >
          Generate
        </button>
      ) : (
        <div className="flex flex-row gap-2 mt-4">
          <button
            onClick={handlePlayAudio}
            className="btn btn-success"
          >
            Play
          </button>
          <button
            onClick={() => alert("Audio and Transcript")}
            className="btn btn-secondary"
          >
            Download
          </button>
        </div>
      )}
    </div>
  );
};

export default StoryTellingComponent;