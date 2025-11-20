import React from 'react';
import { CommentProductData } from '@/services/api';
import { formatMatchedData, formatEnrichedData } from '@/utils/productDataFormatter';

interface ProductDataTableProps {
  productData: CommentProductData;
  dataSource?: 'enriched' | 'matched';
}

const ProductDataTable: React.FC<ProductDataTableProps> = ({ productData, dataSource }) => {
  const productFields = [
    { key: 'razor' as const, label: 'Razor' },
    { key: 'blade' as const, label: 'Blade' },
    { key: 'brush' as const, label: 'Brush' },
    { key: 'soap' as const, label: 'Soap' },
  ];

  const rows = productFields
    .map(field => ({
      ...field,
      data: productData[field.key],
    }))
    .filter(row => row.data !== null && row.data !== undefined);

  if (rows.length === 0) {
    return null;
  }

  return (
    <div className='mt-4'>
      <div className='mb-2 flex items-center justify-between'>
        <h3 className='text-sm font-medium text-gray-700'>Product Data</h3>
        {dataSource && (
          <span
            className={`px-2 py-1 text-xs rounded-full ${
              dataSource === 'enriched'
                ? 'bg-green-100 text-green-800'
                : 'bg-blue-100 text-blue-800'
            }`}
          >
            {dataSource === 'enriched' ? 'Enriched Phase' : 'Matched Phase'}
          </span>
        )}
      </div>
      <div className='overflow-x-auto'>
        <table className='min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg'>
          <thead className='bg-gray-50'>
            <tr>
              <th className='px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200'>
                Product
              </th>
              <th className='px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200'>
                Original
              </th>
              <th className='px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200'>
                Matched
              </th>
              <th className='px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                Enriched
              </th>
            </tr>
          </thead>
          <tbody className='bg-white divide-y divide-gray-200'>
            {rows.map((row, index) => {
              const { data, label } = row;
              const original = data?.original || '';
              const matched = data?.matched || null;
              const enriched = data?.enriched || null;
              const formattedMatched = formatMatchedData(matched, row.key);
              const formattedEnriched = formatEnrichedData(enriched);

              return (
                <tr key={row.key} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className='px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200'>
                    {label}
                  </td>
                  <td className='px-4 py-3 text-sm text-gray-900 border-r border-gray-200'>
                    {original || <span className='text-gray-400'>-</span>}
                  </td>
                  <td className='px-4 py-3 text-sm text-gray-700 border-r border-gray-200'>
                    {matched ? (
                      <div className='whitespace-pre-wrap'>{formattedMatched}</div>
                    ) : (
                      <span className='text-gray-400'>-</span>
                    )}
                  </td>
                  <td className='px-4 py-3 text-sm text-gray-700'>
                    {enriched ? (
                      <div className='whitespace-pre-wrap'>{formattedEnriched}</div>
                    ) : (
                      <span className='text-gray-400'>-</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ProductDataTable;
