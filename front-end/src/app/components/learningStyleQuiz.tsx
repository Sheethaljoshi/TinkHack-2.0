"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FaHeadphones } from "react-icons/fa";
import { FaEye } from "react-icons/fa";
import { IconContext } from "react-icons";

interface LearningStyleQuizProps {
  onComplete?: () => void;
}

const LearningStyleQuiz: React.FC<LearningStyleQuizProps> = ({ onComplete }) => {
  const router = useRouter();
  const [showQuiz, setShowQuiz] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<{[key: string]: boolean}>({});
  
  const auditoryQuestions = [
    "Do you remember things better when you hear them rather than see them?",
    "Do you enjoy listening to audiobooks or podcasts?",
    "Do you find it easier to follow spoken instructions than written ones?",
    "Do you talk to yourself or read out loud to understand something better?",
    "Do you prefer attending lectures or discussions over reading slides?",
    "Do background sounds easily distract you while studying?",
    "Do you often memorize by repeating information out loud?"
  ];
  
  const visualQuestions = [
    "Do you remember faces better than names?",
    "Do you prefer using diagrams, charts, or maps when learning?",
    "Do you find it easier to understand written instructions than verbal ones?",
    "Do you visualize concepts or pictures in your head to remember them?",
    "Do you enjoy watching videos to learn something new?",
    "Do you find color-coding and highlighting helpful while studying?",
    "Do you prefer reading over listening to explanations?"
  ];
  
  // All questions combined and labeled with type
  const allQuestions = [
    ...auditoryQuestions.map(q => ({ text: q, type: 'auditory' })),
    ...visualQuestions.map(q => ({ text: q, type: 'visual' }))
  ];
  
  // Shuffle questions to mix auditory and visual
  const shuffleArray = (array: any[]) => {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  };
  
  const [shuffledQuestions] = useState(shuffleArray(allQuestions));
  
  useEffect(() => {
    // Check if we already have learning style in localStorage
    const storedLearningStyle = localStorage.getItem('learningStyle');
    
    if (storedLearningStyle) {
      setShowQuiz(false);
      if (onComplete) onComplete();
    }
  }, [onComplete]);
  
  const handleAnswer = (answer: boolean) => {
    const currentQuestion = shuffledQuestions[currentStep];
    
    setAnswers({
      ...answers,
      [currentQuestion.text]: answer
    });
    
    if (currentStep < shuffledQuestions.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Quiz completed, determine learning style
      determineLearningStyle();
    }
  };
  
  const determineLearningStyle = () => {
    let auditoryCount = 0;
    let visualCount = 0;
    
    // Count yes answers for each type
    Object.keys(answers).forEach(question => {
      const questionObj = allQuestions.find(q => q.text === question);
      if (questionObj && answers[question]) {
        if (questionObj.type === 'auditory') {
          auditoryCount++;
        } else {
          visualCount++;
        }
      }
    });
    
    // Determine dominant style
    const learningStyle = auditoryCount > visualCount ? 'auditory' : 'visual';
    
    // Store in localStorage
    localStorage.setItem('learningStyle', learningStyle);
    
    // Notify parent component that quiz is complete
    if (onComplete) {
      onComplete();
    }
    
    // Redirect to appropriate route
    const route = learningStyle === 'auditory' ? '/learn_audio' : '/learn_visual';
    router.push(route);
  };
  
  const skipQuiz = () => {
    // Default to visual if skipped
    localStorage.setItem('learningStyle', 'visual');
    setShowQuiz(false);
    
    // Notify parent component that quiz is complete
    if (onComplete) {
      onComplete();
    }
    
    // Redirect to visual learning page
    router.push('/learn_visual');
  };
  
  if (!showQuiz) {
    return null;
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-8 rounded-lg max-w-md w-full shadow-xl dark:bg-gray-800 dark:text-white">
        <h2 className="text-2xl font-bold mb-6 text-center">Learning Style Quiz</h2>
        
        {currentStep < shuffledQuestions.length ? (
          <>
            <div className="mb-6">
              <div className="flex justify-between mb-2 text-sm text-gray-500 dark:text-gray-300">
                <span>Question {currentStep + 1} of {shuffledQuestions.length}</span>
                <span>
                  {shuffledQuestions[currentStep].type === 'auditory' ? (
                    <span className="flex items-center">
                      <IconContext.Provider value={{ className: "mr-1" }}>
                        <FaHeadphones />
                      </IconContext.Provider>
                      Listening
                    </span>
                  ) : (
                    <span className="flex items-center">
                      <IconContext.Provider value={{ className: "mr-1" }}>
                        <FaEye />
                      </IconContext.Provider>
                      Visual
                    </span>
                  )}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-600">
                <div 
                  className="bg-blue-600 h-2.5 rounded-full" 
                  style={{ width: `${((currentStep + 1) / shuffledQuestions.length) * 100}%` }}
                ></div>
              </div>
            </div>
            
            <p className="text-lg mb-8 text-center">{shuffledQuestions[currentStep].text}</p>
            
            <div className="flex justify-center space-x-4">
              <button 
                onClick={() => handleAnswer(true)}
                className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
              >
                Yes
              </button>
              <button 
                onClick={() => handleAnswer(false)}
                className="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
              >
                No
              </button>
            </div>
            
            <div className="mt-6 text-center">
              <button 
                onClick={skipQuiz} 
                className="text-gray-500 hover:text-gray-700 transition dark:text-gray-300 dark:hover:text-gray-100"
              >
                Skip Quiz
              </button>
            </div>
          </>
        ) : (
          <div className="text-center">
            <p className="text-lg mb-4">Analyzing your responses...</p>
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LearningStyleQuiz; 