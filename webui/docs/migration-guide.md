# Migration Guide

This guide provides step-by-step instructions for migrating existing components to use the new ShadCN-based component library patterns.

## Overview

The migration process involves updating components to follow consistent design patterns, use ShadCN components where appropriate, and maintain performance while improving maintainability.

## Migration Checklist

### Pre-Migration
- [ ] Review existing component functionality
- [ ] Identify dependencies and imports
- [ ] Plan component structure changes
- [ ] Prepare test updates

### During Migration
- [ ] Update component imports
- [ ] Replace custom styling with ShadCN/Tailwind
- [ ] Update prop interfaces
- [ ] Maintain existing functionality
- [ ] Update tests

### Post-Migration
- [ ] Verify all tests pass
- [ ] Test component interactions
- [ ] Validate performance
- [ ] Update documentation

## Component-Specific Migration Guides

### Table Components

#### From Custom Table to ShadCN Table

**Before**:
```tsx
<div className="custom-table">
  <table>
    <thead>
      <tr>
        <th>Header</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Content</td>
      </tr>
    </tbody>
  </table>
</div>
```

**After**:
```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

<div className="border rounded-lg">
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Header</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow>
        <TableCell>Content</TableCell>
      </TableRow>
    </TableBody>
  </Table>
</div>
```

#### From GenericDataTable to Specialized Components

**Before**:
```tsx
import { GenericDataTable } from '@/components/data/GenericDataTable';

const columns = [
  { key: 'name', header: 'Name', width: 200 },
  { key: 'value', header: 'Value', width: 150 }
];

<GenericDataTable
  data={data}
  columns={columns}
  onSort={handleSort}
/>
```

**After** (for specialized use cases):
```tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

<Table>
  <TableHeader>
    <TableRow>
      <TableHead onClick={() => handleSort('name')}>Name</TableHead>
      <TableHead onClick={() => handleSort('value')}>Value</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {sortedData.map((item) => (
      <TableRow key={item.id}>
        <TableCell>{item.name}</TableCell>
        <TableCell>{item.value}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

### Form Components

#### From Custom Inputs to ShadCN Inputs

**Before**:
```tsx
<input 
  className="custom-input"
  value={value}
  onChange={handleChange}
/>
```

**After**:
```tsx
import { Input } from '@/components/ui/input';

<Input
  value={value}
  onChange={handleChange}
  className="w-full"
/>
```

#### From Custom Checkboxes to ShadCN Checkboxes

**Before**:
```tsx
<input 
  type="checkbox"
  className="custom-checkbox"
  checked={checked}
  onChange={handleChange}
/>
```

**After**:
```tsx
import { Checkbox } from '@/components/ui/checkbox';

<Checkbox
  checked={checked}
  onCheckedChange={handleChange}
/>
```

### Button Components

#### From Custom Buttons to ShadCN Buttons

**Before**:
```tsx
<button className="custom-button">
  Click me
</button>
```

**After**:
```tsx
import { Button } from '@/components/ui/button';

<Button>
  Click me
</Button>
```

## Styling Migration

### Color Migration

**Before**:
```tsx
<div className="custom-blue-bg custom-text">
  Content
</div>
```

**After**:
```tsx
<div className="bg-blue-600 text-white">
  Content
</div>
```

### Spacing Migration

**Before**:
```tsx
<div className="custom-spacing">
  Content
</div>
```

**After**:
```tsx
<div className="p-4 space-y-4">
  Content
</div>
```

### Typography Migration

**Before**:
```tsx
<h1 className="custom-title">Title</h1>
<p className="custom-text">Text</p>
```

**After**:
```tsx
<h1 className="text-xl font-semibold text-gray-900">Title</h1>
<p className="text-sm text-gray-600">Text</p>
```

## Performance Optimization

### Virtualization Migration

**Before**:
```tsx
{data.map((item) => (
  <div key={item.id}>{item.name}</div>
))}
```

**After** (for large datasets):
```tsx
import { VirtualizedTable } from '@/components/data/VirtualizedTable';

<VirtualizedTable
  data={data}
  columns={columns}
  height={400}
  rowHeight={48}
