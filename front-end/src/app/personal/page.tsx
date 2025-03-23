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
      <div className="drawer-content flex flex-col p-8 bg-gradient-to-br from-base-200/50 to-base-300/30 min-h-screen">
        <label htmlFor="my-drawer-2" className="btn btn-ghost drawer-button lg:hidden">
          <HiOutlineChatAlt size={24} />
        </label>
        <div className="mb-6">
          <div className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">Diagnostics</div>
          <div className="h-1 w-24 bg-gradient-to-r from-primary to-secondary rounded-full mt-1"></div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card bg-base-100 shadow-xl hover:shadow-2xl transition-all duration-300 border border-base-300/50">
            <div className="card-body">
              <h2 className="card-title text-primary">Health Summary</h2>
              <PieChartComponent />
            </div>
          </div>

          <div className="card bg-base-100 shadow-xl hover:shadow-2xl transition-all duration-300 border border-base-300/50">
            <div className="card-body">
              <h2 className="card-title text-primary">Progress</h2>
              <LineChartComponent />
            </div>
          </div>
        </div>

       
        
        
        <div className="fixed bottom-10 right-10 flex flex-col gap-4">
          <button className="btn btn-circle btn-primary shadow-lg hover:shadow-primary/50 transition-all duration-300" onClick={() => setShowModalchat(true)}>
            <HiChatAlt2 size={24} />
          </button>
          <button className="btn btn-circle btn-secondary shadow-lg hover:shadow-secondary/50 transition-all duration-300" onClick={() => setShowTalkToRemi(true)}>
            <FaRobot size={24} />
          </button>
        </div>

        <Modalchat isVisible={showModalchat} onClose={() => setShowModalchat(false)} />
        <TalkToRemi isVisible={showTalkToRemi} onClose={() => setShowTalkToRemi(false)} />
      </div>

      <div className="drawer-side">
        <label htmlFor="my-drawer-2" className="drawer-overlay"></label>
        <ul className="menu p-0 w-80 h-full bg-gradient-to-b from-base-300 to-base-200 text-base-content">
          <div className="flex flex-col gap-8 pt-8 pb-6 px-4 bg-gradient-to-b from-primary/10 to-base-300 shadow-md">
            <div className="flex justify-center">
              <div className="avatar">
                
              </div>
            </div>
            <div className="flex flex-col items-center space-y-1">
              <h2 className="text-xl font-bold">Sheethal Joshy Thomas</h2>
              <p className="text-sm opacity-75">Premium User</p>
              <div className="badge badge-primary mt-1">Pro</div>
            </div>
          </div>
          
          <div className="px-3 py-4">
            <li className="mb-2">
              <a href="/" className="flex items-center text-lg rounded-lg hover:bg-primary/10 transition-all duration-200">
                <HiHome size={20} className="text-primary" /> 
                <span className="ml-2">Home</span>
              </a>
            </li>
            <li className="mb-2">
              <a href="/people" className="flex items-center text-lg rounded-lg hover:bg-primary/10 transition-all duration-200">
                <HiAcademicCap size={20} className="text-primary" /> 
                <span className="ml-2">History</span>
              </a>
            </li>
            <li className="mb-2">
              <a href="#" className="flex items-center text-lg rounded-lg hover:bg-primary/10 transition-all duration-200">
                <HiAcademicCap size={20}/> 
                <span className="ml-2">Science</span>
              </a>
            </li>
            <li  className="mb-2">
              <a href="" className="flex items-center text-lg rounded-lg hover:bg-primary/10 transition-all duration-200">
                <HiAcademicCap size={20} className="text-primary" /> 
                <span className="ml-2">English</span>
              </a>
            </li>
            <li>
              <a className="flex items-center text-lg bg-primary/20 font-medium rounded-lg hover:bg-primary/30 transition-all duration-200">
                <HiDocumentText size={20} className="text-primary" /> 
                <span className="ml-2">Diagnostics</span>
              </a>
            </li>
          </div>
          
          <div className="mt-auto mx-4 mb-6">
            <div className="flex items-center justify-between p-4 bg-base-100 rounded-lg shadow-inner">
              <span className="font-medium">Theme</span>
              <input id="theme" type="checkbox" className="toggle toggle-primary" value="synthwave" />
            </div>
          </div>
        </ul>
      </div>
    </div>
  );
}