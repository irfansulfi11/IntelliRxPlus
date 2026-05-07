import React, { useState } from 'react';
import { Search as SearchIcon, Plus, X, AlertTriangle, CheckCircle } from 'lucide-react';
import axios from 'axios';

function Search() {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [drugList, setDrugList] = useState([]);
  const [interactions, setInteractions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await axios.get(`http://127.0.0.1:8000/search/drugs?query=${encodeURIComponent(searchTerm)}`);
      setResults(response.data);
    } catch (err) {
      setError('Search failed. Please try again.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const addDrug = (drug) => {
    if (!drugList.find(d => d.name === drug.name)) {
      setDrugList([...drugList, drug]);
    }
  };

  const removeDrug = (drugName) => {
    setDrugList(drugList.filter(d => d.name !== drugName));
    if (drugList.length <= 2) setInteractions(null);
  };

  const checkInteractions = async () => {
    if (drugList.length < 2) {
      setError('Add at least 2 drugs to check interactions');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post('http://127.0.0.1:8000/interactions/check', {
        drugs: drugList.map(d => d.name)
      });
      setInteractions(response.data);
    } catch (err) {
      setError('Failed to check interactions');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Drug Search</h1>
        <p className="text-gray-600">Search drugs and check interactions</p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="flex space-x-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search for drugs (e.g., Aspirin, Ibuprofen)"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              loading ? 'bg-gray-300 text-gray-500' : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Search Results */}
        <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Search Results</h2>
          
          {results.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <SearchIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Enter a drug name to search</p>
            </div>
          ) : (
            <div className="space-y-4">
              {results.map((drug, i) => (
                <div key={i} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-800">{drug.name}</h3>
                      {drug.description && (
                        <p className="text-gray-600 text-sm mt-1">{drug.description}</p>
                      )}
                      {drug.drug_class && (
                        <p className="text-sm text-gray-500 mt-1">Class: {drug.drug_class}</p>
                      )}
                    </div>
                    <button
                      onClick={() => addDrug(drug)}
                      className="ml-4 p-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Interaction Checker */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Interaction Checker</h2>
          
          <div className="space-y-2 mb-4">
            {drugList.length === 0 ? (
              <p className="text-gray-500 text-sm">Add drugs to check interactions</p>
            ) : (
              drugList.map((drug, i) => (
                <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm font-medium">{drug.name}</span>
                  <button
                    onClick={() => removeDrug(drug.name)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>

          {drugList.length >= 2 && (
            <button
              onClick={checkInteractions}
              disabled={loading}
              className={`w-full py-2 rounded-lg font-medium transition-colors ${
                loading ? 'bg-gray-300 text-gray-500' : 'bg-orange-600 text-white hover:bg-orange-700'
              }`}
            >
              {loading ? 'Checking...' : 'Check Interactions'}
            </button>
          )}

          {/* Interaction Results */}
          {interactions && (
            <div className="mt-4 p-4 border rounded-lg">
              <h3 className="font-semibold mb-3">Results</h3>
              
              {interactions.interactions?.length > 0 ? (
                <div className="space-y-2">
                  {interactions.interactions.map((interaction, i) => (
                    <div key={i} className={`p-3 rounded ${
                      interaction.severity === 'high' ? 'bg-red-50 border border-red-200' :
                      interaction.severity === 'moderate' ? 'bg-yellow-50 border border-yellow-200' :
                      'bg-blue-50 border border-blue-200'
                    }`}>
                      <div className="flex items-start">
                        <AlertTriangle className={`w-4 h-4 mr-2 mt-0.5 ${
                          interaction.severity === 'high' ? 'text-red-500' :
                          interaction.severity === 'moderate' ? 'text-yellow-500' :
                          'text-blue-500'
                        }`} />
                        <div>
                          <p className="text-sm font-medium">
                            {interaction.drug1} ↔ {interaction.drug2}
                          </p>
                          <p className="text-xs text-gray-600 mt-1">{interaction.description}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center text-green-700">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  <span className="text-sm">No significant interactions found</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
        <p className="text-sm text-blue-700">
          This tool provides general information and should not replace professional medical advice.
        </p>
      </div>
    </div>
  );
}

export default Search;