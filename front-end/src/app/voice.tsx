"use client";
import { useState, useEffect, useRef } from "react";
import { BsChatLeftHeart } from "react-icons/bs";
import { IconContext } from "react-icons";

const VoiceAssistant: React.FC = () => {
  const [isMounted, setIsMounted] = useState(false);
  const modalRef = useRef<HTMLDialogElement | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null; // Avoid hydration errors

  return (
    <div className="max-w-3xl  mx-auto p-14 bg-base-100 shadow-xl rounded-full">
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
          <h3 className="font-bold text-2xl">Hello!</h3>
          <p className="py-6 text-lg">Click the button below to close</p>
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

export default VoiceAssistant;