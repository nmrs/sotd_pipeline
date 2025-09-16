import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface Pattern {
    original: string;
    count: number;
}

interface ExpandablePatternsProps {
    topPatterns: Pattern[];
    allPatterns: Pattern[];
    remainingCount: number;
    maxInitial?: number;
}

const ExpandablePatterns: React.FC<ExpandablePatternsProps> = ({
    topPatterns,
    allPatterns,
    remainingCount,
    maxInitial = 3,
}) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const handleToggle = () => {
        setIsExpanded(!isExpanded);
    };

    const displayPatterns = isExpanded ? allPatterns : topPatterns;

    return (
        <div className="space-y-1">
            {displayPatterns.map((pattern, index) => (
                <div key={index} className="text-sm text-gray-700">
                    <span className="font-medium">{pattern.original}</span>
                    <span className="ml-2 text-gray-500">({pattern.count})</span>
                </div>
            ))}

            {remainingCount > 0 && (
                <button
                    onClick={handleToggle}
                    className="flex items-center gap-1 text-sm text-blue-600 font-medium hover:text-blue-800 focus:outline-none focus:underline"
                    aria-label={isExpanded ? 'Show fewer patterns' : 'Show all patterns'}
                >
                    {isExpanded ? (
                        <>
                            <ChevronUp className="h-4 w-4" />
                            Show fewer
                        </>
                    ) : (
                        <>
                            <ChevronDown className="h-4 w-4" />
                            + {remainingCount} more
                        </>
                    )}
                </button>
            )}
        </div>
    );
};

export default ExpandablePatterns;
