import React from 'react';
import { BrushMatchingAnalyzer } from '@/components/BrushMatchingAnalyzer';

export function BrushMatchingAnalyzerPage() {
  return (
    <div className='min-h-screen bg-gray-50'>
      <div className='container mx-auto py-8'>
        <div className='mb-8'>
          <h1 className='text-3xl font-bold text-gray-900 mb-2'>Brush Matching Analyzer</h1>
          <p className='text-gray-600'>
            Test brush strings and see detailed scoring results from the brush matching system.
          </p>
        </div>

        <BrushMatchingAnalyzer />
      </div>
    </div>
  );
}
