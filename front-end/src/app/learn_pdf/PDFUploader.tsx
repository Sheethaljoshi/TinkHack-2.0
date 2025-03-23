"use client";
import { useState, useEffect, useRef } from "react";
import { FaUpload, FaFile, FaCheck, FaTimes, FaBook, FaFeather } from "react-icons/fa";

export default function PDFUploader() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [pdfFiles, setPdfFiles] = useState<string[]>([]);
  const [uploadedFilename, setUploadedFilename] = useState<string>("");
  const [summary, setSummary] = useState<string>("");
  const [story, setStory] = useState<string>("");
  const [isSummaryLoading, setIsSummaryLoading] = useState<boolean>(false);
  const [isStoryLoading, setIsStoryLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch available PDF files on component mount
  useEffect(() => {
    fetchPdfFiles();
  }, []);

  const fetchPdfFiles = async () => {
    try {
      setStatusMessage("Loading PDF files...");
      console.log("Fetching PDF file list...");
      
      const response = await fetch("http://127.0.0.1:8000/list_pdf_files");
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch PDF files");
      }
      
      const data = await response.json();
      console.log("PDF files:", data.files);
      setPdfFiles(data.files || []);
      setUploadStatus("idle");
      setStatusMessage("");
    } catch (error) {
      console.error("Error fetching PDF files:", error);
      setStatusMessage(`Failed to load existing PDF files: ${error instanceof Error ? error.message : "Server might be unavailable"}`);
      setUploadStatus("error");
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
        setSelectedFile(file);
        setUploadStatus("idle");
        setStatusMessage("");
      } else {
        setSelectedFile(null);
        setUploadStatus("error");
        setStatusMessage("Please select a PDF file.");
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus("error");
      setStatusMessage("Please select a file first");
      return;
    }

    setIsUploading(true);
    setUploadStatus("idle");
    setStatusMessage("Uploading...");
    setSummary("");
    setStory("");
    setErrorMessage("");

    try {
      console.log("Uploading file:", selectedFile.name);
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch("http://127.0.0.1:8000/upload_pdf", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = "Upload failed";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (parseError) {
          console.error("Error parsing error response:", parseError);
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log("Upload response:", data);
      
      setUploadStatus("success");
      setStatusMessage(`File "${data.filename}" uploaded successfully!`);
      setUploadedFilename(data.filename);
      setSelectedFile(null);
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      
      // Refresh the file list
      await fetchPdfFiles();

      // Auto-generate summary and story for the uploaded file
      generateSummary(data.filename);
      generateStory(data.filename);
    } catch (error) {
      console.error("Error uploading file:", error);
      setUploadStatus("error");
      setStatusMessage(`Upload failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsUploading(false);
    }
  };

  const generateSummary = async (filename: string) => {
    if (!filename) return;

    setIsSummaryLoading(true);
    setSummary("");
    setErrorMessage("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/summary/${encodeURIComponent(filename)}/beginner`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate summary");
      }

      const data = await response.json();
      setSummary(data.summary);
    } catch (error) {
      console.error("Error generating summary:", error);
      setErrorMessage(`Error generating summary: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsSummaryLoading(false);
    }
  };

  const generateStory = async (filename: string) => {
    if (!filename) return;

    setIsStoryLoading(true);
    setStory("");
    setErrorMessage("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/story/${encodeURIComponent(filename)}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate story");
      }

      const data = await response.json();
      setStory(data.story);
    } catch (error) {
      console.error("Error generating story:", error);
      setErrorMessage(`Error generating story: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsStoryLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">PDF File Uploader</h1>
      
      <div className="mb-6">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 flex flex-col items-center">
          <FaFile className="text-4xl text-gray-400 mb-2" />
          <p className="mb-4 text-sm text-gray-500">
            Select a PDF file to upload or drag and drop it here
          </p>
          
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf"
            className="hidden"
            id="pdf-upload"
          />
          
          <label
            htmlFor="pdf-upload"
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 cursor-pointer flex items-center"
          >
            <FaUpload className="mr-2" />
            Browse Files
          </label>
          
          {selectedFile && (
            <div className="mt-4 text-sm">
              Selected: <span className="font-semibold">{selectedFile.name}</span> ({Math.round(selectedFile.size / 1024)} KB)
            </div>
          )}
        </div>
        
        {uploadStatus !== 'idle' && (
          <div className={`mt-3 p-3 rounded-md ${
            uploadStatus === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            <div className="flex items-center">
              {uploadStatus === 'success' ? (
                <FaCheck className="mr-2" />
              ) : (
                <FaTimes className="mr-2" />
              )}
              {statusMessage}
            </div>
          </div>
        )}
        
        <button
          className="mt-4 w-full bg-green-500 text-white py-2 rounded-md hover:bg-green-600 disabled:bg-gray-400 flex items-center justify-center"
          onClick={handleUpload}
          disabled={isUploading || !selectedFile}
        >
          {isUploading ? "Uploading..." : "Upload PDF"}
        </button>
      </div>
      
      {uploadedFilename && (
        <div className="mt-8 p-4 border rounded-md">
          <h2 className="text-xl font-semibold mb-3">Generate Content for "{uploadedFilename}"</h2>
          
          {errorMessage && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
              {errorMessage}
            </div>
          )}
          
          {(isSummaryLoading || isStoryLoading) && (
            <div className="mb-4 p-3 bg-blue-100 text-blue-700 rounded-md">
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {isSummaryLoading && isStoryLoading ? "Generating summary and story..." : 
                 isSummaryLoading ? "Generating summary..." : "Generating story..."}
              </div>
            </div>
          )}
          
          <div className="flex space-x-2 mb-6">
            <button
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center disabled:bg-gray-400"
              onClick={() => generateSummary(uploadedFilename)}
              disabled={isSummaryLoading}
            >
              <FaBook className="mr-2" />
              {isSummaryLoading ? "Generating Summary..." : "Generate Summary"}
            </button>
            
            <button
              className="px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 flex items-center disabled:bg-gray-400"
              onClick={() => generateStory(uploadedFilename)}
              disabled={isStoryLoading}
            >
              <FaFeather className="mr-2" />
              {isStoryLoading ? "Generating Story..." : "Generate Story"}
            </button>
          </div>
          
          {summary && (
            <div className="mb-4">
              <h3 className="text-lg font-semibold mb-2">Summary</h3>
              <div className="bg-gray-100 p-4 rounded-md max-h-60 overflow-y-auto">
                {summary}
              </div>
            </div>
          )}
          
          {story && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Story</h3>
              <div className="bg-gray-100 p-4 rounded-md max-h-60 overflow-y-auto">
                {story}
              </div>
            </div>
          )}
        </div>
      )}
      
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-2">Available PDF Files</h2>
        {pdfFiles.length > 0 ? (
          <ul className="bg-gray-100 p-3 rounded-md max-h-60 overflow-y-auto">
            {pdfFiles.map((file, index) => (
              <li key={index} className="flex items-center py-1 border-b border-gray-200 last:border-0">
                <FaFile className="text-gray-500 mr-2" />
                <span className="flex-grow">{file}</span>
                <div className="flex space-x-2">
                  <button
                    onClick={() => generateSummary(file)}
                    className="text-blue-500 hover:text-blue-700"
                    title="Generate Summary"
                  >
                    <FaBook />
                  </button>
                  <button
                    onClick={() => generateStory(file)}
                    className="text-purple-500 hover:text-purple-700"
                    title="Generate Story"
                  >
                    <FaFeather />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500 italic">No PDF files available. Upload one to get started!</p>
        )}
      </div>
    </div>
  );
} 