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
            // Check fiber changes (enriched data overrides matched)
            const matchedKnotFiber = originalData?.knot?.fiber;
            const enrichedFiber = enrichedData?.fiber;
            if (matchedKnotFiber !== enrichedFiber) {
                changes.push(`Fiber: ${matchedKnotFiber || 'None'} → ${enrichedFiber || 'None'}`);
            }

            // Check knot size changes
            const matchedKnotSize = originalData?.knot?.knot_size_mm;
            const enrichedKnotSize = enrichedData?.knot_size_mm;
            if (matchedKnotSize !== enrichedKnotSize) {
                changes.push(`Knot Size: ${matchedKnotSize || 'None'} → ${enrichedKnotSize || 'None'}`);
            }

            // For brush enrichment, only fiber and knot_size_mm can change
            // Brand, model, handle_maker, etc. should remain the same from match phase
            // Don't check other fields as they shouldn't change during brush enrichment
        } else {
            // For other fields, check top-level fields
            if (originalData.fiber !== enrichedData.fiber) {
                changes.push(`Fiber: ${originalData.fiber || 'None'} → ${enrichedData.fiber || 'None'}`);
            }
            if (originalData.knot_size_mm !== enrichedData.knot_size_mm) {
                changes.push(`Knot Size: ${originalData.knot_size_mm || 'None'} → ${enrichedData.knot_size_mm || 'None'}`);
            }
            if (originalData.handle_maker !== enrichedData.handle_maker) {
                changes.push(`Handle: ${originalData.handle_maker || 'None'} → ${enrichedData.handle_maker || 'None'}`);
            }
        }

        // Add extraction source info if available
        if (enrichedData?._extraction_source) {
            changes.push(`Source: ${enrichedData._extraction_source}`);
        }

        return changes.length > 0 ? changes : ['No enrich-phase changes detected'];
    };

    const comparisonText = getComparisonText();

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black bg-opacity-50"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">
                        🔄 Enrich Phase Adjustments
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4">
                    <div className="mb-4">
                        <h4 className="font-medium text-gray-900 mb-2">Original Text:</h4>
                        <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                            {originalText}
                        </p>
                    </div>

                    <div>
                        <h4 className="font-medium text-gray-900 mb-2">Changes Made:</h4>
                        <div className="space-y-2">
                            {comparisonText.map((change, index) => (
                                <div key={index} className="text-sm bg-blue-50 p-2 rounded border-l-4 border-blue-500">
                                    {change}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="flex justify-end p-4 border-t border-gray-200">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default EnrichPhaseModal; 