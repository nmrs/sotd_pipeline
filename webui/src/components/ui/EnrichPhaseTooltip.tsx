import React, { useState } from 'react';
import { Info } from 'lucide-react';

interface EnrichPhaseTooltipProps {
  children: React.ReactNode;
  originalData: Record<string, any>;
  enrichedData: Record<string, any>;
  field: string;
  className?: string;
}

const EnrichPhaseTooltip: React.FC<EnrichPhaseTooltipProps> = ({
  children,
  originalData,
  enrichedData,
  field,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(false);

  // Extract relevant fields for comparison
  const getComparisonText = () => {
    const changes: string[] = [];

    // Compare fiber if it exists
    if (originalData.fiber !== enrichedData.fiber) {
      changes.push(`Fiber: ${originalData.fiber || 'None'} → ${enrichedData.fiber || 'None'}`);
    }

    // Compare other relevant fields based on field type
    if (field === 'brush') {
      if (originalData.knot_size_mm !== enrichedData.knot_size_mm) {
        changes.push(`Knot Size: ${originalData.knot_size_mm || 'None'} → ${enrichedData.knot_size_mm || 'None'}`);
      }
      if (originalData.handle_maker !== enrichedData.handle_maker) {
        changes.push(`Handle: ${originalData.handle_maker || 'None'} → ${enrichedData.handle_maker || 'None'}`);
      }
    }

    // Add extraction source info if available
    if (enrichedData._extraction_source) {
      changes.push(`Source: ${enrichedData._extraction_source}`);
    }

    return changes.length > 0 ? changes.join('\n') : 'No enrich-phase changes detected';
  };

  const comparisonText = getComparisonText();

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="cursor-help"
      >
        {children}
      </div>
      {isVisible && (
        <div className="absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg max-w-xs bottom-full left-1/2 transform -translate-x-1/2 mb-2">
          <div className="font-medium mb-1">Enrich Phase Adjustments:</div>
          <div className="whitespace-pre-line text-xs">
            {comparisonText}
          </div>
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
        </div>
      )}
    </div>
  );
};

export default EnrichPhaseTooltip; 