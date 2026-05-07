import React, { useState, useEffect } from 'react';
import { User, Search, Calendar } from 'lucide-react';
import axios from 'axios';

function HistoryPage() {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [prescriptions, setPrescriptions] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/patients');
      setPatients(response.data);
    } catch (err) {
      console.error('Failed to load patients');
    } finally {
      setLoading(false);
    }
  };

  const fetchPrescriptions = async (patientId) => {
    try {
      const response = await axios.get(`http://127.0.0.1:8000/patients/${patientId}/prescriptions`);
      setPrescriptions(response.data);
    } catch (err) {
      setPrescriptions([]);
    }
  };

  const selectPatient = (patient) => {
    setSelectedPatient(patient);
    fetchPrescriptions(patient.id);
  };

  const filteredPatients = patients.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6 text-center">
        <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p>Loading patients...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Patient History</h1>
        <p className="text-gray-600">View patient prescription records</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Patient List */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Patients ({filteredPatients.length})</h2>
          
          <div className="relative mb-4">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search patients..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredPatients.map((patient) => (
              <div
                key={patient.id}
                onClick={() => selectPatient(patient)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedPatient?.id === patient.id
                    ? 'bg-blue-50 border-blue-300'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center">
                  <User className="w-4 h-4 text-gray-400 mr-2" />
                  <div>
                    <h3 className="font-medium text-gray-800">{patient.name}</h3>
                    <p className="text-sm text-gray-600">Age: {patient.age}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Prescription Details */}
        <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm">
          {selectedPatient ? (
            <>
              <h2 className="text-lg font-semibold mb-4">
                {selectedPatient.name}'s Prescriptions ({prescriptions.length})
              </h2>

              {prescriptions.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <p>No prescriptions found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {prescriptions.map((prescription) => (
                    <div key={prescription.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar className="w-4 h-4 mr-1" />
                          {new Date(prescription.created_at).toLocaleDateString()}
                        </div>
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          ID: {prescription.id}
                        </span>
                      </div>

                      {prescription.structured_json?.medications && (
                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Medications:</h4>
                          <div className="space-y-2">
                            {prescription.structured_json.medications.map((med, i) => (
                              <div key={i} className="bg-gray-50 p-3 rounded">
                                <h5 className="font-medium">{med.name}</h5>
                                <div className="text-sm text-gray-600 mt-1">
                                  {med.dosage && <span className="mr-4">Dosage: {med.dosage}</span>}
                                  {med.frequency && <span>Frequency: {med.frequency}</span>}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {prescription.structured_json?.interactions?.length > 0 && (
                        <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded p-3">
                          <h4 className="font-medium text-yellow-800 mb-1">⚠️ Interactions:</h4>
                          <ul className="text-sm text-yellow-700 space-y-1">
                            {prescription.structured_json.interactions.map((interaction, i) => (
                              <li key={i}>• {interaction}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <User className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Select a patient to view their prescription history</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default HistoryPage;