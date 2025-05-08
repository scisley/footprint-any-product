import React, { useState } from 'react';
import { SearchFiltersProps } from '../../types';

const SearchFilters: React.FC<SearchFiltersProps> = ({
  onSearch,
  onScoreFilterChange,
  onDateFilterChange
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [minScore, setMinScore] = useState<number>(0);
  const [maxScore, setMaxScore] = useState<number>(100);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchTerm);
  };
  
  const handleScoreFilterChange = () => {
    onScoreFilterChange(minScore, maxScore);
  };
  
  const handleDateFilterChange = () => {
    onDateFilterChange(
      startDate ? startDate : null,
      endDate ? endDate : null
    );
  };
  
  const handleReset = () => {
    setSearchTerm('');
    setMinScore(0);
    setMaxScore(100);
    setStartDate('');
    setEndDate('');
    onSearch('');
    onScoreFilterChange(0, 100);
    onDateFilterChange(null, null);
  };
  
  return (
    <div 
      className="mb-6 p-4 rounded-xl"
      style={{ 
        backgroundColor: 'var(--card-background)',
        border: '1px solid var(--card-border)',
      }}
    >
      <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-2">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search by product name or URL..."
          className="flex-grow p-2 rounded-lg outline-glow focus:outline-none"
          style={{ 
            backgroundColor: 'var(--button-hover)', 
            color: 'var(--foreground)',
            borderWidth: '1px',
            borderColor: 'var(--card-border)',
            borderStyle: 'solid'
          }}
        />
        <button
          type="submit"
          className="eco-button px-4 py-2 rounded-lg font-medium text-white"
          style={{ backgroundColor: 'var(--primary)' }}
        >
          Search
        </button>
        <button
          type="button"
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          className="eco-button px-3 py-2 rounded-lg"
          style={{ 
            backgroundColor: 'var(--button-hover)',
            border: '1px solid var(--card-border)',
            color: 'var(--foreground)'
          }}
        >
          {showAdvancedFilters ? 'Hide Filters' : 'Filters'}
        </button>
      </form>
      
      {showAdvancedFilters && (
        <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--card-border)' }}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Carbon Score Filter */}
            <div>
              <h3 
                className="text-sm font-medium mb-2"
                style={{ color: 'var(--foreground)' }}
              >
                Carbon Score Range
              </h3>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={minScore}
                  onChange={(e) => setMinScore(parseInt(e.target.value))}
                  className="w-20 p-2 rounded"
                  style={{ 
                    backgroundColor: 'var(--button-hover)', 
                    color: 'var(--foreground)',
                    border: '1px solid var(--card-border)',
                  }}
                />
                <span style={{ color: 'var(--foreground)' }}>to</span>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={maxScore}
                  onChange={(e) => setMaxScore(parseInt(e.target.value))}
                  className="w-20 p-2 rounded"
                  style={{ 
                    backgroundColor: 'var(--button-hover)', 
                    color: 'var(--foreground)',
                    border: '1px solid var(--card-border)',
                  }}
                />
                <button
                  type="button"
                  onClick={handleScoreFilterChange}
                  className="eco-button px-3 py-1.5 rounded text-sm"
                  style={{ 
                    backgroundColor: 'var(--button-hover)',
                    border: '1px solid var(--card-border)',
                    color: 'var(--foreground)'
                  }}
                >
                  Apply
                </button>
              </div>
            </div>
            
            {/* Date Filter */}
            <div>
              <h3 
                className="text-sm font-medium mb-2"
                style={{ color: 'var(--foreground)' }}
              >
                Date Range
              </h3>
              <div className="flex items-center gap-3">
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="p-2 rounded"
                  style={{ 
                    backgroundColor: 'var(--button-hover)', 
                    color: 'var(--foreground)',
                    border: '1px solid var(--card-border)',
                  }}
                />
                <span style={{ color: 'var(--foreground)' }}>to</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="p-2 rounded"
                  style={{ 
                    backgroundColor: 'var(--button-hover)', 
                    color: 'var(--foreground)',
                    border: '1px solid var(--card-border)',
                  }}
                />
                <button
                  type="button"
                  onClick={handleDateFilterChange}
                  className="eco-button px-3 py-1.5 rounded text-sm"
                  style={{ 
                    backgroundColor: 'var(--button-hover)',
                    border: '1px solid var(--card-border)',
                    color: 'var(--foreground)'
                  }}
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
          
          <div className="mt-4 text-right">
            <button
              type="button"
              onClick={handleReset}
              className="eco-button px-4 py-1.5 rounded text-sm"
              style={{ 
                backgroundColor: 'var(--button-hover)',
                border: '1px solid var(--card-border)',
                color: 'var(--foreground)'
              }}
            >
              Reset All Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchFilters;