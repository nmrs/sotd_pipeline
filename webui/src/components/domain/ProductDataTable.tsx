import React from 'react';
import { CommentProductData, ProductFieldData } from '@/services/api';
import { formatMatchedData, formatEnrichedData } from '@/utils/productDataFormatter';

export type ProductFieldKey = 'razor' | 'blade' | 'brush' | 'soap';

interface ProductDataTableProps {
  productData?: CommentProductData | null;
  dataSource?: 'enriched' | 'matched';
  isEditing?: boolean;
  editValues?: Record<ProductFieldKey, string>;
  onEditChange?: (field: ProductFieldKey, value: string) => void;
}

const PRODUCT_FIELDS: { key: ProductFieldKey; label: string }[] = [
  { key: 'razor', label: 'Razor' },
  { key: 'blade', label: 'Blade' },
  { key: 'brush', label: 'Brush' },
  { key: 'soap', label: 'Soap' },
];

function overrideDisplay(data?: ProductFieldData | null): {
  value: string;
  pending: boolean;
} {
  if (!data) {
    return { value: '', pending: false };
  }
  if (data.override_value) {
    return { value: data.override_value, pending: Boolean(data.override_pending) };
  }
  return { value: '', pending: false };
}

const ProductDataTable: React.FC<ProductDataTableProps> = ({
  productData,
  dataSource,
  isEditing = false,
  editValues,
  onEditChange,
}) => {
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
                Override
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
            {PRODUCT_FIELDS.map((field, index) => {
              const data = productData?.[field.key];
              const original = data?.original || '';
              const matched = data?.matched || null;
              const enriched = data?.enriched || null;
              const formattedMatched = formatMatchedData(matched, field.key);
              const formattedEnriched = formatEnrichedData(enriched);
              const { value: overrideValue, pending } = overrideDisplay(data);

              return (
                <tr key={field.key} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className='px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200'>
                    {field.label}
                  </td>
                  <td className='px-4 py-3 text-sm text-gray-900 border-r border-gray-200'>
                    {original || <span className='text-gray-400'>-</span>}
                  </td>
                  <td className='px-4 py-3 text-sm text-gray-900 border-r border-gray-200'>
                    {isEditing ? (
                      <input
                        type='text'
                        className='w-full min-w-[10rem] rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
                        value={editValues?.[field.key] ?? ''}
                        onChange={e => onEditChange?.(field.key, e.target.value)}
                        aria-label={`${field.label} override`}
                      />
                    ) : overrideValue ? (
                      <div className='flex items-start gap-2'>
                        <span className='whitespace-pre-wrap'>{overrideValue}</span>
                        {pending && (
                          <span className='shrink-0 px-1.5 py-0.5 text-xs rounded bg-amber-100 text-amber-800'>
                            Pending
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className='text-gray-400'>-</span>
                    )}
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
