import React, { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const LineChartComponent = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchWellnessData = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/total_wellness"); // Backend URL
        setData(response.data); // Set state with API data
      } catch (error) {
        console.error("Error fetching wellness data:", error);
      }
    };

    fetchWellnessData();
  }, []);

  return (
    <div className="w-full h-[300px] p-4 bg-white shadow-lg rounded-lg flex flex-col">
      <h2 className="text-lg font-bold mb-2">Sheethal&apos;s Wellness Score this Week</h2>
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} padding={{ left: 5, right: 5 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default LineChartComponent;
