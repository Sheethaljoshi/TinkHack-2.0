import { useState } from 'react';

const DifficultySelector = () => {
  const [difficulty, setDifficulty] = useState(1);
  const [generated, setGenerated] = useState(false);

  const handleGenerate = () => {
    setGenerated(true);
  };

  const handlePlayAudio = () => {
    const audio = new Audio('/success_sound.mp3');
    audio.play();
  };

  const handleDownload = () => {
    const noteContent = `Difficulty selected: ${difficulty}`;
    const blob = new Blob([noteContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'notes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col items-center p-4 bg-white shadow-lg rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Select Difficulty</h2>
      <input
        type="range"
        min="1"
        max="3"
        step="1"
        value={difficulty}
        onChange={(e) => setDifficulty(Number(e.target.value))}
        className="range range-primary mb-4"
      />
      <span className="text-lg font-semibold">Difficulty: {difficulty}</span>
      {!generated ? (
        <button
          onClick={handleGenerate}
          className="btn btn-primary mt-4"
        >
          Generate
        </button>
      ) : (
        <>
          <button
            onClick={handlePlayAudio}
            className="btn btn-success mt-4"
          >
            Play
          </button>
          <button
            onClick={handleDownload}
            className="btn btn-secondary mt-4"
          >
            Download Notes
          </button>
        </>
      )}
    </div>
  );
};

export default DifficultySelector;