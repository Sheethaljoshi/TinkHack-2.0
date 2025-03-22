"use client";
import { TbHomeMove } from "react-icons/tb";

const VoiceAssistant1: React.FC = () => {

  return (
    <div className="max-w-xs flex flex-col justify-evenly items-center h-full mx-auto p-4 bg-base-100 shadow-lg rounded-xl">
      <div className="text-xl font-bold text-[#343232]">Follow me</div>
      <div className="flex justify-center">
        <button className="btn btn-primary rounded-md font-extrabold text-2xl">
          <TbHomeMove />
        </button>
      </div>
    </div>
  );
};

export default VoiceAssistant1;