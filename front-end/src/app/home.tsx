"use client"
import React, { useState } from 'react';
import Accordion from './components/accordion';
import Modalchat from './components/modalchat';
import StoryGenerator from './story';
import JournalEntry from './journal';
import VoiceAssistant from './voice';
import VoiceAssistant1 from './map';



const HomeContent: React.FC = () => {
  const [showModalchat, setShowModalchat] = useState(false);
  return (
    <div className='min-h-full bg-base-200 rounded-3xl'><div className='flex justify-end'>
        <label htmlFor="my-drawer-2" className="btn btn-primary drawer-button lg:hidden mr-14 mt-4">|||</label>
        </div>
    <div className=" min-h-full flex gap-3 bg-base-200 rounded-3xl">
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
          Meet your personal AI tutor—a real-time assistant that quizzes you, reinforces what you’ve learned, and explains any topic from your study history. Try it now and start learning smarter!
          </div>
        </div>
      </div>
        <div className='ml-16 flex items-center p-10'>
          <VoiceAssistant/>
        </div>
      </div>
  </div>
  </div>
  );
};

export default HomeContent;