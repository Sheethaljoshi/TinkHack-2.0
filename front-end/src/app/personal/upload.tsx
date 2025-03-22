import { useState } from "react";

export default function UploadMedicalDocuments() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  return (
    <div className="max-w-lg mx-auto p-6 rounded-2xl shadow-lg border border-gray-300 bg-white">
      <div className="flex flex-col items-center gap-4">
        <h2 className="text-lg font-semibold">Upload Medical Documents</h2>
        <input 
          type="file" 
          accept=".pdf,.doc,.docx" 
          onChange={handleFileChange} 
          className=" file-input file-input-primary" 
          id="file-upload"
        />
    </div>
    </div>
  );
}