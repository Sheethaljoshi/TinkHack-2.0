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
    <div className=" min-h-full flex bg-base-200 rounded-3xl">
      <div className='flex flex-col'>
        <div className='font-semibold mt-8 ml-12 mb-6'>
          <div className='text-5xl text-[#343232]'>Welcome</div>
          <div className='text-8xl mt-1 text-[#343232] font-extrabold'>Sheethal!</div>
        </div>
        <div className='ml-10'>
          <div className='mt-3 flex gap-4'>
          <div className='w-2/3'>
          <VoiceAssistant/>
          </div>
          <div className='w-1/3'>
          <VoiceAssistant1/>
          </div>
          </div>
          <div className='mt-5'>
          <JournalEntry/>
          </div>
       
        </div>
      </div>
      <div className='flex flex-col gap-5 ml-16 mt-5'>
        <div className=''>
          <StoryGenerator/>
        </div>
      </div>
  </div>
  </div>
  );
};

export default HomeContent;