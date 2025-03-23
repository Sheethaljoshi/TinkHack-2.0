"use client"
import { FaRegCompass } from "react-icons/fa";
import { FaHome } from "react-icons/fa";
import { MdEmojiPeople } from "react-icons/md";
import { FaMapMarkedAlt } from "react-icons/fa";
import { FaHandHoldingHeart } from "react-icons/fa";
import { FaUserDoctor } from "react-icons/fa6";
import { useState } from "react";
import Link from 'next/link';
import Modalchat from "../components/modalchat";
import dynamic from "next/dynamic";
import LineChartComponent from "./linechart";
import MedicineTracker from "./tracker";
import UploadMedicalDocuments from "./upload";
import TalkToRemi from "../components/TalkToRemi";
import { FaRobot } from "react-icons/fa";
import { HiHome, HiDocumentText, HiAcademicCap, HiCollection, HiChatAlt2, HiOutlineChatAlt } from "react-icons/hi";

// Import PieChart dynamically to avoid SSR issues
const PieChartComponent = dynamic(() => import("./piechart"), {
  ssr: false,
  loading: () => <div className="h-64 w-full flex justify-center items-center">Loading Chart...</div>
});

export default function Home() {
  const [showModalchat, setShowModalchat] = useState(false);
  const [showTalkToRemi, setShowTalkToRemi] = useState(false);

  return (
    <div className="drawer lg:drawer-open">
      <input id="my-drawer-2" type="checkbox" className="drawer-toggle" />
      <div className="drawer-content flex flex-col p-8">
        <label htmlFor="my-drawer-2" className="btn btn-ghost drawer-button lg:hidden">
          <HiOutlineChatAlt size={24} />
        </label>
        <div className="mb-6">
          <div className="text-3xl font-bold">Diagnostics</div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Health Summary</h2>
              <PieChartComponent />
            </div>
          </div>

          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Progress</h2>
              <LineChartComponent />
            </div>
          </div>
        </div>

        <div className="mt-6">
          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Medicine Tracker</h2>
              <MedicineTracker />
            </div>
          </div>
        </div>

        <div className="mt-6">
          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">Upload Medical Documents</h2>
              <UploadMedicalDocuments />
            </div>
          </div>
        </div>
        
        <div className="fixed bottom-10 right-10 flex flex-col gap-4">
          <button className="btn btn-circle btn-primary shadow-lg" onClick={() => setShowModalchat(true)}>
            <HiChatAlt2 size={24} />
          </button>
          <button className="btn btn-circle btn-secondary shadow-lg" onClick={() => setShowTalkToRemi(true)}>
            <FaRobot size={24} />
          </button>
        </div>

        <Modalchat isVisible={showModalchat} onClose={() => setShowModalchat(false)} />
        <TalkToRemi isVisible={showTalkToRemi} onClose={() => setShowTalkToRemi(false)} />
      </div>

      <div className="drawer-side">
        <label htmlFor="my-drawer-2" className="drawer-overlay"></label>
        <ul className="menu p-4 w-80 bg-base-200 text-base-content h-full">
          <div className="flex flex-col gap-8 py-4">
            <div className="flex justify-center">
              <div className="avatar">
                <div className="w-24 rounded-full">
                  <img src="/profile.jpg" alt="Profile" />
                </div>
              </div>
            </div>
            <div className="flex flex-col items-center space-y-1">
              <h2 className="text-xl font-bold">John Doe</h2>
              <p className="text-sm opacity-75">Premium User</p>
            </div>
          </div>
          <li className="mb-2"><a className="flex items-center text-lg"><HiHome size={20} /> <span className="ml-2">Home</span></a></li>
          <li className="mb-2"><a className="flex items-center text-lg"><HiAcademicCap size={20} /> <span className="ml-2">History</span></a></li>
          <li className="mb-2"><a className="flex items-center text-lg"><HiAcademicCap size={20} /> <span className="ml-2">Science</span></a></li>
          <li className="mb-2"><a className="flex items-center text-lg"><HiAcademicCap size={20} /> <span className="ml-2">English</span></a></li>
          <li><a className="flex items-center text-lg"><HiDocumentText size={20} /> <span className="ml-2">Diagnostics</span></a></li>
        </ul>
      </div>
      <input id="theme" type="checkbox" className="toggle theme-controller" value="synthwave" />
    </div>
  );
}