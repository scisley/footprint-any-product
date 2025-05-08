'use client';

import { useState } from 'react';
import { ProductInputProps } from '@/types/components';

export function ProductInput({ onSubmit, isLoading = false }: ProductInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSubmit(input.trim());
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <label 
            htmlFor="product-input" 
            className="text-lg font-medium"
          >
            Enter a product URL or name
          </label>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            We&apos;ll analyze the environmental impact of the product and generate a carbon footprint report
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            id="product-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="https://www.example.com/product or Product Name"
            className="flex-1 px-4 py-3 rounded-lg border border-[var(--border)] bg-background focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-6 py-3 bg-[var(--primary)] hover:bg-[var(--primary-dark)] text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors sm:w-auto w-full"
          >
            {isLoading ? (
              <div className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Starting analysis...</span>
              </div>
            ) : (
              "Analyze Carbon Footprint"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}