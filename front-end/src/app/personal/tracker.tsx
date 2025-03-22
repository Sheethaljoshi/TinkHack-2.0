import { useState, useEffect } from "react";
import axios from "axios";

const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export default function MedicineTracker() {
  const [medicines, setMedicines] = useState<string[]>([]);
  const [schedule, setSchedule] = useState<boolean[][]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/get_medicine_tracker", {
          params: { email: "sh33thal24@gmail.com" },
        });

        setMedicines(response.data.medicines);
        setSchedule(response.data.schedule);
        setLoading(false);
      } catch (err) {
        setError("Failed to fetch medicine tracker data.");
        setLoading(false);
      }
    };

    fetchData();
  }, []);
  
  const toggleTaken = async (medIndex: number, dayIndex: number) => {
    const medicine = medicines[medIndex];
  
    // Get the current day of the week (0 = Sunday, 6 = Saturday)
    const currentDayIndex = new Date().getDay();
  
    // Calculate the correct date for each day in the tracker (align with UI)
    const today = new Date();
    today.setDate(today.getDate() - (currentDayIndex - dayIndex)); // Adjust correctly
    const formattedDate = today.toISOString().split("T")[0]; // Format YYYY-MM-DD
  
    try {
      const response = await axios.post("http://127.0.0.1:8000/toggle_medicine_status", 
        { email: "sh33thal24@gmail.com", medicine, date: formattedDate }, 
        { headers: { "Content-Type": "application/json" } }
      );
  
      if (response.status === 200) {
        // Toggle the value in UI after a successful update
        const updatedSchedule = schedule.map((med, i) =>
          i === medIndex ? med.map((taken, j) => (j === dayIndex ? !taken : taken)) : med
        );
        setSchedule(updatedSchedule);
      }
    } catch (error) {
      console.error("Failed to update medicine status:", error);
    }
  };
  

  if (loading) return <p className="text-center">Loading...</p>;
  if (error) return <p className="text-center text-red-500">{error}</p>;

  return (
    <div className="max-w-2xl mx-auto p-3 bg-white rounded-lg shadow-md mt-1">
      <h2 className="text-lg font-bold mb-2 text-black">Medicine Tracker</h2>
      <div className="overflow-auto max-h-[calc(3*56px)] border rounded-lg">
        <table className="w-full border-collapse shadow-md">
          <thead>
            <tr className="bg-green-600 text-white">
              <th className="border border-gray-300 px-4 py-2 text-sm">Medicine</th>
              {days.map((day) => (
                <th key={day} className="border border-gray-300 px-2 py-2 text-xs bg-green-600">{day}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {medicines.map((medicine, medIndex) => (
              <tr key={medicine} className={medIndex % 2 === 0 ? "bg-gray-100" : "bg-gray-50"}>
                <td className="border border-gray-300 px-4 py-2 font-medium text-gray-800 text-sm">{medicine}</td>
                {days.map((_, dayIndex) => (
                  <td key={dayIndex} className="border border-gray-300 px-4 py-2 text-center bg-white">
                    <input
                      type="checkbox"
                      checked={schedule[medIndex]?.[dayIndex] || false}
                      onChange={() => toggleTaken(medIndex, dayIndex)}
                      className="w-4 h-4 cursor-pointer checkbox checkbox-warning"
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
