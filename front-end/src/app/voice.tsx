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
    <div className="max-w-xs mx-auto p-4 bg-base-100 shadow-lg rounded-xl">
      <div className="text-xl font-bold text-[#343232] mb-2 text-center">
        Having a bad day?
      </div>

      <div className="flex justify-center">
        <button 
          className="btn btn-primary" 
          onClick={() => modalRef.current?.showModal()}
        >
          Talk to Remi 
          <IconContext.Provider value={{ color: "black", className: "global-class-name", size:"1.40em" }}>
            <div>
              <BsChatLeftHeart />
            </div>
          </IconContext.Provider>
        </button>

        {/* Modal */}
        <dialog ref={modalRef} id="my_modal_4" className="modal">
          <div className="modal-box w-11/12 max-w-5xl">
            <h3 className="font-bold text-lg">Hello!</h3>
            <p className="py-4">Click the button below to close</p>
            <div className="modal-action">
              <form method="dialog">
                <button className="btn">Close</button>
              </form>
            </div>
          </div>
        </dialog>
      </div>
    </div>
  );
};

export default VoiceAssistant;
