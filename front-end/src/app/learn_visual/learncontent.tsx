"use client"
import React, { useState, useEffect } from 'react';
import VoiceAssistant2 from './learnvis1';
import VoiceAssistant4 from './learnvis2';
import VoiceAssistant5 from './learnvis3';


const ContentPage: React.FC = () => {

    return (
        <div className="flex gap-10 w-full p-10 bg-base-200 rounded-2xl">
            <div className='flex flex-col gap-9 w-1/2'>
                <div>
                <VoiceAssistant2/>
                </div>
                <div>
                
                </div>
            </div>
            <div className='flex flex-col gap-5 w-1/2 h-full'>
                <div>
                <VoiceAssistant5/>
                </div>
            </div>
           
        </div>
    );
};

export default ContentPage;
