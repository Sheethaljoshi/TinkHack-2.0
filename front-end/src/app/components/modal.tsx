import React, { ChangeEvent, useState } from 'react';
import { RiHeartAdd2Line } from "react-icons/ri";
import { IconContext } from "react-icons";
import axios from 'axios';

interface ModalProps {
  isVisible: boolean;
  onClose: () => void;
}

const Modal: React.FC<ModalProps> = ({ isVisible, onClose }) => {
  const [activeTab, setActiveTab] = useState(1);
  const [personName, setPersonName] = useState('');
  const [therelation, setRelation] = useState('');
  const [theoccupation, setOccupation] = useState('');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  
  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPdfFile(file); 
    }
  };

  const handleSubmit = async () => {
    let url = '';
    const formData = new FormData();
    formData.append('email', 'sh33thal24@gmail.com');
    formData.append('first_name', 'Sheethal');
    formData.append('last_name', 'Joshi Thomas');

    if (activeTab === 1) {
      url = `http://127.0.0.1:8000/insert/person_with_pdf/`;
      formData.append('name', personName);
      formData.append('relation', therelation);
      formData.append('occupation', theoccupation);
      if (pdfFile) {
        formData.append('pdf_file', pdfFile);
      }
    }

    const response = await axios.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    onClose();
    window.location.reload();
  };

  const handleTabChange = (tabIndex: number) => {
    setActiveTab(tabIndex);
  };

  if (!isVisible) return null;

  return (
    <div className='fixed inset-0 bg-black bg-opacity-45 backdrop-blur flex justify-center items-center'>
      <div className='w-[600px]'>
        <div className='bg-base-200 p-7 rounded-3xl flex flex-col'>
          <div className='mb-7 mt-2 text-lg flex'>
            <div className='mr-2'>
              <IconContext.Provider value={{ size: '23' }}>
                <div>
                  <RiHeartAdd2Line />
                </div>
              </IconContext.Provider>
            </div>
            Learn a new module
          </div>
          <div role="tablist" className="tabs tabs-lifted mb-6">
            <input
              type="radio"
              name="my_tabs_2"
              role="tab"
              className="tab"
              aria-label="Physics"
              checked={activeTab === 1}
              onChange={() => handleTabChange(1)}
            />
            <div role="tabpanel" className={`tab-content bg-base-100 border-base-300 rounded-box p-6 ${activeTab === 1 ? '' : 'hidden'}`}>
              <div className="mb-4">
                <label className="input input-bordered flex items-center gap-2">
                  Module
                  <input type="text" className="grow" value={personName} onChange={(e) => setPersonName(e.target.value)} />
                </label>
              </div>
              <div className="mb-4">
                <label className="input input-bordered flex items-center gap-2">
                  Date
                  <input type="date" className="grow" value={therelation} onChange={(e) => setRelation(e.target.value)} />
                </label>
              </div>
              <div className="mb-4">
                <label className="input input-bordered flex items-center gap-2">
                  Current Proficiency
                  <input type="text" className="grow" value={theoccupation} onChange={(e) => setOccupation(e.target.value)} />
                </label>
              </div>
              <div className="mb-4">
                <label className="flex flex-col gap-2">
                  Upload Study Material
                  <input type="file" className="file-input file-input-primary file-input-bordered w-full max-w-xs" accept="application/pdf" onChange={handleFileUpload} />
                </label>
              </div>
            </div>
          </div>
          <div className='flex justify-end'>
            <button className='btn bg-secondary mr-2 dark:text-black' onClick={handleSubmit}>Submit</button>
            <button className='btn bg-primary dark:text-black' onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Modal;
