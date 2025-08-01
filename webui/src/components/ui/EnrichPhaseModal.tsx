import React from 'react';
import { X } from 'lucide-react';

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

  // Extract relevant fields for comparison
  const getComparisonText = () => {
    const changes: string[] = [];

    // For brush field, check the enriched data against matched data
    if (field === 'brush') {
      const matchedBrush = originalData?.brush;
      const enrichedBrush = enrichedData?.brush;

      if (matchedBrush && enrichedBrush) {
        // Check for actual changes in brush fields
        const brushFields = ['handle_maker', 'handle_model', 'knot_maker', 'knot_model', 'knot_size_mm', 'fiber'];
        
        brushFields.forEach(brushField => {
          const matchedValue = matchedBrush[brushField];
          const enrichedValue = enrichedBrush[brushField];
          
          // Only show changes if the field exists in enriched data and is different
          if (enrichedValue !== undefined && enrichedValue !== matchedValue) {
            const displayMatched = matchedValue ?? 'None';
            const displayEnriched = enrichedValue ?? 'None';
            changes.push(`${brushField.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${displayMatched} → ${displayEnriched}`);
          }
        });

        // Check for source tracking information
        const sourceFields = ['_extraction_source', '_fiber_extraction_source', '_handle_extraction_source', '_knot_extraction_source'];
        sourceFields.forEach(sourceField => {
          if (enrichedBrush[sourceField]) {
            changes.push(`Source: ${enrichedBrush[sourceField]}`);
          }
        });
      }
    }

    // For other fields, check direct field changes
    if (field !== 'brush') {
      const matchedValue = originalData?.[field];
      const enrichedValue = enrichedData?.[field];
      
      // Only show changes if the field exists in enriched data and is different
      if (enrichedValue !== undefined && enrichedValue !== matchedValue) {
        const displayMatched = matchedValue ?? 'None';
        const displayEnriched = enrichedValue ?? 'None';
        changes.push(`${field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${displayMatched} → ${displayEnriched}`);
      }
    }

    return changes.length > 0 ? changes.join('\n') : 'No changes detected';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Enrich Phase Adjustments</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Original Text:</h3>
            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
              {originalText}
            </p>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Changes:</h3>
            <pre className="text-sm text-gray-600 bg-gray-50 p-3 rounded whitespace-pre-wrap">
              {getComparisonText()}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnrichPhaseModal;
