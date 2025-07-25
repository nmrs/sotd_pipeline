import React, { useState, useEffect, useRef } from 'react';

interface PerformanceMetrics {
  renderTime: number;
  memoryUsage?: number;
  dataSize: number;
  operationCount: number;
  averageResponseTime: number;
}

interface PerformanceMonitorProps {
  dataSize: number;
  operationCount: number;
  onMetricsUpdate?: (metrics: PerformanceMetrics) => void;
  showDetails?: boolean;
}

export const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({
  dataSize,
  operationCount,
  onMetricsUpdate,
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTime: 0,
    dataSize: 0,
    operationCount: 0,
    averageResponseTime: 0,
  });
  const [isExpanded, setIsExpanded] = useState(false);
  const renderStartTime = useRef<number>(0);
  const responseTimes = useRef<number[]>([]);

  useEffect(() => {
    renderStartTime.current = performance.now();
  }, []);

  useEffect(() => {
    const renderTime = performance.now() - renderStartTime.current;
    const memoryUsage = (performance as Performance & { memory?: { usedJSHeapSize: number } })
      .memory?.usedJSHeapSize;

    const newMetrics: PerformanceMetrics = {
      renderTime,
      memoryUsage,
      dataSize,
      operationCount,
      averageResponseTime:
        responseTimes.current.length > 0
          ? responseTimes.current.reduce((a, b) => a + b, 0) / responseTimes.current.length
          : 0,
    };

    setMetrics(newMetrics);
    onMetricsUpdate?.(newMetrics);
  }, [dataSize, operationCount, onMetricsUpdate]);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (ms: number): string => {
    if (ms < 1000) return `${ms.toFixed(2)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getPerformanceColor = (value: number, threshold: number): string => {
    if (value <= threshold * 0.5) return 'text-green-600';
    if (value <= threshold) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className='bg-white border border-gray-200 rounded-lg p-4'>
      <div className='flex items-center justify-between mb-2'>
        <h3 className='text-sm font-medium text-gray-900'>Performance Monitor</h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className='text-xs text-gray-500 hover:text-gray-700'
        >
          {isExpanded ? 'Hide Details' : 'Show Details'}
        </button>
      </div>

      <div className='grid grid-cols-2 md:grid-cols-4 gap-4 mb-3'>
        <div className='text-center'>
          <div className={`text-lg font-semibold ${getPerformanceColor(metrics.renderTime, 100)}`}>
            {formatTime(metrics.renderTime)}
          </div>
          <div className='text-xs text-gray-500'>Render Time</div>
        </div>

        <div className='text-center'>
          <div className='text-lg font-semibold text-blue-600'>
            {metrics.dataSize.toLocaleString()}
          </div>
          <div className='text-xs text-gray-500'>Data Items</div>
        </div>

        <div className='text-center'>
          <div className='text-lg font-semibold text-purple-600'>{metrics.operationCount}</div>
          <div className='text-xs text-gray-500'>Operations</div>
        </div>

        <div className='text-center'>
          <div
            className={`text-lg font-semibold ${getPerformanceColor(metrics.averageResponseTime, 500)}`}
          >
            {formatTime(metrics.averageResponseTime)}
          </div>
          <div className='text-xs text-gray-500'>Avg Response</div>
        </div>
      </div>

      {isExpanded && (
        <div className='border-t border-gray-200 pt-3'>
          <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-xs'>
            <div>
              <div className='font-medium text-gray-700 mb-1'>Memory Usage</div>
              <div className='text-gray-600'>
                {metrics.memoryUsage ? formatBytes(metrics.memoryUsage) : 'N/A'}
              </div>
            </div>
            <div>
              <div className='font-medium text-gray-700 mb-1'>Performance Status</div>
              <div
                className={`font-medium ${
                  metrics.renderTime < 100
                    ? 'text-green-600'
                    : metrics.renderTime < 500
                      ? 'text-yellow-600'
                      : 'text-red-600'
                }`}
              >
                {metrics.renderTime < 100
                  ? 'Excellent'
                  : metrics.renderTime < 500
                    ? 'Good'
                    : 'Needs Optimization'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceMonitor;
