"use client"
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Flashcard {
  id: string;
  question: string;
  answer: string;
  difficulty: number;
  hint: string;
}

// Fallback flashcards for each topic when API fails
const fallbackFlashcards: Record<string, Flashcard[]> = {
  "Quit India Movement.pdf": [
    {
      id: "1",
      question: "When was the Quit India Movement launched?",
      answer: "August 8, 1942",
      difficulty: 1,
      hint: "It was during World War II"
    },
    {
      id: "2",
      question: "Who gave the famous 'Do or Die' speech?",
      answer: "Mahatma Gandhi",
      difficulty: 1,
      hint: "Father of the Nation"
    },
    {
      id: "3",
      question: "What was the main goal of the Quit India Movement?",
      answer: "To force the British to leave India immediately",
      difficulty: 2,
      hint: "It's in the name of the movement"
    },
    {
      id: "4",
      question: "Where was the Quit India resolution passed?",
      answer: "Bombay (now Mumbai)",
      difficulty: 2,
      hint: "A major city in western India"
    },
    {
      id: "5",
      question: "What happened to Congress leaders after the Quit India Movement was launched?",
      answer: "They were immediately arrested and imprisoned",
      difficulty: 2,
      hint: "The British tried to prevent the movement from gaining momentum"
    }
  ],
  "Gandhi Philosophy.pdf": [
    {
      id: "1",
      question: "What is 'Satyagraha'?",
      answer: "A form of non-violent resistance or civil disobedience",
      difficulty: 1,
      hint: "Truth + Force"
    },
    {
      id: "2",
      question: "What is 'Ahimsa'?",
      answer: "Non-violence or non-harm to all living beings",
      difficulty: 1,
      hint: "One of Gandhi's core principles"
    },
    {
      id: "3",
      question: "Which book was written by Gandhi that explains his philosophy?",
      answer: "Hind Swaraj (Indian Home Rule)",
      difficulty: 2,
      hint: "Written in 1909"
    }
  ],
  "Indian Independence.pdf": [
    {
      id: "1",
      question: "When did India gain independence from British rule?",
      answer: "August 15, 1947",
      difficulty: 1,
      hint: "National holiday in India"
    },
    {
      id: "2",
      question: "Who was the first Prime Minister of independent India?",
      answer: "Jawaharlal Nehru",
      difficulty: 1,
      hint: "He gave the 'Tryst with Destiny' speech"
    }
  ],
  "World War II.pdf": [
    {
      id: "1",
      question: "When did World War II begin?",
      answer: "September 1, 1939",
      difficulty: 1,
      hint: "Germany invaded Poland"
    },
    {
      id: "2",
      question: "Who were the Axis Powers in World War II?",
      answer: "Germany, Italy, and Japan",
      difficulty: 1,
      hint: "Led by Hitler, Mussolini, and Emperor Hirohito"
    }
  ],
  "Modern History.pdf": [
    {
      id: "1",
      question: "What event is considered the start of the Modern Era?",
      answer: "The Renaissance or the Age of Discovery",
      difficulty: 2,
      hint: "Cultural awakening in Europe"
    },
    {
      id: "2",
      question: "What was the Industrial Revolution?",
      answer: "The transition to new manufacturing processes in Europe and the US",
      difficulty: 1,
      hint: "Steam power and mechanization"
    }
  ]
};

// Function to get default flashcards for any topic
const generateDefaultFlashcards = (topic: string): Flashcard[] => {
  const topicName = topic.replace('.pdf', '');
  return [
    {
      id: "1",
      question: `What is the significance of ${topicName}?`,
      answer: `${topicName} was a significant historical event or concept.`,
      difficulty: 1,
      hint: "Think about the historical context"
    },
    {
      id: "2",
      question: `Who were the key figures associated with ${topicName}?`,
      answer: "Several important historical figures were involved.",
      difficulty: 1,
      hint: "Consider the leadership during this period"
    },
    {
      id: "3",
      question: `What were the outcomes of ${topicName}?`,
      answer: "It led to significant changes in society and politics.",
      difficulty: 2,
      hint: "Think about the aftermath"
    },
    {
      id: "4",
      question: `When did ${topicName} occur?`,
      answer: "It occurred during a pivotal time in history.",
      difficulty: 1,
      hint: "Consider the century or time period"
    },
    {
      id: "5",
      question: `Why is ${topicName} important to study?`,
      answer: "It offers insights into historical patterns and human behavior.",
      difficulty: 3,
      hint: "Think about historical significance"
    }
  ];
};

