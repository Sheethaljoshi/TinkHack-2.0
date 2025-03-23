"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import LearningStyleQuiz from './learningStyleQuiz';

const OnboardingModal: React.FC = () => {
  const router = useRouter();
  const [showModal, setShowModal] = useState(false);
  const [showIntro, setShowIntro] = useState(true);
  const [showQuiz, setShowQuiz] = useState(false);
  
  useEffect(() => {
    // Check if user has completed onboarding
    const hasCompletedOnboarding = localStorage.getItem('hasCompletedOnboarding');
    const learningStyle = localStorage.getItem('learningStyle');
    
    // Show modal if user hasn't completed onboarding
    if (!hasCompletedOnboarding && !learningStyle) {
      setShowModal(true);
    }
  }, []);
  
  const handleQuizComplete = () => {
    // Set that user has completed onboarding
    localStorage.setItem('hasCompletedOnboarding', 'true');
    setShowModal(false);
    
    // Get the learning style and redirect
    const learningStyle = localStorage.getItem('learningStyle');
    if (learningStyle) {
      const route = learningStyle === 'auditory' ? '/learn_audio' : '/learn_visual';
      router.push(route);
    }
  };
  
  const handleStartQuiz = () => {
    // Hide intro, show quiz
    setShowIntro(false);
    setShowQuiz(true);
  };
  
  const handleSkipQuiz = () => {
    // Default to visual learning style
    localStorage.setItem('learningStyle', 'visual');
    localStorage.setItem('hasCompletedOnboarding', 'true');
    
    // Close modal and redirect
    setShowModal(false);
    router.push('/learn_visual');
  };
  
  if (!showModal) {
    return null;
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      {showIntro && (
        <div className="bg-white p-8 rounded-lg max-w-md w-full shadow-xl dark:bg-gray-800 dark:text-white">
          <h2 className="text-2xl font-bold mb-4 text-center">Welcome to TinkHack!</h2>
          
          <p className="mb-4">
            We&apos;re excited to help you learn to code in a way that matches how you&apos;re most comfortable learning.
          </p>
          
          <p className="mb-4">
            Everyone learns differently. Some people prefer visual learning with text and diagrams, while others learn better through audio and discussion.
          </p>
          
          <p className="mb-6">
            Take our quick quiz to personalize your learning experience, or start right away with our default approach.
          </p>
          
          <div className="flex flex-col space-y-3">
            <button 
              onClick={handleStartQuiz}
              className="w-full py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
            >
              Take the Quiz
            </button>
            
            <button 
              onClick={handleSkipQuiz}
              className="w-full py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
            >
              Start Learning
            </button>
          </div>
        </div>
      )}
      
      {showQuiz && (
        <LearningStyleQuiz onComplete={handleQuizComplete} />
      )}
    </div>
  );
};

export default OnboardingModal; 