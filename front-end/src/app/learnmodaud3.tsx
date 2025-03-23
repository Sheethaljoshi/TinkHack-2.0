"use client";
import { useState, useEffect, useRef } from "react";
import { BsChatLeftHeart } from "react-icons/bs";
import { IconContext } from "react-icons";
import DifficultySelector from "./components/summary";

const VoiceAssistant4: React.FC = () => {
  const [isMounted, setIsMounted] = useState(false);
  const modalRef = useRef<HTMLDialogElement | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null; // Avoid hydration errors

  return (
    <div className="max-w-3xl  mx-auto p-14 bg-base-100 shadow-xl rounded-2xl">
      <div className="text-2xl font-extrabold text-[#343232] mb-4 text-center">
        Having a bad day?
      </div>

      <div className="flex justify-center">
        <button 
          className="btn btn-lg btn-primary px-6 py-3 text-xl flex items-center gap-3" 
          onClick={() => modalRef.current?.showModal()}
        >
          Talk to Remi 
          <IconContext.Provider value={{ color: "black", className: "global-class-name", size:"1.8em" }}>
            <div>
              <BsChatLeftHeart />
            </div>
          </IconContext.Provider>
        </button>
      </div>

      {/* Larger Modal */}
      <dialog ref={modalRef} id="my_modal_4" className="modal">
        <div className="modal-box w-full max-w-3xl p-8">
        <h2 className="text-4xl font-bold mb-8 p-3">Explain Module: </h2>
          <DifficultySelector/>
          <div className="modal-action">
            <form method="dialog">
              <button className="btn btn-lg">Close</button>
            </form>
          </div>
        </div>
      </dialog>
    </div>
  );
};

export default VoiceAssistant4;