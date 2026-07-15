import React from 'react';
import { SOAP_MASHUP_BADGE_SOURCES_TOOLTIP, SOAP_MASHUP_EXCLUSION_TOOLTIP } from '../../utils/soapMashup';

interface MashupExclusionBadgeProps {
  className?: string;
}

const MashupExclusionBadge: React.FC<MashupExclusionBadgeProps> = ({ className = '' }) => (
  <span
    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200 ${className}`}
    title={`${SOAP_MASHUP_EXCLUSION_TOOLTIP} ${SOAP_MASHUP_BADGE_SOURCES_TOOLTIP}`}
  >
    <svg
      className="w-3 h-3 mr-1"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
      />
    </svg>
    Mashup
  </span>
);

export default MashupExclusionBadge;
