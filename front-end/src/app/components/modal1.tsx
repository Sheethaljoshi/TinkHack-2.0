import React, { useState, useEffect, ChangeEvent } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";

interface ModalProps {
  isVisible: boolean;
  onClose: () => void;
  name: string;
  description: string;
  relation: string;
  occupation: string;
  person_index: number;
  image_url?: string;
}

const Modal1: React.FC<ModalProps> = ({
  isVisible,
  onClose,
  name,
  description,
  relation,
  occupation,
  person_index,
  image_url,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [newName, setNewName] = useState(name);
  const [newDescription, setNewDescription] = useState(description);
  const [newRelation, setNewRelation] = useState(relation);
  const [newOccupation, setNewOccupation] = useState(occupation);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [descriptionPoints, setDescriptionPoints] = useState<string[]>([]);
  const [checkedItems, setCheckedItems] = useState<boolean[]>([]);

  const router = useRouter();

  useEffect(() => {
    // Split description into bullet points using regex for numbers or bullets
    const points = description.split(/\d+\.\s|\*\*/).filter((point) => point.trim() !== "");
    setDescriptionPoints(points);
    setCheckedItems(new Array(points.length).fill(false));
  }, [description]);

  const handleCheckboxChange = (index: number) => {
    const updatedCheckedItems = [...checkedItems];
    updatedCheckedItems[index] = !updatedCheckedItems[index];
    setCheckedItems(updatedCheckedItems);
  };

  const handleImageUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
    }
  };

  const handleSubmit2 = async () => {
    const formData = new FormData();
    formData.append("email", "sh33thal24@gmail.com");
    formData.append("first_name", "Sheethal");
    formData.append("last_name", "Joshi Thomas");
    formData.append("person_index", person_index.toString());
    formData.append("name", newName);
    formData.append("relation", newRelation);
    formData.append("occupation", newOccupation);
    
    // Only include checked points in the final description
    const filteredDescription = descriptionPoints
      .filter((_, index) => checkedItems[index])
      .join(". ");

    formData.append("description", filteredDescription);

    if (selectedImage) {
      formData.append("image", selectedImage);
    }

    try {
      await axios.post("http://127.0.0.1:8000/delete/person", formData, {
        params: {
          email: 'sh33thal24@gmail.com',
          first_name: 'Sheethal',
          last_name: 'Joshi Thomas',
          person_index: person_index,
        },
      });
      onClose();
      window.location.reload();
    } catch (error) {
      console.error("Error updating person:", error);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-45 backdrop-blur flex justify-center items-center z-50">
      <div className="lg:w-[1000px] w-96 m-auto">
        <div className="bg-base-200 p-7 rounded-3xl flex flex-col overflow-auto max-h-[80vh]">
          <div className="mb-7 mt-2 text-lg flex justify-between">
            <div className="lg:flex">
              <div className="mr-2">
                <div className="avatar flex-col mt-10">
                  <div className="w-60 rounded-xl">
                    <img src={image_url} className="object-cover w-full h-full" />
                  </div>
                  <button className="btn w-64 bg-success mr-6 mt-4" onClick={() => router.push("/learn_audio")}>
                    Start learning
                  </button>
                  <button className="btn w-64 bg-warning mr-6 mt-4" onClick={handleSubmit2}>
                    Delete Module
                  </button>
                </div>
              </div>
              <div className="mt-10">
                <div className="flex mb-4 justify-between">
                  <div className="flex-col lg:flex">
                    <div className="font-extrabold text-3xl">{name}</div>
                    <div className="mt-2 ml-1 mr-12 text-xl">{relation}</div>
                  </div>
                  <div className="text-md mr-8 mt-1">Proficiency: {occupation}</div>
                </div>
                <div className="card bg-base-100 shadow-xl overflow-auto max-h-[80vh] mt-8">
                  <div className="card-body">
                    <div className="mt-2 ml-3">
                      {descriptionPoints.map((point, index) => (
                        <div key={index} className="flex items-center mb-2">
                          <input
                            type="checkbox"
                            className="mr-2"
                            checked={checkedItems[index]}
                            onChange={() => handleCheckboxChange(index)}
                          />
                          <span>{point}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="card-actions justify-end">
              <button className="btn btn-square btn-sm" onClick={onClose}>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Modal1;
