import React, { useState } from 'react';
import { Upload, User, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

function Dashboard() {
  const [file, setFile] = useState(null);
  const [patient, setPatient] = useState({ name: '', age: '' });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleUpload = async () => {
    if (!file || !patient.name || !patient.age) {
      setError('Please fill all required fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('patient_name', patient.name);
      formData.append('patient_age', patient.age);

      const response = await axios.post('http://127.0.0.1:8000/upload', formData);
      setResult(response.data);
    } catch (err) {
      setError('Upload failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Prescription Reader</h1>
        <p className="text-gray-600">Upload and analyze prescription images</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Patient Info */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center mb-4">
            <User className="w-5 h-5 text-blue-600 mr-2" />
            <h2 className="text-lg font-semibold">Patient Information</h2>
          </div>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Patient Name *"
              value={patient.name}
              onChange={(e) => setPatient({...patient, name: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="number"
              placeholder="Age *"
              value={patient.age}
              onChange={(e) => setPatient({...patient, age: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Upload */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center mb-4">
            <Upload className="w-5 h-5 text-blue-600 mr-2" />
            <h2 className="text-lg font-semibold">Upload Prescription</h2>
          </div>
          <div className="space-y-4">
            <label className={`block border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
              file ? 'border-green-400 bg-green-50' : 'border-gray-300 hover:border-blue-400'
            }`}>
              <input type="file" className="hidden" onChange={(e) => setFile(e.target.files[0])} accept="image/*" />
              {file ? (
                <div className="flex items-center justify-center">
                  <CheckCircle className="w-8 h-8 text-green-500 mb-2" />
                </div>
              ) : (
                <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              )}
              <p className="text-sm text-gray-600">
                {file ? file.name : 'Click to upload prescription'}
              </p>
            </label>
            
            <button
              onClick={handleUpload}
              disabled={loading}
              className={`w-full py-3 rounded-lg font-medium transition-colors ${
                loading ? 'bg-gray-300 text-gray-500' : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {loading ? 'Processing...' : 'Process Prescription'}
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Results</h2>
          
          {result.structured_data?.medications && (
            <div className="space-y-3">
              <h3 className="font-medium text-gray-800">Medications:</h3>
              {result.structured_data.medications.map((med, i) => (
                <div key={i} className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold">{med.name}</h4>
                  <div className="text-sm text-gray-600 mt-1">
                    {med.dosage && <span className="mr-4">Dosage: {med.dosage}</span>}
                    {med.frequency && <span>Frequency: {med.frequency}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {result.interactions?.length > 0 && (
            <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="font-medium text-yellow-800 mb-2">⚠️ Drug Interactions</h3>
              <ul className="text-sm text-yellow-700 space-y-1">
                {result.interactions.map((interaction, i) => (
                  <li key={i}>• {interaction}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Dashboard;