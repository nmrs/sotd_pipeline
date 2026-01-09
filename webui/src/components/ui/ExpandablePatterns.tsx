import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface Pattern {
    original: string;
    count: number;
    match_type: string;
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

    const getMatchTypeColor = (matchType: string) => {
        switch (matchType) {
            case 'exact':
                return 'bg-green-100 text-green-800';
            case 'regex':
                return 'bg-blue-100 text-blue-800';
            case 'brand':
                return 'bg-orange-100 text-orange-800';
            case 'dash_split':
                return 'bg-purple-100 text-purple-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="space-y-1">
            {displayPatterns.map((pattern, index) => (
                <div key={index} className="text-sm text-gray-700 flex items-center gap-2">
                    <span className="font-medium">{pattern.original}</span>
                    <span className="text-gray-500">({pattern.count})</span>
                    <span className={`inline-flex items-center px-1.5 py-0.5 text-xs font-semibold rounded-full ${getMatchTypeColor(pattern.match_type)}`}>
                        {pattern.match_type}
                    </span>
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
