import React, { useState, useEffect } from 'react';
import { GenericDataTable, DataTableColumn } from './GenericDataTable';
import { GenericDataTableOptimized } from './GenericDataTableOptimized';

interface TestData {
    id: number;
    name: string;
    email: string;
    status: string;
    date: string;
}

const PerformanceTest: React.FC = () => {
    const [testData, setTestData] = useState<TestData[]>([]);
    const [enableLogging, setEnableLogging] = useState(false);
    const [sortColumn, setSortColumn] = useState<string>('');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
    const [useOptimized, setUseOptimized] = useState(false);
    const [dataSize, setDataSize] = useState(1000);

    // Generate test data
    useEffect(() => {
        const data: TestData[] = [];
        for (let i = 0; i < dataSize; i++) {
            data.push({
                id: i,
                name: `User ${i}`,
                email: `user${i}@example.com`,
                status: i % 3 === 0 ? 'active' : i % 3 === 1 ? 'inactive' : 'pending',
                date: new Date(Date.now() - Math.random() * 1000000000).toISOString()
            });
        }
        setTestData(data);
    }, [dataSize]);

    const columns: DataTableColumn<TestData>[] = [
        { key: 'id', header: 'ID', width: 80 },
        { key: 'name', header: 'Name', width: 200 },
        { key: 'email', header: 'Email', width: 250 },
        { key: 'status', header: 'Status', width: 120 },
        { key: 'date', header: 'Date', width: 150 }
    ];

    const handleSort = (column: string) => {
        const start = performance.now();
        if (sortColumn === column) {
            setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
        } else {
            setSortColumn(column);
            setSortDirection('asc');
        }
        const end = performance.now();
        console.log(`Sort operation took ${end - start}ms`);
    };

    const TableComponent = useOptimized ? GenericDataTableOptimized : GenericDataTable;
    const tableLabel = useOptimized ? 'Optimized' : 'Baseline';

    return (
        <div className="p-4">
            <div className="mb-4 space-y-4">
                <h2 className="text-xl font-bold">Performance Test</h2>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="flex items-center space-x-2">
                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                checked={enableLogging}
                                onChange={(e) => setEnableLogging(e.target.checked)}
                                className="mr-2"
                            />
                            Enable Performance Logging
                        </label>
                    </div>

                    <div className="flex items-center space-x-2">
                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                checked={useOptimized}
                                onChange={(e) => setUseOptimized(e.target.checked)}
                                className="mr-2"
                            />
                            Use Optimized Version
                        </label>
                    </div>

                    <div className="flex items-center space-x-2">
                        <label className="text-sm font-medium">Data Size:</label>
                        <select
                            value={dataSize}
                            onChange={(e) => setDataSize(Number(e.target.value))}
                            className="border rounded px-2 py-1 text-sm"
                        >
                            <option value={100}>100 rows</option>
                            <option value={500}>500 rows</option>
                            <option value={1000}>1000 rows</option>
                            <option value={2000}>2000 rows</option>
                            <option value={5000}>5000 rows</option>
                        </select>
                    </div>

                    <div className="text-sm text-gray-600">
                        Current: {tableLabel} ({testData.length} rows)
                    </div>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded p-3">
                    <h3 className="font-semibold text-blue-900 mb-2">Instructions:</h3>
                    <ul className="text-sm text-blue-800 space-y-1">
                        <li>• Toggle between Baseline and Optimized versions</li>
                        <li>• Enable performance logging to see console metrics</li>
                        <li>• Try resizing columns and sorting to measure performance</li>
                        <li>• Adjust data size to test different scenarios</li>
                        <li>• Check browser console for detailed timing information</li>
                    </ul>
                </div>
            </div>

            <div className="mb-4 p-3 bg-gray-100 rounded">
                <h3 className="font-semibold mb-2">Performance Metrics:</h3>
                <div className="text-sm text-gray-700">
                    <p>• Column width calculation time</p>
                    <p>• Sorting operation time</p>
                    <p>• Resize operation frequency and timing</p>
                    <p>• Total resize session duration</p>
                </div>
            </div>

            <TableComponent
                data={testData}
                columns={columns}
                onSort={handleSort}
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                enablePerformanceLogging={enableLogging}
                testId={`performance-test-table-${useOptimized ? 'optimized' : 'baseline'}`}
            />
        </div>
    );
};

export default PerformanceTest; 