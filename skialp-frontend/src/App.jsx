import { useState, useEffect } from "react";
import axios from "axios";

export default function SkialpReport() {
  const [report, setReport] = useState(null);
  const BACKEND_URL = "https://skialp-backend.fly.dev/report"; 

  useEffect(() => {
    axios.get(BACKEND_URL)
      .then((res) => setReport(res.data))
      .catch((err) => console.error("Error fetching report:", err));
  }, []);

  return (
    <div className="flex flex-col items-center p-4">
      <h1 className="text-2xl font-bold">Skialp Report</h1>
      {report ? (
        <div className="border p-4 mt-4 rounded-lg shadow-md">
          <p><strong>Location:</strong> {report.location}</p>
          <p><strong>Temperature:</strong> {report.temperature}°C</p>
          <p><strong>Snow Depth:</strong> {report.snow_depth} cm</p>
          <p><strong>Avalanche Risk:</strong> {report.avalanche_risk}</p>
        </div>
      ) : (
        <p>Loading report...</p>
      )}
      <button onClick={() => window.location.reload()} className="mt-4 p-2 bg-blue-500 text-white rounded">
        Refresh
      </button>
    </div>
  );
}
