'use client';

import { useState } from 'react';
import { ProductInputProps, ProductInputData } from '@/types/components';

export function ProductInput({ onSubmit, isLoading = false }: ProductInputProps) {
  const [productUrl, setProductUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (productUrl.trim() && !isLoading) {
      onSubmit({ url: productUrl.trim() });
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h2 className="text-xl font-semibold">Enter Product URL</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Provide the URL of the product page for analysis.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4">
          <div>
            <label htmlFor="product-url" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Product URL
            </label>
            <input
              id="product-url"
              type="url"
              value={productUrl}
              onChange={(e) => setProductUrl(e.target.value)}
              placeholder="e.g., https://www.example.com/product-page"
              className="w-full px-4 py-3 rounded-lg border border-[var(--border)] bg-background focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
              disabled={isLoading}
              required
            />
          </div>
        </div>
        
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!productUrl.trim() || isLoading}
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
