"use client"
import React, { useState, useEffect } from 'react';
import Accordion from './components/accordion';
import Modalchat from './components/modalchat';
import StoryGenerator from './story';
import JournalEntry from './journal';
import VoiceAssistant from './voice';
import VoiceAssistant1 from './map';
import OnboardingModal from './components/OnboardingModal';
import { useRouter } from 'next/navigation';

const HomeContent: React.FC = () => {
  const [showModalchat, setShowModalchat] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const router = useRouter();
  
  useEffect(() => {
    // Check if this is the first visit
    const isFirstVisit = !localStorage.getItem('hasVisitedBefore');
    if (isFirstVisit) {
      setShowOnboarding(true);
    }
  }, []);
  
  const handleStartLearning = () => {
    // Trigger custom event to start learning
    const event = new Event('startLearning');
    window.dispatchEvent(event);
    
    // Check if learning style exists and redirect directly if it does
    const learningStyle = localStorage.getItem('learningStyle');
    if (learningStyle) {
      const route = learningStyle === 'auditory' ? '/learn_audio' : '/learn_visual';
      router.push(route);
    } else {
      // Show onboarding if learning style doesn't exist
      setShowOnboarding(true);
    }
  };
  
  return (
    <div className='min-h-full bg-base-200 rounded-3xl'>
      <div className='flex justify-end'>
        <label htmlFor="my-drawer-2" className="btn btn-primary drawer-button lg:hidden mr-14 mt-4">|||</label>
      </div>
      <div className="min-h-full flex gap-3 bg-base-200 rounded-3xl">
        <div className='flex'>
          <div className='w-3/6'>
            <div className='font-semibold mt-8 ml-12 mb-6'>
              <div className='text-5xl text-[#343232]'>Welcome</div>
              <div className='text-8xl mt-1 text-[#343232] font-extrabold'>Sheethal!</div>
              <div className='text-xl font-bold mt-10'>
                AI-Powered Learning Assistant 🎧
              </div>
              <div className='text-md font-normal mt-3'>
                Are you an audio learner? Our AI makes studying effortless with narrated lessons, podcast-style reviews, AI-generated audiobooks, and voice-guided memory drills designed to fit your learning style.
              </div>
              <div className='text-xl font-bold mt-8'>
                Real-Time AI API Assistant 🤖
              </div>
              <div className='text-md font-normal mt-3'>
                Meet your personal AI tutor—a real-time assistant that quizzes you, reinforces what you&apos;ve learned, and explains any topic from your study history. Try it now and start learning smarter!
              </div>
              
              {/* Start Learning Button */}
              <div className='mt-8'>
                <button 
                  onClick={handleStartLearning} 
                  className="btn btn-lg btn-success text-white px-8 py-3 text-xl"
                >
                  Start Learning
                </button>
              </div>
            </div>
          </div>
          <div className='ml-16 flex items-center p-10'>
            <VoiceAssistant/>
          </div>
        </div>
      </div>
      
      {/* Show onboarding modal if needed */}
      {showOnboarding && <OnboardingModal />}
    </div>
  );
};

export default HomeContent;