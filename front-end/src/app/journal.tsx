import React from 'react';

const DiaryEntry: React.FC = () => {
  return (
    <div className="container min-w-96">
      <div className="card bg-base-100 shadow-xl">
        <div className="card-body">
          <h2 className="card-title text-md font-bold ml-2 text-[#343232]">Anything to Remember for Later?</h2>
          <div className="form-control w-full max-w-lg mt-1 ">
            <input type="date" className="input input-sm input-bordered min-w-" />
          </div>
          <div className="form-control w-full max-w-lg">
            <textarea className="textarea textarea-md textarea-bordered h-20" placeholder="Write your diary entry here..."></textarea>
          </div>
          <div className="card-actions ml-2 w-full">
            <button className="btn btn-sm btn-secondary w-full mt-2 text-[#343232]">Submit</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiaryEntry;