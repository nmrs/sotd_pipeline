# Data Table Components

This directory contains the core data table components used throughout the application. Each component is designed to handle specific use cases while maintaining consistent patterns and performance.

## Components Overview

### BrushSplitTable
A specialized table for editing brush split data with bulk save functionality.

**Location**: `webui/src/components/data/BrushSplitTable.tsx`

**Features**:
- ✅ Bulk save mechanism for multiple changes
- ✅ Row selection with checkboxes
- ✅ Inline editing of handle and knot fields
- ✅ Should not split checkbox
- ✅ Unsaved changes indicator
- ✅ ShadCN Table components for consistent styling

**Usage Example**:
```tsx
import BrushSplitTable from '@/components/data/BrushSplitTable';

const MyComponent = () => {
    const brushSplits = [
        { original: 'Test Brush', handle: 'Test Handle', knot: 'Test Knot' }
    ];

    const handleSave = (index: number, updatedSplit: BrushSplit) => {
        // Handle save logic
    };

    return (
        <BrushSplitTable
            brushSplits={brushSplits}
            onSave={handleSave}
            onSelectionChange={(selected) => console.log(selected)}
        />
    );
};
```

**Props**:
- `brushSplits: BrushSplit[]` - Array of brush split data
- `onSave?: (index: number, updatedSplit: BrushSplit) => void` - Save callback
- `onSelectionChange?: (selectedIndices: number[]) => void` - Selection change callback
- `selectedIndices?: number[]` - Currently selected row indices

### BrushTable
A virtualized table for displaying brush data with filtering capabilities.

**Location**: `webui/src/components/data/BrushTable.tsx`

**Features**:
- ✅ Virtualization for large datasets
- ✅ Hierarchical display (main brush + components)
- ✅ Filtering checkboxes for brushes and components
- ✅ Comment ID linking
- ✅ Status indicators (Matched/Unmatched)
- ✅ Pending changes support

**Usage Example**:
```tsx
import BrushTable from '@/components/data/BrushTable';

const MyComponent = () => {
    const brushData = [
        {
            main: { text: 'Test Brush', count: 5, comment_ids: ['123'], examples: ['ex1'] },
            components: {
                handle: { text: 'Test Handle', status: 'Matched' },
                knot: { text: 'Test Knot', status: 'Unmatched' }
            }
        }
    ];

    return (
        <BrushTable
            items={brushData}
            onBrushFilter={(itemName, isFiltered) => console.log(itemName, isFiltered)}
            onComponentFilter={(componentName, isFiltered) => console.log(componentName, isFiltered)}
            columnWidths={{
                filtered: 100, brush: 200, handle: 150, knot: 150,
                count: 80, comment_ids: 150, examples: 200
            }}
        />
    );
};
```

**Props**:
- `items: BrushData[]` - Array of brush data
- `onBrushFilter: (itemName: string, isFiltered: boolean) => void` - Brush filter callback
- `onComponentFilter: (componentName: string, isFiltered: boolean) => void` - Component filter callback
- `filteredStatus?: Record<string, boolean>` - Current filter status
- `pendingChanges?: Record<string, boolean>` - Pending filter changes
- `columnWidths: object` - Column width configuration
- `onCommentClick?: (commentId: string) => void` - Comment click callback
- `commentLoading?: boolean` - Comment loading state

### GenericDataTable
A flexible, reusable table component with sorting and column resizing.

**Location**: `webui/src/components/data/GenericDataTable.tsx`

**Features**:
- ✅ Custom column rendering
- ✅ Column sorting with visual indicators
- ✅ Column resizing with drag handles
- ✅ Row click handling
- ✅ Loading and empty states
- ✅ Performance logging
- ✅ Sticky headers
- ✅ Responsive design

**Usage Example**:
```tsx
import { GenericDataTable, DataTableColumn } from '@/components/data/GenericDataTable';

const MyComponent = () => {
    const data = [
        { id: 1, name: 'Item 1', count: 10 },
        { id: 2, name: 'Item 2', count: 5 }
    ];

    const columns: DataTableColumn[] = [
        { key: 'id', header: 'ID', width: 50 },
        { key: 'name', header: 'Name', width: 200 },
        { 
            key: 'count', 
            header: 'Count', 
            width: 100,
            render: (value) => <span className="font-bold">{value}</span>
        }
    ];

    return (
        <GenericDataTable
            data={data}
            columns={columns}
            onSort={(column) => console.log('Sort:', column)}
            onRowClick={(row) => console.log('Row clicked:', row)}
            enablePerformanceLogging={true}
        />
    );
};
```

