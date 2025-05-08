'use client';

import { useState } from 'react';
import Image from 'next/image';
import { ProductInput } from '@/components/ProductInput';
import { FootprintAnalysis } from '@/components/FootprintAnalysis';
import { ProductInputData } from '@/types/components';

export default function Home() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [productBrand, setProductBrand] = useState('');
  const [productCategory, setProductCategory] = useState('');
  const [productDescription, setProductDescription] = useState('');
  const webSocketUrl = 'ws://localhost:3005/ws';

  const handleSubmit = (input: ProductInputData) => {
    setProductBrand(input.brand);
    setProductCategory(input.category);
    setProductDescription(input.description);
    setIsAnalyzing(true);
  };

  const handleAnalysisComplete = () => {
    setIsAnalyzing(false);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--border)] py-4">
        <div className="container mx-auto px-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Image 
              src="/globe.svg" 
              alt="Footprint Any Product logo" 
              width={32} 
              height={32} 
              className="dark:invert"
            />
            <h1 className="text-xl font-bold">Footprint Any Product</h1>
          </div>
        </div>
      </header>
      
      <main className="flex-1 container mx-auto px-4 py-12 flex flex-col gap-8">
        <div className="max-w-3xl mx-auto text-center mb-8">
          <h2 className="text-3xl font-bold mb-4">Analyze Any Product&apos;s Carbon Footprint</h2>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            Enter a product URL or name to get a detailed lifecycle carbon analysis powered by AI
          </p>
        </div>
        
        <ProductInput 
          onSubmit={handleSubmit} 
          isLoading={isAnalyzing} 
        />
        
        <FootprintAnalysis
          url={webSocketUrl}
          isStreaming={isAnalyzing}
          brand={productBrand}
          category={productCategory}
          description={productDescription}
          onStreamingComplete={handleAnalysisComplete}
        />
      </main>
      
      <footer className="border-t border-[var(--border)] py-6">
        <div className="container mx-auto px-4 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>© {new Date().getFullYear()} Footprint Any Product. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
