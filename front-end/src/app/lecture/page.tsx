"use client"
import React, { useState } from 'react';
import AILecturer from '../learn_visual/AILecturer';
import Link from 'next/link';

export default function LecturePage() {
  const [showInstructions, setShowInstructions] = useState(false);

  return (
    <div className="w-full min-h-screen p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Real-time AI Lecture</h1>
        <button 
          onClick={() => setShowInstructions(!showInstructions)} 
          className="btn btn-sm btn-outline"
        >
          {showInstructions ? "Hide Instructions" : "Show Instructions"}
        </button>
      </div>
      
      {showInstructions && (
        <div className="alert alert-info mb-4">
          <div>
            <h3 className="font-bold">Setup Instructions</h3>
            <ol className="list-decimal list-inside ml-2">
              <li>Make sure the backend server is running with: <code className="bg-base-300 px-2 py-1 rounded">python text.py</code></li>
              <li>Ensure you have a D-ID API key in a <code className="bg-base-300 px-2 py-1 rounded">.env</code> file <strong>in the same directory as text.py</strong> (not in the frontend): 
                <pre className="bg-base-300 px-2 py-1 rounded mt-1 text-xs">DID_API_KEY=your_key_here</pre>
              </li>
              <li>The system will try to use the D-ID API to generate a video lecturer, but will fall back to a YouTube video if there are any issues.</li>
              <li>If you're seeing errors, check the browser console for more details.</li>
            </ol>
          </div>
        </div>
      )}
      
      <AILecturer />
    </div>
  );
} 