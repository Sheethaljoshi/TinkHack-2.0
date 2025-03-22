"use client"
import React, { useState, useEffect } from 'react';
import VoiceAssistant from '../voice';
import VoiceAssistant2 from '../learnmodaud';


const ContentPage: React.FC = () => {

    return (
        <div className="flex gap-10 w-full p-10 bg-base-200 rounded-2xl">
            <div className='flex flex-col gap-5 w-1/2'>
                <div>
                <VoiceAssistant2/>
                </div>
                <div>
                <VoiceAssistant2/>
                </div>
            </div>
            <div className='flex flex-col gap-5 w-1/2'>
                <div>
                <VoiceAssistant2/>
                </div>
                <div>
                <VoiceAssistant2/>
                </div>
            </div>
           
        </div>
    );
};

export default ContentPage;
