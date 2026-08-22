import React from 'react';
import { SOAP_SAMPLE_BADGE_SOURCES_TOOLTIP, SOAP_SAMPLE_USAGE_TOOLTIP } from '../../utils/soapSample';

interface SampleUsageBadgeProps {
  className?: string;
  sampleType?: string | null;
}

const SampleUsageBadge: React.FC<SampleUsageBadgeProps> = ({
  className = '',
  sampleType = 'sample',
}) => {
  const label = sampleType && sampleType.trim() ? sampleType.trim() : 'sample';
  const display =
    label.toLowerCase() === 'sample'
      ? 'Sample'
      : label.charAt(0).toUpperCase() + label.slice(1).toLowerCase();

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-sky-100 text-sky-800 border border-sky-200 ${className}`}
      title={`${SOAP_SAMPLE_USAGE_TOOLTIP} ${SOAP_SAMPLE_BADGE_SOURCES_TOOLTIP} Type: ${label}.`}
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
          d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
        />
      </svg>
      {display}
    </span>
  );
};

export default SampleUsageBadge;
