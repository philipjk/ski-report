import { useState } from "react";
import axios from "axios";

export default function SkialpReport() {
  const [location, setLocation] = useState("");
  const [report, setReport] = useState(null);
  const BACKEND_URL = "https://skialp-backend.fly.dev/report";

  const fetchReport = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}?location=${location}`);
      setReport(response.data);
    } catch (error) {
      console.error("Error fetching report:", error);
    }
  };

  return (
    <div className="flex flex-col items-center p-4">
      <h1 className="text-2xl font-bold">Skialp Report</h1>
      <input
        type="text"
        placeholder="Enter location (e.g., Courmayeur)"
        value={location}
        onChange={(e) => setLocation(e.target.value)}
        className="border p-2 mt-4 rounded"
      />
      <button onClick={fetchReport} className="mt-2 p-2 bg-blue-500 text-white rounded">
        Get Report
      </button>
      {report && (
        <div className="border p-4 mt-4 rounded-lg shadow-md">
          <p><strong>Location:</strong> {report.location}</p>
          <p><strong>Temperature:</strong> {report.temperature}°C</p>
          <p><strong>Snow Depth:</strong> {report.snow_depth} cm</p>
          <p><strong>Avalanche Risk:</strong> {report.avalanche_risk}</p>
          <p><strong>Summary:</strong> {report.summary}</p>
        </div>
      )}
    </div>
  );
}