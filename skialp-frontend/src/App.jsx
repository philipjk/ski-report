import { useState } from "react";
import axios from "axios";

export default function SkialpReport() {
  const [location, setLocation] = useState(null);
  const [report, setReport] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchError, setSearchError] = useState(null);
  
  // Use local backend in development, production backend otherwise
  const BACKEND_URL = import.meta.env.DEV 
    ? "http://localhost:8000"
    : "https://skialp-backend.fly.dev";

  const fetchReport = async (locationData) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/report`, {
        params: {
          location: locationData.name.split(',')[0],
          lat: locationData.lat,
          lon: locationData.lon
        }
      });
      setReport(response.data);
    } catch (error) {
      console.error("Error fetching report:", error);
      setSearchError("Failed to fetch weather report");
    }
  };

  const handleLocationSearch = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${BACKEND_URL}/validate-location`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: searchQuery }),
      });
      
      const data = await response.json();
      if (data.error) {
        setSearchError(data.error);
        return;
      }
      
      setLocation(data.location);
      setSearchError(null);
      fetchReport(data.location);
    } catch (error) {
      setSearchError('Failed to validate location');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-100 to-white flex items-center justify-center p-6">
      <div className="max-w-3xl w-full bg-white rounded-2xl shadow-2xl p-8 flex flex-col items-center text-center">
        <h1 className="text-5xl font-bold text-blue-900 mb-6">Skialp Report</h1>
        <p className="text-lg text-gray-600 mb-6">
          Get snow conditions and weather reports for your ski touring destination
        </p>
        
        <form onSubmit={handleLocationSearch} className="w-full flex flex-col items-center">
          <label htmlFor="location-search" className="text-lg font-medium text-gray-700 mb-2">
            Where do you want to go skiing?
          </label>
          <div className="w-full flex flex-col sm:flex-row gap-3">
            <input
              id="location-search"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter a location (e.g., Chamonix, Courmayeur)"
              className="flex-1 p-3 border rounded-lg text-lg text-center shadow-sm"
              autoFocus
            />
            <button 
              type="submit" 
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium shadow-md"
            >
              Get Report
            </button>
          </div>
        </form>
        
        {searchError && (
          <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg w-full">
            {searchError}
          </div>
        )}
        
        {location && (
          <div className="mt-6 text-lg font-medium text-gray-800">
            Selected location: <span className="text-blue-700">{location.name}</span>
          </div>
        )}

        {report && (
          <div className="mt-8 border-t pt-6 w-full">
            <h2 className="text-2xl font-semibold mb-4">Current Conditions</h2>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="p-6 bg-blue-50 rounded-lg shadow">
                <p className="text-lg"><strong>Temperature:</strong> {report.temperature}°C</p>
                <p className="text-lg"><strong>Snow Depth:</strong> {report.snow_depth} cm</p>
              </div>
              <div className="p-6 bg-blue-50 rounded-lg shadow">
                <p className="text-lg"><strong>Avalanche Risk:</strong> {report.avalanche_risk}</p>
                <p className="text-lg"><strong>Summary:</strong> {report.summary}</p>
              </div>
            </div>
            {report.meteogram && (
              <div className="mt-6 w-full">
                <img 
                  src={report.meteogram} 
                  alt="Weather forecast meteogram" 
                  className="w-full rounded-lg shadow-lg"
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
