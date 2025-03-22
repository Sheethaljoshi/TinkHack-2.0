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

const PieChartComponent = dynamic(() => import("./piechart"), {
  ssr: false,
});

export default function Home() {

  const [showModalchat, setShowModalchat] = useState(false);

    return (
        <div className="drawer lg:drawer-open">
          <input id="my-drawer-2" type="checkbox" className="drawer-toggle" />
          <div className="drawer-content flex-flex-col m-6 bg-base-200 rounded-3xl ">
            <div className="text-3xl mt-5 font-extrabold flex"><div className="pl-6 pr-4"><FaUserDoctor /></div>Diagnostics</div>
            <div className="flex gap-9 w-full m-5 items-start h-72 mt-4">
              <div className="bg-white rounded-2xl shadow-md ml-12">
              <PieChartComponent/>
              </div>
              <div className=" w-[600px]">
              <LineChartComponent />
              </div>
            </div>
            <div className="flex ">
              <div className="mt-24 ml-12">
                <UploadMedicalDocuments/>
              </div>
              <div className="mt-1 ml-4">
               <MedicineTracker/>
              </div>
            </div>
    </div> 
    <div className="drawer-side rounded-t-3xl rounded-b-3xl sm:rounded-t-3xl sm:rounded-b-3xl shadow-2xl dark:shadow-2xl ">
      <label htmlFor="my-drawer-2" aria-label="close sidebar" className="drawer-overlay"></label> 
      <ul className="menu p-4 w-80 min-h-full bg-base-200 text-base-content round">
        <div className="text-3xl font-extrabold m-5 flex">Explore<div className="ml-2 mt-1"><FaRegCompass /></div></div>
        <div className="flex flex-col ">
        <div className='items-center mb-8'>
        <li className='p-2 '><Link href="/" className='text-lg flex justify-center font-bold'><div ><FaHome /></div>Home</Link></li>
        <li className='p-2'><Link href="/people" className='text-lg flex justify-center font-bold'><div><MdEmojiPeople /></div>People</Link></li>
        <li className='p-2'><Link href="/places" className='text-lg flex justify-center font-bold'><div><FaMapMarkedAlt /></div>Places</Link></li>
        <li className='p-2'><Link href="/memories" className='text-lg flex justify-center font-semibold'><div><FaHandHoldingHeart /></div>Memories</Link></li>
        <li className='p-2'><Link href="/personal" className='text-lg flex justify-center font-semibold'><div><FaUserDoctor /></div>Diagnostics</Link></li>
        </div>
        <div className="flex mt-48 justify-between">
        <div className="ml-4"><button onClick={()=>setShowModalchat(true)} className="btn btn-primary" >Assistant</button></div>
        <label className="flex cursor-pointer gap-2 mt-4">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>
          <input type="checkbox" value="dark" className="toggle theme-controller"/>
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
        </label>
        </div>
        </div>
      </ul>
    </div>
    <Modalchat isVisible={showModalchat} onClose ={()=>setShowModalchat(false)}/>
  </div>
    )
}