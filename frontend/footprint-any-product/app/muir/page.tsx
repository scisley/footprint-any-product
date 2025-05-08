'use client';

import React, { useState } from 'react';
import Link from 'next/link';

// Import types from central location
import { MuirApiResponse, MaterialComponent, NewRunData, MuirApiRequestType } from '../types';

const MuirApiPage = () => {
  const [apiResponse, setApiResponse] = useState<MuirApiResponse>({
    data: null,
    isLoading: false
  });
  const [runId, setRunId] = useState<string>('');
  const [procurementId, setProcurementId] = useState<string>('');
  const [page, setPage] = useState<number>(0);
  const [perPage, setPerPage] = useState<number>(10);
  
  // State for creating new runs
  const [newRunData, setNewRunData] = useState<NewRunData>({
    product_name: "Sample Product",
    product_description: "A test product for API submission",
    mass_kg: 2.5,
    source_location: "Germany",
    destination_location: "France",
    upstream_sourcing_countries: ["China", "India"],
    material_breakdown: {
      product: "Sample Product",
      productMass: 2.5,
      massUnit: "kg",
      components: [
        {
          component: "Steel",
          mass: 2.0,
          recycledContent: 0.3
        },
        {
          component: "Plastic Packaging",
          mass: 0.5,
          recycledContent: 0.05
        }
      ]
    },
    supplier_scope_1_and_2_ef: 0.15
  });
  const [showAdvancedForm, setShowAdvancedForm] = useState<boolean>(false);
  const [tempCountry, setTempCountry] = useState<string>('');
  
  // Function to add a new country to the upstream_sourcing_countries array
  const addUpstreamCountry = (event: React.MouseEvent) => {
    event.preventDefault();
    if (tempCountry.trim()) {
      setNewRunData({
        ...newRunData,
        upstream_sourcing_countries: [...newRunData.upstream_sourcing_countries, tempCountry.trim()]
      });
      setTempCountry('');
    }
  };
  
  // Function to remove a country from the upstream_sourcing_countries array
  const removeUpstreamCountry = (index: number) => {
    const updatedCountries = [...newRunData.upstream_sourcing_countries];
    updatedCountries.splice(index, 1);
    setNewRunData({
      ...newRunData,
      upstream_sourcing_countries: updatedCountries
    });
  };
  
  // Function to add a new component to the material_breakdown.components array
  const addComponent = () => {
    setNewRunData({
      ...newRunData,
      material_breakdown: {
        ...newRunData.material_breakdown,
        components: [
          ...newRunData.material_breakdown.components,
          {
            component: "New Component",
            mass: 1.0,
            recycledContent: 0.0
          }
        ]
      }
    });
  };
  
  // Function to remove a component from the material_breakdown.components array
  const removeComponent = (index: number) => {
    const updatedComponents = [...newRunData.material_breakdown.components];
    updatedComponents.splice(index, 1);
    setNewRunData({
      ...newRunData,
      material_breakdown: {
        ...newRunData.material_breakdown,
        components: updatedComponents
      }
    });
  };
  
  // Function to update a component's properties
  const updateComponent = (index: number, field: keyof MaterialComponent, value: string | number) => {
    const updatedComponents = [...newRunData.material_breakdown.components];
    updatedComponents[index] = {
      ...updatedComponents[index],
      [field]: typeof value === 'string' && field !== 'component' ? parseFloat(value) : value
    };
    
    setNewRunData({
      ...newRunData,
      material_breakdown: {
        ...newRunData.material_breakdown,
        components: updatedComponents
      }
    });
  };

  // Function to fetch data from the API
  const fetchData = async (type: MuirApiRequestType, id?: string) => {
    setApiResponse({ data: null, isLoading: true });
    
    try {
      const baseUrl = "https://service-run-api.muir.ai";
      const apiKey = process.env.NEXT_PUBLIC_MUIR_API_KEY || '';
      
      console.log('API Key available:', !!apiKey);
      
      if (!apiKey) {
        throw new Error('MUIR_API_KEY is not set in environment variables');
      }
      
      let endpoint = '';
      let params: Record<string, string> = {};
      
      switch (type) {
        case 'info':
          endpoint = "/carbon_origin/info";
          break;
        case 'runs':
          endpoint = "/carbon_origin/runs";
          params = { page: page.toString(), per_page: perPage.toString() };
          break;
        case 'run-by-id':
          if (!id) {
            throw new Error('Run ID is required');
          }
          endpoint = `/carbon_origin/runs/${id}`;
          break;
        case 'procurement-ids':
          endpoint = "/carbon_origin/procurements/ids";
          params = { page: page.toString(), per_page: perPage.toString() };
          break;
        case 'procurement':
          if (!id) {
            throw new Error('Procurement ID is required');
          }
          endpoint = `/carbon_origin/procurements/${id}`;
          break;
        case 'create-run':
          endpoint = "/carbon_origin/runs";
          break;
      }
      
      const url = new URL(endpoint, baseUrl);
      
      // Add query parameters if any
      Object.keys(params).forEach(key => {
        url.searchParams.append(key, params[key]);
      });
      
      console.log(`Fetching from: ${url.toString()}`);
      
      // Set the method based on the type of request
      const method = type === 'create-run' ? 'POST' : 'GET';
      
      // Set up the request options
      const requestOptions: RequestInit = {
        method,
        headers: {
          'APIKey': apiKey,
          'Accept': '*/*',
        }
      };
      
      // Add the request body for POST requests
      if (method === 'POST') {
        requestOptions.headers = {
          ...requestOptions.headers,
          'Content-Type': 'application/json'
        };
        
        // For create-run, send an array with the new run data
        requestOptions.body = JSON.stringify([newRunData]);
      }
      
      const response = await fetch(url.toString(), requestOptions);
      
      if (!response.ok) {
        let errorMessage = `Error: ${response.status} ${response.statusText}`;
        
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || errorMessage;
        } catch {
          // If we can't parse the error as JSON, just use the status code message
        }
        
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      
      setApiResponse({
        data,
        isLoading: false
      });
      
    } catch (error) {
      console.error('API Error:', error);
      setApiResponse({
        data: null,
        error: error instanceof Error ? error.message : 'An unknown error occurred',
        isLoading: false
      });
    }
  };


  return (
    <div 
      className="min-h-screen p-6 pb-10"
      style={{ background: "var(--background)" }}
    >
      <header className="relative z-10 max-w-5xl mx-auto py-6 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 
              className="text-2xl md:text-3xl font-bold" 
              style={{ color: 'var(--primary)' }}
            >
              Muir API Explorer
            </h1>
            <p className="mt-1" style={{ color: 'var(--foreground)' }}>
              View data from the Muir Carbon Origin API
            </p>
          </div>
          <Link
            href="/"
            className="eco-button px-3 py-1.5 rounded inline-flex items-center text-sm"
            style={{ 
              backgroundColor: 'var(--button-hover)',
              border: '1px solid var(--card-border)',
              color: 'var(--foreground)'
            }}
          >
            Back to Home
          </Link>
        </div>
      </header>
      
      <div className="max-w-5xl mx-auto relative z-10">
        <div 
          className="p-6 rounded-xl shadow-md mb-8"
          style={{ 
            backgroundColor: 'var(--card-background)',
            border: '1px solid var(--card-border)',
          }}
        >
          <h2 
            className="text-xl font-bold mb-4"
            style={{ color: 'var(--foreground)' }}
          >
            API Endpoints
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Organization Info */}
            <div 
              className="p-4 rounded-lg transition-all hover:shadow-md cursor-pointer"
              style={{ 
                backgroundColor: 'var(--background)', 
                border: '1px solid var(--card-border)' 
              }}
              onClick={() => fetchData('info')}
            >
              <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--primary)' }}>
                Organization Info
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--foreground)' }}>
                Get information about your organization and API access
              </p>
              <button
                className="eco-button px-4 py-2 rounded-lg text-white w-full"
                style={{ backgroundColor: 'var(--primary)' }}
                onClick={(e) => {
                  e.stopPropagation();
                  fetchData('info');
                }}
              >
                Fetch Info
              </button>
            </div>
            
            {/* All Runs */}
            <div 
              className="p-4 rounded-lg transition-all hover:shadow-md cursor-pointer"
              style={{ 
                backgroundColor: 'var(--background)', 
                border: '1px solid var(--card-border)' 
              }}
              onClick={() => fetchData('runs')}
            >
              <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--primary)' }}>
                All Carbon Runs
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--foreground)' }}>
                Get a list of all carbon origin runs
              </p>
              <div className="flex gap-2 mb-4">
                <div>
                  <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                    Page
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={page}
                    onChange={(e) => setPage(parseInt(e.target.value) || 0)}
                    className="w-full p-2 rounded-lg"
                    style={{ 
                      backgroundColor: 'var(--card-background)', 
                      border: '1px solid var(--card-border)',
                      color: 'var(--foreground)'
                    }}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                <div>
                  <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                    Per Page
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={perPage}
                    onChange={(e) => setPerPage(parseInt(e.target.value) || 10)}
                    className="w-full p-2 rounded-lg"
                    style={{ 
                      backgroundColor: 'var(--card-background)', 
                      border: '1px solid var(--card-border)',
                      color: 'var(--foreground)'
                    }}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
              </div>
              <button
                className="eco-button px-4 py-2 rounded-lg text-white w-full"
                style={{ backgroundColor: 'var(--primary)' }}
                onClick={(event) => {
                  event.stopPropagation();
                  fetchData('runs');
                }}
              >
                Fetch Runs
              </button>
            </div>
            
            {/* Run by ID */}
            <div 
              className="p-4 rounded-lg transition-all hover:shadow-md cursor-pointer"
              style={{ 
                backgroundColor: 'var(--background)', 
                border: '1px solid var(--card-border)' 
              }}
              onClick={() => runId && fetchData('run-by-id', runId)}
            >
              <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--primary)' }}>
                Run by ID
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--foreground)' }}>
                Get details of a specific carbon run
              </p>
              <div className="mb-4">
                <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                  Run ID
                </label>
                <input
                  type="text"
                  value={runId}
                  onChange={(e) => setRunId(e.target.value)}
                  placeholder="Enter run ID"
                  className="w-full p-2 rounded-lg mb-2"
                  style={{ 
                    backgroundColor: 'var(--card-background)', 
                    border: '1px solid var(--card-border)',
                    color: 'var(--foreground)'
                  }}
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="text-xs" style={{ color: 'var(--score-neutral)' }}>
                  Try with example IDs: <button 
                    className="underline"
                    onClick={(e) => {
                      e.stopPropagation();
                      setRunId('run-001');
                    }}
                  >run-001</button> or <button 
                    className="underline"
                    onClick={(e) => {
                      e.stopPropagation();
                      setRunId('run-002');
                    }}
                  >run-002</button>
                </div>
              </div>
              <button
                className="eco-button px-4 py-2 rounded-lg text-white w-full"
                style={{ 
                  backgroundColor: runId ? 'var(--primary)' : 'var(--score-neutral)' 
                }}
                disabled={!runId}
                onClick={(event) => {
                  event.stopPropagation();
                  if (runId) fetchData('run-by-id', runId);
                }}
              >
                Fetch Run Details
              </button>
            </div>
            
            {/* Procurement IDs */}
            <div 
              className="p-4 rounded-lg transition-all hover:shadow-md cursor-pointer"
              style={{ 
                backgroundColor: 'var(--background)', 
                border: '1px solid var(--card-border)' 
              }}
              onClick={() => fetchData('procurement-ids')}
            >
              <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--primary)' }}>
                Procurement IDs
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--foreground)' }}>
                Get a list of all procurement IDs
              </p>
              <button
                className="eco-button px-4 py-2 rounded-lg text-white w-full"
                style={{ backgroundColor: 'var(--primary)' }}
                onClick={(e) => {
                  e.stopPropagation();
                  fetchData('procurement-ids');
                }}
              >
                Fetch Procurement IDs
              </button>
            </div>
            
            {/* Procurement by ID */}
            <div 
              className="p-4 rounded-lg transition-all hover:shadow-md cursor-pointer md:col-span-2"
              style={{ 
                backgroundColor: 'var(--background)', 
                border: '1px solid var(--card-border)' 
              }}
              onClick={() => procurementId && fetchData('procurement', procurementId)}
            >
              <h3 className="font-bold text-lg mb-2" style={{ color: 'var(--primary)' }}>
                Procurement by ID
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--foreground)' }}>
                Get details of a specific procurement
              </p>
              <div className="mb-4">
                <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                  Procurement ID
                </label>
                <input
                  type="text"
                  value={procurementId}
                  onChange={(e) => setProcurementId(e.target.value)}
                  placeholder="Enter procurement ID"
                  className="w-full p-2 rounded-lg mb-2"
                  style={{ 
                    backgroundColor: 'var(--card-background)', 
                    border: '1px solid var(--card-border)',
                    color: 'var(--foreground)'
                  }}
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="text-xs" style={{ color: 'var(--score-neutral)' }}>
                  Try with example IDs: <button 
                    className="underline"
                    onClick={(e) => {
                      e.stopPropagation();
                      setProcurementId('proc-001');
                    }}
                  >proc-001</button> or <button 
                    className="underline"
                    onClick={(e) => {
                      e.stopPropagation();
                      setProcurementId('proc-002');
                    }}
                  >proc-002</button>
                </div>
              </div>
              <button
                className="eco-button px-4 py-2 rounded-lg text-white w-full"
                style={{ 
                  backgroundColor: procurementId ? 'var(--primary)' : 'var(--score-neutral)' 
                }}
                disabled={!procurementId}
                onClick={(e) => {
                  e.stopPropagation();
                  if (procurementId) fetchData('procurement', procurementId);
                }}
              >
                Fetch Procurement Details
              </button>
            </div>
            
            {/* Create New Run */}
            <div 
              className="p-4 rounded-lg transition-all hover:shadow-md md:col-span-2"
              style={{ 
                backgroundColor: 'var(--background)', 
                border: '1px solid var(--card-border)' 
              }}
            >
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-bold text-lg" style={{ color: 'var(--primary)' }}>
                  Create New Run
                </h3>
                <button
                  className="text-xs px-2 py-1 rounded"
                  style={{
                    backgroundColor: 'var(--card-background)',
                    border: '1px solid var(--card-border)',
                    color: 'var(--foreground)'
                  }}
                  onClick={() => setShowAdvancedForm(!showAdvancedForm)}
                >
                  {showAdvancedForm ? 'Show Simple Form' : 'Show Advanced Form'}
                </button>
              </div>
              <p className="text-sm mb-4" style={{ color: 'var(--foreground)' }}>
                Create a new carbon origin run analysis
              </p>
              
              {/* Simple Form */}
              {!showAdvancedForm && (
                <div className="space-y-4">
                  <div>
                    <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                      Product Name
                    </label>
                    <input
                      type="text"
                      value={newRunData.product_name}
                      onChange={(e) => setNewRunData({...newRunData, product_name: e.target.value})}
                      className="w-full p-2 rounded-lg"
                      style={{ 
                        backgroundColor: 'var(--card-background)', 
                        border: '1px solid var(--card-border)',
                        color: 'var(--foreground)'
                      }}
                    />
                  </div>
                  
                  <div>
                    <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                      Product Description
                    </label>
                    <textarea
                      value={newRunData.product_description}
                      onChange={(e) => setNewRunData({...newRunData, product_description: e.target.value})}
                      className="w-full p-2 rounded-lg"
                      style={{ 
                        backgroundColor: 'var(--card-background)', 
                        border: '1px solid var(--card-border)',
                        color: 'var(--foreground)'
                      }}
                      rows={2}
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                        Mass (kg)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={newRunData.mass_kg}
                        onChange={(e) => setNewRunData({...newRunData, mass_kg: parseFloat(e.target.value) || 0})}
                        className="w-full p-2 rounded-lg"
                        style={{ 
                          backgroundColor: 'var(--card-background)', 
                          border: '1px solid var(--card-border)',
                          color: 'var(--foreground)'
                        }}
                      />
                    </div>
                    
                    <div>
                      <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                        Supplier Scope 1 & 2 Emissions Factor
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={newRunData.supplier_scope_1_and_2_ef}
                        onChange={(e) => setNewRunData({...newRunData, supplier_scope_1_and_2_ef: parseFloat(e.target.value) || 0})}
                        className="w-full p-2 rounded-lg"
                        style={{ 
                          backgroundColor: 'var(--card-background)', 
                          border: '1px solid var(--card-border)',
                          color: 'var(--foreground)'
                        }}
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                        Source Location
                      </label>
                      <input
                        type="text"
                        value={newRunData.source_location}
                        onChange={(e) => setNewRunData({...newRunData, source_location: e.target.value})}
                        className="w-full p-2 rounded-lg"
                        style={{ 
                          backgroundColor: 'var(--card-background)', 
                          border: '1px solid var(--card-border)',
                          color: 'var(--foreground)'
                        }}
                      />
                    </div>
                    
                    <div>
                      <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                        Destination Location
                      </label>
                      <input
                        type="text"
                        value={newRunData.destination_location}
                        onChange={(e) => setNewRunData({...newRunData, destination_location: e.target.value})}
                        className="w-full p-2 rounded-lg"
                        style={{ 
                          backgroundColor: 'var(--card-background)', 
                          border: '1px solid var(--card-border)',
                          color: 'var(--foreground)'
                        }}
                      />
                    </div>
                  </div>
                </div>
              )}
              
              {/* Advanced Form */}
              {showAdvancedForm && (
                <div className="space-y-6 mt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                        Product Name
                      </label>
                      <input
                        type="text"
                        value={newRunData.product_name}
                        onChange={(e) => setNewRunData({...newRunData, product_name: e.target.value})}
                        className="w-full p-2 rounded-lg"
                        style={{ 
                          backgroundColor: 'var(--card-background)', 
                          border: '1px solid var(--card-border)',
                          color: 'var(--foreground)'
                        }}
                      />
                    </div>
                    
                    <div>
                      <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                        Mass (kg)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={newRunData.mass_kg}
                        onChange={(e) => {
                          const newMass = parseFloat(e.target.value) || 0;
                          setNewRunData({
                            ...newRunData, 
                            mass_kg: newMass,
                            material_breakdown: {
                              ...newRunData.material_breakdown,
                              productMass: newMass
                            }
                          });
                        }}
                        className="w-full p-2 rounded-lg"
                        style={{ 
                          backgroundColor: 'var(--card-background)', 
                          border: '1px solid var(--card-border)',
                          color: 'var(--foreground)'
                        }}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                      Product Description
                    </label>
                    <textarea
                      value={newRunData.product_description}
                      onChange={(e) => setNewRunData({...newRunData, product_description: e.target.value})}
                      className="w-full p-2 rounded-lg"
                      style={{ 
                        backgroundColor: 'var(--card-background)', 
                        border: '1px solid var(--card-border)',
                        color: 'var(--foreground)'
                      }}
                      rows={2}
                    />
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                        Source Location
                      </label>
                      <input
                        type="text"
                        value={newRunData.source_location}
                        onChange={(e) => setNewRunData({...newRunData, source_location: e.target.value})}
                        className="w-full p-2 rounded-lg"
                        style={{ 
                          backgroundColor: 'var(--card-background)', 
                          border: '1px solid var(--card-border)',
                          color: 'var(--foreground)'
                        }}
                      />
                    </div>
                    
                    <div>
                      <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                        Destination Location
                      </label>
                      <input
                        type="text"
                        value={newRunData.destination_location}
                        onChange={(e) => setNewRunData({...newRunData, destination_location: e.target.value})}
                        className="w-full p-2 rounded-lg"
                        style={{ 
                          backgroundColor: 'var(--card-background)', 
                          border: '1px solid var(--card-border)',
                          color: 'var(--foreground)'
                        }}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                      Upstream Sourcing Countries
                    </label>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {newRunData.upstream_sourcing_countries.map((country, index) => (
                        <div 
                          key={index}
                          className="px-2 py-1 rounded-full text-xs flex items-center"
                          style={{ 
                            backgroundColor: 'var(--primary-light)',
                            color: 'var(--primary-dark)'
                          }}
                        >
                          {country}
                          <button 
                            className="ml-1 w-4 h-4 rounded-full flex items-center justify-center"
                            style={{
                              backgroundColor: 'var(--primary-dark)',
                              color: 'white'
                            }}
                            onClick={() => removeUpstreamCountry(index)}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                    <div className="flex">
                      <input
                        type="text"
                        value={tempCountry}
                        onChange={(e) => setTempCountry(e.target.value)}
                        placeholder="Add a country"
                        className="flex-grow p-2 rounded-l-lg"
                        style={{ 
                          backgroundColor: 'var(--card-background)', 
                          border: '1px solid var(--card-border)',
                          color: 'var(--foreground)'
                        }}
                      />
                      <button
                        className="px-3 py-2 rounded-r-lg"
                        style={{
                          backgroundColor: 'var(--primary)',
                          color: 'white'
                        }}
                        onClick={addUpstreamCountry}
                      >
                        Add
                      </button>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-xs block mb-1" style={{ color: 'var(--foreground)' }}>
                      Supplier Scope 1 & 2 Emissions Factor
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={newRunData.supplier_scope_1_and_2_ef}
                      onChange={(e) => setNewRunData({...newRunData, supplier_scope_1_and_2_ef: parseFloat(e.target.value) || 0})}
                      className="w-full p-2 rounded-lg"
                      style={{ 
                        backgroundColor: 'var(--card-background)', 
                        border: '1px solid var(--card-border)',
                        color: 'var(--foreground)'
                      }}
                    />
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-xs font-semibold" style={{ color: 'var(--foreground)' }}>
                        Material Breakdown Components
                      </label>
                      <button
                        className="text-xs px-2 py-1 rounded"
                        style={{
                          backgroundColor: 'var(--primary)',
                          color: 'white'
                        }}
                        onClick={addComponent}
                      >
                        Add Component
                      </button>
                    </div>
                    
                    {newRunData.material_breakdown.components.map((component, index) => (
                      <div 
                        key={index}
                        className="p-3 mb-3 rounded-lg"
                        style={{
                          backgroundColor: 'var(--card-background)',
                          border: '1px solid var(--card-border)'
                        }}
                      >
                        <div className="flex justify-between mb-2">
                          <span className="font-medium" style={{ color: 'var(--foreground)' }}>
                            Component {index + 1}
                          </span>
                          <button
                            className="text-xs px-2 py-0.5 rounded"
                            style={{
                              backgroundColor: 'var(--status-error)',
                              color: 'white'
                            }}
                            onClick={() => removeComponent(index)}
                          >
                            Remove
                          </button>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                          <div>
                            <label className="text-xs block mb-1" style={{ color: 'var(--score-neutral)' }}>
                              Name
                            </label>
                            <input
                              type="text"
                              value={component.component}
                              onChange={(e) => updateComponent(index, 'component', e.target.value)}
                              className="w-full p-2 rounded-lg text-sm"
                              style={{ 
                                backgroundColor: 'var(--background)', 
                                border: '1px solid var(--card-border)',
                                color: 'var(--foreground)'
                              }}
                            />
                          </div>
                          
                          <div>
                            <label className="text-xs block mb-1" style={{ color: 'var(--score-neutral)' }}>
                              Mass (kg)
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={component.mass}
                              onChange={(e) => updateComponent(index, 'mass', e.target.value)}
                              className="w-full p-2 rounded-lg text-sm"
                              style={{ 
                                backgroundColor: 'var(--background)', 
                                border: '1px solid var(--card-border)',
                                color: 'var(--foreground)'
                              }}
                            />
                          </div>
                          
                          <div>
                            <label className="text-xs block mb-1" style={{ color: 'var(--score-neutral)' }}>
                              Recycled Content (0-1)
                            </label>
                            <input
                              type="number"
                              step="0.05"
                              min="0"
                              max="1"
                              value={component.recycledContent}
                              onChange={(e) => updateComponent(index, 'recycledContent', e.target.value)}
                              className="w-full p-2 rounded-lg text-sm"
                              style={{ 
                                backgroundColor: 'var(--background)', 
                                border: '1px solid var(--card-border)',
                                color: 'var(--foreground)'
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <button
                className="eco-button px-4 py-2 rounded-lg text-white w-full mt-4"
                style={{ backgroundColor: 'var(--primary)' }}
                onClick={() => fetchData('create-run')}
              >
                Create New Run
              </button>
            </div>
          </div>
        </div>
        
        {/* API Response */}
        <div 
          className="p-6 rounded-xl shadow-md mb-8"
          style={{ 
            backgroundColor: 'var(--card-background)',
            border: '1px solid var(--card-border)',
          }}
        >
          <h2 
            className="text-xl font-bold mb-4 flex justify-between items-center"
            style={{ color: 'var(--foreground)' }}
          >
            <span>API Response</span>
            {apiResponse.data !== null && (
              <button
                className="eco-button text-xs px-3 py-1 rounded"
                style={{ 
                  backgroundColor: 'var(--button-hover)',
                  border: '1px solid var(--card-border)',
                  color: 'var(--foreground)'
                }}
                onClick={() => {
                  navigator.clipboard.writeText(
                    typeof apiResponse.data === 'object' && apiResponse.data !== null
                      ? JSON.stringify(apiResponse.data, null, 2)
                      : String(apiResponse.data)
                  );
                }}
              >
                Copy JSON
              </button>
            )}
          </h2>
          
          <div
            className="p-4 rounded-lg"
            style={{ 
              backgroundColor: 'var(--background)', 
              border: '1px solid var(--card-border)',
              minHeight: '200px'
            }}
          >
            {apiResponse.isLoading ? (
              <div className="flex justify-center items-center h-40">
                <div className="animate-spin h-8 w-8 border-4 border-primary rounded-full border-t-transparent"></div>
              </div>
            ) : apiResponse.error ? (
              <div className="text-center p-4" style={{ color: 'var(--status-error)' }}>
                {apiResponse.error}
              </div>
            ) : apiResponse.data ? (
              <pre 
                className="overflow-auto"
                style={{ color: 'var(--foreground)', maxHeight: '400px' }}
              >
                {typeof apiResponse.data === 'object' && apiResponse.data !== null 
                  ? JSON.stringify(apiResponse.data, null, 2)
                  : String(apiResponse.data)}
              </pre>
            ) : (
              <div className="text-center p-4 opacity-60" style={{ color: 'var(--foreground)' }}>
                Select an API endpoint and click the fetch button to see results
              </div>
            )}
          </div>
        </div>
        
        <div className="p-6 rounded-xl shadow-md mb-8 text-sm">
          <h3 className="font-bold mb-2" style={{ color: 'var(--primary)' }}>Notes:</h3>
          <p className="mb-2" style={{ color: 'var(--foreground)' }}>
            This page connects directly to the Muir Carbon Origin API using the MUIR_API_KEY set in your environment.
          </p>
          <ol className="list-decimal pl-5" style={{ color: 'var(--foreground)' }}>
            <li className="mb-1">The API key is securely stored in the .env.local file</li>
            <li className="mb-1">API calls are made directly to service-run-api.muir.ai</li>
            <li className="mb-1">Response data is displayed as raw JSON</li>
          </ol>
          <p className="mt-2 text-xs opacity-70" style={{ color: 'var(--foreground)' }}>
            * If you see authentication errors, verify that your MUIR_API_KEY is correctly set in .env.local and that NEXT_PUBLIC_MUIR_API_KEY is properly exposed.
          </p>
        </div>
        
        <footer className="text-center mt-12 opacity-70 text-sm" style={{ color: 'var(--foreground)' }}>
          <p>Carbon Footprint Analyzer - Muir API Integration</p>
        </footer>
      </div>
    </div>
  );
};

export default MuirApiPage;