/>
```

### Memoization Migration

**Before**:
```tsx
const MyComponent = ({ data }) => {
  const processedData = data.map(item => ({
    ...item,
    processed: item.value * 2
  }));
  
  return <div>{/* render */}</div>;
};
```

**After**:
```tsx
const MyComponent = ({ data }) => {
  const processedData = useMemo(() => 
    data.map(item => ({
      ...item,
      processed: item.value * 2
    })), [data]
  );
  
  return <div>{/* render */}</div>;
};
```

## Testing Migration

### Test Updates

**Before**:
```tsx
test('should render table', () => {
  render(<CustomTable data={data} />);
  expect(screen.getByTestId('custom-table')).toBeInTheDocument();
});
```

**After**:
```tsx
test('should render table', () => {
  render(<Table data={data} />);
  expect(screen.getByRole('table')).toBeInTheDocument();
});
```

### Accessibility Testing

**Before**:
```tsx
test('should be accessible', () => {
  render(<CustomComponent />);
  // Basic accessibility checks
});
```

**After**:
```tsx
test('should be accessible', () => {
  render(<Component />);
  
  // Test keyboard navigation
  const button = screen.getByRole('button');
  button.focus();
  fireEvent.keyDown(button, { key: 'Enter' });
  
  // Test ARIA labels
  expect(screen.getByLabelText('Sort by name')).toBeInTheDocument();
  
  // Test screen reader support
  expect(screen.getByRole('table')).toBeInTheDocument();
});
```

## Common Migration Patterns

### State Management Migration

**Before**:
```tsx
const [sortColumn, setSortColumn] = useState('');
const [sortDirection, setSortDirection] = useState('asc');

const handleSort = (column) => {
  if (sortColumn === column) {
    setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
  } else {
    setSortColumn(column);
    setSortDirection('asc');
  }
};
```

**After**:
```tsx
const [sortState, setSortState] = useState({ column: '', direction: 'asc' });

const handleSort = (column) => {
  setSortState(prev => ({
    column,
    direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
  }));
};
```

### Event Handling Migration

**Before**:
```tsx
const handleClick = (e) => {
  e.preventDefault();
  e.stopPropagation();
  // custom logic
};
```

**After**:
```tsx
const handleClick = useCallback((e) => {
  e.preventDefault();
  e.stopPropagation();
  // custom logic
}, [dependencies]);
```

## Troubleshooting

### Common Issues

#### Import Errors
**Problem**: Cannot find module '@/components/ui/table'
**Solution**: Ensure ShadCN components are properly installed and configured

#### Styling Conflicts
**Problem**: Custom styles overriding ShadCN styles
**Solution**: Remove custom CSS and use Tailwind utility classes

#### Performance Issues
**Problem**: Component re-rendering too frequently
**Solution**: Add React.memo, useMemo, and useCallback where appropriate

#### Test Failures
**Problem**: Tests failing after migration
**Solution**: Update test selectors to match new component structure

### Debugging Tips

1. **Check Console**: Look for import errors and warnings
2. **Inspect Elements**: Verify styling is applied correctly
3. **Test Interactions**: Ensure all functionality still works
4. **Performance Profile**: Use React DevTools to identify bottlenecks

## Migration Timeline

### Phase 1: Foundation (Week 1)
- [ ] Set up ShadCN components
- [ ] Create base component library
- [ ] Establish design system

### Phase 2: Core Components (Week 2)
- [ ] Migrate table components
- [ ] Migrate form components
- [ ] Migrate button components

### Phase 3: Specialized Components (Week 3)
- [ ] Migrate complex components
- [ ] Optimize performance
- [ ] Update tests

### Phase 4: Documentation (Week 4)
- [ ] Update component documentation
- [ ] Create migration examples
- [ ] Final testing and validation

## Success Metrics

### Functional Success
- [ ] All components work as expected
- [ ] No breaking changes
- [ ] All tests pass
- [ ] Performance maintained or improved

### Design Success
- [ ] Consistent styling across components
- [ ] ShadCN design system followed
- [ ] Accessibility compliance
- [ ] Responsive design working

### Code Quality Success
- [ ] Reduced code duplication
- [ ] Improved maintainability
- [ ] Better component organization
- [ ] Clear documentation

## Best Practices

### Do's
- ✅ Test thoroughly before and after migration
- ✅ Maintain existing functionality
- ✅ Use consistent patterns
- ✅ Document changes
- ✅ Optimize for performance

### Don'ts
- ❌ Break existing functionality
- ❌ Ignore accessibility requirements
- ❌ Skip testing
- ❌ Use inconsistent patterns
- ❌ Forget to update documentation

## Support

For migration support:
1. Check the component documentation
2. Review design system guidelines
3. Test with the provided examples
4. Consult the troubleshooting section
5. Create an issue if problems persist 