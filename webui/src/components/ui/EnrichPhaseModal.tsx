import React from 'react';
import { X } from 'lucide-react';
import { formatEnrichPhaseChanges } from '../../utils/enrichPhaseUtils';

interface EnrichPhaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  originalData: Record<string, any>;
  enrichedData: Record<string, any>;
  field: string;
  originalText: string;
}

const EnrichPhaseModal: React.FC<EnrichPhaseModalProps> = ({
  isOpen,
  onClose,
  originalData,
  enrichedData,
  field,
  originalText,
}) => {
  if (!isOpen) return null;

  // Use shared utility to format enrich phase changes
  const comparisonText = formatEnrichPhaseChanges(originalData, enrichedData, field);

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
      <div className='bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto'>
        <div className='flex justify-between items-center mb-4'>
          <h2 className='text-lg font-semibold'>Enrich Phase Adjustments</h2>
          <button onClick={onClose} className='text-gray-500 hover:text-gray-700'>
            <X size={20} />
          </button>
        </div>

        <div className='space-y-4'>
          <div>
            <h3 className='font-medium text-gray-900 mb-2'>Original Text:</h3>
            <p className='text-sm text-gray-600 bg-gray-50 p-3 rounded'>{originalText}</p>
          </div>

          <div>
            <h3 className='font-medium text-gray-900 mb-2'>Changes:</h3>
            <pre className='text-sm text-gray-600 bg-gray-50 p-3 rounded whitespace-pre-wrap'>
              {comparisonText}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnrichPhaseModal;
