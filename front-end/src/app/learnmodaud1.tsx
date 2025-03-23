import { useState } from 'react';

const MnemonicComponent = () => {
  const [input, setInput] = useState("");
  const [mnemonic, setMnemonic] = useState("");
  const [audio, setAudio] = useState("");
  const [generated, setGenerated] = useState(false);

  const handleGenerate = async () => {
    const formData = new FormData();
    formData.append("input_text", input);
  
    const response = await fetch("http://127.0.0.1:8000/generate-mnemonic/", {
      method: "POST",
      body: formData,
    });
  
    const data = await response.json();
    setMnemonic(data.mnemonic);
    setAudio(data.audio_url);
    setGenerated(true);
  };

  const handlePlayAudio = () => {
    const audioElement = new Audio(`http://127.0.0.1:8000${audio}`);
    audioElement.play();
  };

  const handleDownload = () => {
    const blob = new Blob([mnemonic], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mnemonic.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card bg-white shadow-lg p-6 rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Mnemonic Generator</h2>
      <p className="mb-2">Enter a keyword or phrase to generate a mnemonic:</p>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="input input-bordered w-full mb-4"
      />
      <button
        onClick={handleGenerate}
        className="btn btn-primary w-full mb-4"
      >
        Generate Mnemonic
      </button>
      {generated && (
        <div>
          <div className="mb-4">
            <label className="block text-lg font-semibold mb-2">Generated Mnemonic:</label>
            <textarea
              className="textarea textarea-primary w-full"
              rows={3}
              value={mnemonic}
              readOnly
            />
          </div>
          <div className="flex flex-col gap-4">
            <button
              onClick={handlePlayAudio}
              className="btn btn-success w-full"
            >
              Play Audio
            </button>
            <button
              onClick={handleDownload}
              className="btn btn-secondary w-full"
            >
              Download Mnemonic
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MnemonicComponent;