**Props**:
- `data: T[]` - Array of data items
- `columns: DataTableColumn<T>[]` - Column definitions
- `onRowClick?: (row: T) => void` - Row click callback
- `onSort?: (column: string) => void` - Sort callback
- `sortColumn?: string` - Currently sorted column
- `sortDirection?: 'asc' | 'desc'` - Sort direction
- `emptyMessage?: string` - Empty state message
- `loading?: boolean` - Loading state
- `testId?: string` - Test identifier
- `className?: string` - Additional CSS classes
- `maxHeight?: string` - Maximum table height
- `enablePerformanceLogging?: boolean` - Enable performance logging

### VirtualizedTable
A high-performance virtualized table for large datasets.

**Location**: `webui/src/components/data/VirtualizedTable.tsx`

**Features**:
- ✅ Virtualization with react-window
- ✅ Auto-sizing with react-virtualized-auto-sizer
- ✅ Custom row rendering
- ✅ Performance optimized for large datasets
- ✅ Smooth scrolling
- ✅ Memory efficient

**Usage Example**:
```tsx
import { VirtualizedTable } from '@/components/data/VirtualizedTable';

const MyComponent = () => {
    const data = Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `Item ${i}`,
        value: Math.random()
    }));

    const columns = [
        { key: 'id', header: 'ID', width: 80 },
        { key: 'name', header: 'Name', width: 200 },
        { key: 'value', header: 'Value', width: 150 }
    ];

    return (
        <VirtualizedTable
            data={data}
            columns={columns}
            height={400}
            rowHeight={48}
            resizable={true}
        />
    );
};
```

**Props**:
- `data: T[]` - Array of data items
- `columns: DataTableColumn<T>[]` - Column definitions
- `height: number` - Table height in pixels
- `rowHeight: number` - Height of each row
- `resizable?: boolean` - Enable column resizing

## Design Patterns

### Column Definition Pattern
All table components use a consistent column definition pattern:

```tsx
interface DataTableColumn<T = any> {
    key: string;           // Unique column identifier
    header: string;        // Display name
    width?: number;        // Column width
    render?: (value: any, row: T) => React.ReactNode;  // Custom renderer
}
```

### Performance Considerations
- **Virtualization**: Use VirtualizedTable for datasets > 100 rows
- **Memoization**: Components use React.memo and useMemo for performance
- **Event Handling**: Debounced resize operations to prevent excessive re-renders
- **Memory Management**: Only render visible rows in virtualized tables

### Styling Guidelines
- **ShadCN Components**: Use ShadCN Table components for consistency
- **Color Tokens**: Use Tailwind CSS color tokens (gray-50, blue-600, etc.)
- **Spacing**: Use consistent spacing (p-3, gap-4, etc.)
- **Responsive**: Tables should be responsive and handle overflow gracefully

### Accessibility
- **ARIA Labels**: All interactive elements have proper ARIA labels
- **Keyboard Navigation**: Tables support keyboard navigation
- **Screen Readers**: Proper table structure for screen readers
- **Focus Management**: Clear focus indicators and management

## Migration Notes

### From GenericDataTable to ShadCN
When migrating from GenericDataTable to ShadCN components:

1. **Column Definitions**: Convert to ShadCN Table structure
2. **Cell Rendering**: Adapt render functions to use cell context
3. **Styling**: Use ShadCN Table components for consistent styling
4. **Performance**: Consider VirtualizedTable for large datasets

### Performance Optimization
- Use `enablePerformanceLogging` to identify bottlenecks
- Monitor render times for large datasets
- Consider virtualization for datasets > 100 rows
- Use React.memo for expensive components

## Testing Strategy

### Unit Tests
- Test component rendering with various data sizes
- Test user interactions (clicking, sorting, resizing)
- Test edge cases (empty data, loading states)
- Test accessibility features

### Integration Tests
- Test component interactions
- Test data flow between components
- Test performance with realistic data sizes

### Performance Tests
- Test with 1000+ rows
- Monitor memory usage
- Test scrolling performance
- Test sorting and filtering performance

## Future Enhancements

### Planned Features
- [ ] Advanced filtering capabilities
- [ ] Export functionality (CSV, Excel)
- [ ] Column reordering
- [ ] Row grouping
- [ ] Advanced sorting (multi-column)

### Performance Improvements
- [ ] Lazy loading for large datasets
- [ ] Optimized re-render strategies
- [ ] Better memory management
- [ ] Enhanced virtualization

### Accessibility Enhancements
- [ ] Enhanced keyboard navigation
- [ ] Better screen reader support
- [ ] High contrast mode support
- [ ] Voice control compatibility 