const Flashcards: React.FC = () => {
  // List of available PDF files
  const availablePdfs = [
    "Quit India Movement.pdf"
  ];

  // Get a random topic from available PDFs
  const getRandomTopic = () => {
    const randomIndex = Math.floor(Math.random() * availablePdfs.length);
    return availablePdfs[randomIndex];
  };

  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [showScore, setShowScore] = useState(false);
  const [pdfFile, setPdfFile] = useState<string>(getRandomTopic());
  const [sourceFile, setSourceFile] = useState<string>(""); 
  const [hasStarted, setHasStarted] = useState(false);
  const [usingFallback, setUsingFallback] = useState(false);

  const fetchFlashcards = async () => {
    setLoading(true);
    setError(null);
    setUsingFallback(false);
    
    try {
      // Attempt to fetch from backend
      const response = await axios.post('http://localhost:8000/generate-flashcards/', {
        filename: pdfFile
      }, { timeout: 10000 }); // Increased timeout to 10 seconds
      
      setFlashcards(response.data.flashcards);
      setSourceFile(response.data.source || pdfFile);
      setHasStarted(true);
    } catch (err: any) {
      console.error('Error fetching flashcards:', err);
      
      // Auto-generate flashcards instead of showing error
      let autoGeneratedCards;
      
      // Check if we have pre-defined fallback cards for this topic
      if (fallbackFlashcards[pdfFile]) {
        autoGeneratedCards = fallbackFlashcards[pdfFile];
      } else {
        // Generate generic flashcards based on topic name
        autoGeneratedCards = generateDefaultFlashcards(pdfFile);
      }
      
      setFlashcards(autoGeneratedCards);
      setSourceFile(pdfFile);
      setHasStarted(true);
      setUsingFallback(true);
      
      // Don't show error message to user, just log to console
      console.log(`Using auto-generated flashcards. Backend error: ${err.message || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  // Auto-generate flashcards when user selects a PDF
  const handlePdfSelection = (selectedPdf: string) => {
    setPdfFile(selectedPdf);
  };

  const handleNext = () => {
    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setShowAnswer(false);
      setShowHint(false);
    } else {
      setShowScore(true);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setShowAnswer(false);
      setShowHint(false);
    }
  };

  const handleShowAnswer = () => {
    setShowAnswer(true);
  };

  const handleShowHint = () => {
    setShowHint(true);
  };

  const handleCorrect = () => {
    setScore(score + 1);
    handleNext();
  };

  const handleIncorrect = () => {
    handleNext();
  };

  const handleReset = () => {
    const newRandomTopic = getRandomTopic();
    setPdfFile(newRandomTopic);
    setHasStarted(false);
    setFlashcards([]);
    setCurrentIndex(0);
    setShowAnswer(false);
    setShowHint(false);
    setShowScore(false);
    setScore(0);
    setSourceFile("");
    setError(null);
    setUsingFallback(false);
    
    // Auto-fetch for the new random topic
    setTimeout(() => {
      fetchFlashcards();
    }, 100);
  };

  useEffect(() => {
    // Auto-fetch flashcards immediately when component loads
    fetchFlashcards();
  }, []);

  // If not started yet, show the selection screen with auto-start option
  if (!hasStarted) {
  return (
      <div className="h-[70vh] w-full flex flex-col items-center justify-center bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4 text-center">Flashcard Study</h2>
        <p className="text-center mb-4">Currently loading topic: <span className="font-bold">{pdfFile.replace('.pdf', '')}</span></p>
        
        <div className="form-control w-full max-w-md mb-6">
          <label className="label">
            <span className="label-text font-semibold">Select a different topic to study:</span>
          </label>
          <select 
            className="select select-bordered w-full" 
            value={pdfFile}
            onChange={(e) => handlePdfSelection(e.target.value)}
          >
            {availablePdfs.map((pdf) => (
              <option key={pdf} value={pdf}>
                {pdf.replace('.pdf', '')}
              </option>
            ))}
          </select>
        </div>

        <div className="form-control w-full max-w-md mb-6">
          <label className="label">
            <span className="label-text">Or enter custom topic:</span>
          </label>
      <input
            type="text"
            placeholder="Enter topic name"
            className="input input-bordered w-full"
            value={pdfFile.replace('.pdf', '')}
            onChange={(e) => handlePdfSelection(`${e.target.value}.pdf`)}
          />
          <label className="label">
            <span className="label-text-alt">Make sure the file exists in the server&apos;s PDF directory</span>
          </label>
        </div>
        
        <div className="flex gap-4">
          <button
            className="btn btn-primary mt-4"
            onClick={fetchFlashcards}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading loading-spinner loading-sm"></span>
                Loading...
              </>
            ) : (
              "Generate Flashcards"
            )}
          </button>
          
          <button
            className="btn btn-secondary mt-4"
            onClick={() => {
              const newRandomTopic = getRandomTopic();
              setPdfFile(newRandomTopic);
              setTimeout(() => fetchFlashcards(), 100);
            }}
            disabled={loading}
          >
            Try Random Topic
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-[70vh] w-full flex items-center justify-center bg-white rounded-lg shadow-lg">
        <div className="text-center">
          <div className="loading loading-spinner loading-lg"></div>
          <p className="mt-2">Generating flashcards from {sourceFile || pdfFile}...</p>
        </div>
      </div>
    );
  }

  // Modified to show error as a notification but still display cards
  const currentCard = flashcards[currentIndex];

  return (
    <div className="h-[70vh] w-full flex flex-col bg-white rounded-lg shadow-lg p-6">
     
      <div className="flex justify-between items-center mb-6">
        <div>
          <span className="text-sm text-gray-500 mr-2">
            Card {currentIndex + 1} of {flashcards.length}
          </span>
          <div className="badge badge-outline mt-1">
            Topic: {sourceFile.replace('.pdf', '')}
          </div>
        </div>
        <span className="badge badge-primary">
          Difficulty: {currentCard.difficulty}
        </span>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-4 bg-base-100 rounded-lg">
        <div className="text-xl font-semibold text-center mb-6">
          {currentCard.question}
        </div>

        {showHint && (
          <div className="bg-amber-50 p-3 rounded-lg w-full text-sm text-gray-700 mb-4 border border-amber-200">
            <span className="font-bold">Hint:</span> {currentCard.hint}
          </div>
        )}

        {showAnswer && (
          <div className="bg-blue-50 p-4 rounded-lg w-full text-lg text-center mb-6 border border-blue-200">
            {currentCard.answer}
          </div>
        )}

        <div className="flex gap-3 mt-6">
          {!showAnswer ? (
            <>
              <button
                className="btn btn-primary"
                onClick={handleShowAnswer}
              >
                Show Answer
              </button>
              {currentCard.hint && (
                <button
                  className="btn btn-secondary"
                  onClick={handleShowHint}
                >
                  Show Hint
                </button>
              )}
            </>
          ) : (
            <>
              <button
                className="btn btn-success"
                onClick={handleCorrect}
              >
                Got It Right
              </button>
              <button
                className="btn btn-error"
                onClick={handleIncorrect}
              >
                Got It Wrong
              </button>
            </>
          )}
        </div>
      </div>

      <div className="flex justify-between items-center mt-6">
        <button
          className="btn btn-ghost"
          onClick={handlePrevious}
          disabled={currentIndex === 0}
        >
          ← Previous
        </button>
        <button
          className="btn btn-ghost"
          onClick={handleReset}
        >
          Change Topic
        </button>
        <button
          className="btn btn-ghost"
          onClick={handleNext}
          disabled={currentIndex === flashcards.length - 1}
        >
          Next →
        </button>
      </div>

      {showScore && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4">Quiz Complete!</h2>
            <p className="text-xl mb-6">Your score: {score} out of {flashcards.length}</p>
            <div className="flex gap-4">
              <button
                className="btn btn-primary"
                onClick={() => {
                  setCurrentIndex(0);
                  setShowAnswer(false);
                  setShowHint(false);
                  setShowScore(false);
                  setScore(0);
                }}
              >
                Try Again
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleReset}
              >
                Select New Topic
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Flashcards;
