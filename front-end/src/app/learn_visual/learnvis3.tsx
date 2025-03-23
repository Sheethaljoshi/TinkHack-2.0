import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface StoryPart {
  text: string;
  image: string;
}

const StoryBoard: React.FC = () => {
  const [stories, setStories] = useState<StoryPart[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStory, setSelectedStory] = useState<StoryPart | null>(null);

  const generateStory = async () => {
    try {
      const response = await axios.post('http://localhost:8000/generate-story-from-pdf/');
      setStories(response.data.story_parts);
    } catch (err) {
      setError('Failed to generate story. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    generateStory();
  }, []);

  return (
    <div className="h-[77vh] w-full flex flex-col bg-white rounded-lg shadow-lg">
      <div className="p-2 bg-white shadow-sm">
        <h1 className="text-2xl font-bold text-center">Story Board</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="loading loading-spinner loading-lg"></div>
              <p className="mt-2">Generating your story...</p>
            </div>
          </div>
        ) : error ? (
          <div className="h-full flex items-center justify-center">
            <div className="alert alert-error">
              {error}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-4">
            {stories.map((story, index) => (
              <div 
                key={index} 
                className="bg-base-200 rounded-lg shadow-md p-4 flex flex-col md:flex-row gap-4 cursor-pointer hover:bg-base-300 transition-colors"
                onClick={() => setSelectedStory(story)}
              >
                <div className="md:w-1/3 flex-shrink-0">
                  <div className="relative w-full aspect-square">
                    <img 
                      src={story.image} 
                      alt={`story-${index}`} 
                      className="absolute inset-0 w-full h-full object-cover rounded-lg"
                    />
                  </div>
                </div>
                <div className="md:w-2/3">
                  <h3 className="text-lg font-semibold mb-2">Part {index + 1}</h3>
                  <div className="prose max-w-none">
                    <div className="text-sm leading-relaxed">
                      <div className="line-clamp-4">
                        {story.text}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal */}
      {selectedStory && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedStory(null)}
        >
          <div 
            className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-4">
              <div className="flex justify-between items-start mb-3">
                <h2 className="text-xl font-bold">Full Story</h2>
                <button 
                  className="btn btn-ghost btn-sm"
                  onClick={() => setSelectedStory(null)}
                >
                  ✕
                </button>
              </div>
              <div className="flex flex-col md:flex-row gap-4">
                <div className="md:w-1/2">
                  <div className="relative w-full aspect-square">
                    <img 
                      src={selectedStory.image} 
                      alt="story-image" 
                      className="absolute inset-0 w-full h-full object-cover rounded-lg"
                    />
                  </div>
                </div>
                <div className="md:w-1/2">
                  <div className="prose max-w-none">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {selectedStory.text}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StoryBoard;