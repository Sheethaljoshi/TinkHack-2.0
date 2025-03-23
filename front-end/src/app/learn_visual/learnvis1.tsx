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

const Flashcards: React.FC = () => {
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [score, setScore] = useState(0);
  const [showScore, setShowScore] = useState(false);

  useEffect(() => {
    const fetchFlashcards = async () => {
      try {
        const response = await axios.post('http://localhost:8000/generate-flashcards/');
        setFlashcards(response.data.flashcards);
      } catch (err) {
        setError('Failed to load flashcards. Please try again.');
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchFlashcards();
  }, []);

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

  if (loading) {
    return (
      <div className="h-[70vh] w-full flex items-center justify-center bg-white rounded-lg shadow-lg">
        <div className="text-center">
          <div className="loading loading-spinner loading-lg"></div>
          <p className="mt-2">Loading flashcards...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-[70vh] w-full flex items-center justify-center bg-white rounded-lg shadow-lg">
        <div className="alert alert-error">
          {error}
        </div>
      </div>
    );
  }

  if (showScore) {
    return (
      <div className="h-[70vh] w-full flex flex-col items-center justify-center bg-white rounded-lg shadow-lg p-4">
        <h2 className="text-2xl font-bold mb-4">Quiz Complete!</h2>
        <p className="text-xl mb-4">Your score: {score} out of {flashcards.length}</p>
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
      </div>
    );
  }

  const currentCard = flashcards[currentIndex];

  return (
    <div className="h-[70vh] w-full flex flex-col bg-white rounded-lg shadow-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <span className="text-sm text-gray-500">
          Card {currentIndex + 1} of {flashcards.length}
        </span>
        <span className="text-sm text-gray-500">
          Difficulty: {currentCard.difficulty}
        </span>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="text-xl font-semibold text-center mb-4">
          {currentCard.question}
        </div>

        {showHint && (
          <div className="text-sm text-gray-600 mb-4">
            Hint: {currentCard.hint}
          </div>
        )}

        {showAnswer && (
          <div className="text-lg text-center mb-4">
            {currentCard.answer}
          </div>
        )}

        <div className="flex gap-2 mt-4">
          {!showAnswer ? (
            <>
              <button
                className="btn btn-primary"
                onClick={handleShowAnswer}
              >
                Show Answer
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleShowHint}
              >
                Show Hint
              </button>
            </>
          ) : (
            <>
              <button
                className="btn btn-success"
                onClick={handleCorrect}
              >
                Correct
              </button>
              <button
                className="btn btn-error"
                onClick={handleIncorrect}
              >
                Incorrect
              </button>
            </>
          )}
        </div>

        <div className="flex gap-2 mt-4">
          <button
            className="btn btn-ghost"
            onClick={handlePrevious}
            disabled={currentIndex === 0}
          >
            Previous
          </button>
          <button
            className="btn btn-ghost"
            onClick={handleNext}
            disabled={currentIndex === flashcards.length - 1}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default Flashcards;
