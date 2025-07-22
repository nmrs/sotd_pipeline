# Migration Guide

This document provides a comprehensive guide for migrating existing components to use the **mandatory ShadCN + Tailwind first approach** and the new reusable component library.

---

## Migration Overview

### **MANDATORY**: Migration Priority
1. **High Priority**: Table components (migrate to ShadCN DataTable)
2. **High Priority**: Form components (migrate to ShadCN form components)
3. **Medium Priority**: Layout components (use Tailwind utilities)
4. **Medium Priority**: Button and input components (use ShadCN)
5. **Low Priority**: Specialized components (extend ShadCN when possible)

### Migration Process
1. **Identify components to migrate** - List all components that need updating
2. **Check ShadCN alternatives** - Find ShadCN components that can replace custom ones
3. **Update component usage** - Replace custom components with ShadCN equivalents
4. **Update tests** - Ensure all tests pass with new components
5. **Update documentation** - Update component documentation
6. **Remove old components** - Delete unused custom components

---

## Table Component Migration

### Before: Custom Table Implementation
```tsx
// ❌ OLD - Custom table component
import { CustomTable } from './CustomTable';

<CustomTable
  data={brushSplits}
  columns={[
    { key: 'original', header: 'Original', render: (value) => <span>{value}</span> },
    { key: 'handle', header: 'Handle', render: (value) => <input value={value} /> }
  ]}
  onSort={handleSort}
  onFilter={handleFilter}
/>
```

### After: ShadCN DataTable Implementation
```tsx
// ✅ NEW - ShadCN DataTable component
import { DataTable } from '@/components/ui/data-table';
import { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<BrushSplit>[] = [
  {
    accessorKey: 'original',
    header: 'Original',
    cell: ({ row }) => <span>{row.original.original}</span>
  },
  {
    accessorKey: 'handle',
    header: 'Handle',
    cell: ({ row }) => <input value={row.original.handle} />
  }
];

<DataTable
  columns={columns}
  data={brushSplits}
  resizable={true}
  sortable={true}
  filterable={true}
/>
```

### Specialized Table Components
For specialized use cases, use our specialized table components:

```tsx
// ✅ NEW - Specialized table components
import { BrushSplitDataTable } from '@/components/data/BrushSplitDataTable';
import { UnmatchedAnalyzerDataTable } from '@/components/data/UnmatchedAnalyzerDataTable';
import { PerformanceDataTable } from '@/components/data/PerformanceDataTable';
import { BrushDataTable } from '@/components/data/BrushDataTable';

// For brush split validation with inline editing
<BrushSplitDataTable
  brushSplits={brushSplits}
  onSave={handleSave}
  onSelectionChange={handleSelectionChange}
/>

// For unmatched analyzer with filtering and virtualization
<UnmatchedAnalyzerDataTable
  data={unmatchedData}
  filteredStatus={filteredStatus}
  onFilteredStatusChange={handleFilteredStatusChange}
  fieldType="brush"
/>

// For performance metrics with monitoring
<PerformanceDataTable data={performanceData} />

// For brush data with hierarchical subrows
<BrushDataTable data={brushData} />
```

---

## Form Component Migration

### Before: Custom Form Components
```tsx
// ❌ OLD - Custom form components
import { CustomInput } from './CustomInput';
import { CustomSelect } from './CustomSelect';
import { CustomButton } from './CustomButton';

<div className="form-container">
  <label>Name</label>
  <CustomInput value={name} onChange={setName} />
  
  <label>Category</label>
  <CustomSelect value={category} onChange={setCategory} options={categories} />
  
  <CustomButton onClick={handleSubmit}>Submit</CustomButton>
</div>
```

### After: Reusable Form Components
```tsx
// ✅ NEW - Reusable form components
import { FormContainer, FormField, TextInput, SelectInput, FormActions } from '@/components/ui/reusable-forms';
import { PrimaryButton, SecondaryButton } from '@/components/ui/reusable-buttons';

<FormContainer onSubmit={handleSubmit}>
  <FormField label="Name" error={errors.name} required>
    <TextInput
      value={name}
      onChange={setName}
      placeholder="Enter your name"
    />
  </FormField>
  
  <FormField label="Category" error={errors.category} required>
    <SelectInput
      value={category}
      onChange={setCategory}
      options={categories}
      placeholder="Select a category"
    />
  </FormField>
  
  <FormActions>
    <PrimaryButton type="submit" loading={isSubmitting}>
      Submit
    </PrimaryButton>
    <SecondaryButton type="button" onClick={handleCancel}>
      Cancel
    </SecondaryButton>
  </FormActions>
</FormContainer>
```

---

## Button Component Migration

### Before: Custom Button Components
```tsx
// ❌ OLD - Custom button components
import { CustomButton } from './CustomButton';

<CustomButton
  variant="primary"
  onClick={handleSave}
  disabled={isLoading}
  className="save-button"
>
  {isLoading ? 'Saving...' : 'Save'}
</CustomButton>
```

### After: Reusable Button Components
```tsx
// ✅ NEW - Reusable button components
import { PrimaryButton, SecondaryButton, DangerButton, SuccessButton } from '@/components/ui/reusable-buttons';

<PrimaryButton
  onClick={handleSave}
  loading={isLoading}
>
  Save
</PrimaryButton>

<SecondaryButton onClick={handleCancel}>
  Cancel
</SecondaryButton>

<DangerButton onClick={handleDelete} loading={isDeleting}>
  Delete
</DangerButton>

<SuccessButton onClick={handleConfirm} loading={isConfirming}>
  Confirm
</SuccessButton>
```

---

## Layout Component Migration

### Before: Custom Layout Components
```tsx
// ❌ OLD - Custom layout components
import { CustomCard } from './CustomCard';
import { CustomContainer } from './CustomContainer';

<CustomContainer>
  <CustomCard title="User Information">
    <div>Content goes here</div>
  </CustomCard>
</CustomContainer>
```

### After: Reusable Layout Components
```tsx
// ✅ NEW - Reusable layout components
import { PageLayout, CardLayout, SectionLayout } from '@/components/ui/reusable-layout';

<PageLayout title="Dashboard" subtitle="Overview of your data">
  <SectionLayout title="User Information" description="Personal details">
    <CardLayout title="Profile" subtitle="Basic information">
      <div>Content goes here</div>
    </CardLayout>
  </SectionLayout>
</PageLayout>
```

---

## Styling Migration

### Before: Inline Styles and Custom CSS
```tsx
// ❌ OLD - Inline styles and custom CSS
<div style={{ display: 'flex', padding: '16px', backgroundColor: '#f3f4f6' }}>
  <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
    Title
  </h2>
  <button style={{ 
    backgroundColor: '#2563eb', 
    color: 'white', 
    padding: '8px 16px',
    borderRadius: '4px'
  }}>
    Action
  </button>
</div>

// Custom CSS
.save-button {
  background-color: #2563eb;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
}
```

### After: Tailwind Utilities
```tsx
// ✅ NEW - Tailwind utilities
<div className="flex p-4 bg-gray-100">
  <h2 className="text-lg font-semibold mb-2">
    Title
  </h2>
  <button className="bg-blue-600 text-white px-4 py-2 rounded">
    Action
  </button>
</div>
```

---

## Component Testing Migration

### Before: Custom Component Tests
```tsx
// ❌ OLD - Custom component tests
import { render, screen } from '@testing-library/react';
import { CustomButton } from './CustomButton';

test('CustomButton renders correctly', () => {
  render(<CustomButton>Click me</CustomButton>);
  expect(screen.getByText('Click me')).toBeInTheDocument();
});
```

### After: Reusable Component Tests
```tsx
// ✅ NEW - Reusable component tests
import { render, screen, fireEvent } from '@testing-library/react';
import { PrimaryButton } from '@/components/ui/reusable-buttons';

describe('PrimaryButton', () => {
  test('renders correctly with all props', () => {
    const handleClick = jest.fn();
    render(
      <PrimaryButton onClick={handleClick} loading={false}>
        Click me
      </PrimaryButton>
    );
    
    expect(screen.getByText('Click me')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalled();
  });

  test('shows loading state', () => {
    render(
      <PrimaryButton loading={true}>
        Save
      </PrimaryButton>
    );
    
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  test('supports keyboard navigation', () => {
    render(<PrimaryButton>Click me</PrimaryButton>);
    
    const button = screen.getByRole('button');
    button.focus();
    expect(button).toHaveFocus();
    
    fireEvent.keyDown(button, { key: 'Enter' });
    // Test keyboard interaction
  });
});
```

---

## Performance Optimization Migration

### Before: Unoptimized Components
```tsx
// ❌ OLD - Unoptimized components
const ExpensiveComponent = ({ data }) => {
  const processedData = data.map(item => {
    // Expensive processing
    return processItem(item);
  });

  return (
    <div>
      {processedData.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
};
```

### After: Optimized Components
```tsx
// ✅ NEW - Optimized components
const ExpensiveComponent = React.memo(({ data }) => {
  const processedData = useMemo(() => {
    return data.map(item => processItem(item));
  }, [data]);

  const handleClick = useCallback((id) => {
    // Handle click
  }, []);

  return (
    <div>
      {processedData.map(item => (
        <div key={item.id} onClick={() => handleClick(item.id)}>
          {item.name}
        </div>
      ))}
    </div>
  );
});
```

---

## Accessibility Migration

### Before: Basic Accessibility
```tsx
// ❌ OLD - Basic accessibility
<button onClick={handleClick}>
  <Icon />
  Save
</button>
```

### After: Comprehensive Accessibility
```tsx
// ✅ NEW - Comprehensive accessibility
<button
  onClick={handleClick}
  aria-label="Save changes"
  aria-describedby="save-description"
  disabled={isLoading}
>
  {isLoading ? <LoadingSpinner aria-hidden="true" /> : <SaveIcon aria-hidden="true" />}
  Save
</button>
<div id="save-description" className="sr-only">
  Save all changes to the current document
</div>
```

---

## Migration Checklist

### **MANDATORY**: Pre-Migration Checklist
- [ ] Identify all components to migrate
- [ ] Check ShadCN for available components
- [ ] Check existing reusable component library
- [ ] Plan migration order (tables → forms → buttons → layouts)
- [ ] Create backup of current implementation
- [ ] Set up testing environment

### **MANDATORY**: Migration Checklist
- [ ] Replace custom table components with ShadCN DataTable
- [ ] Replace custom form components with reusable form components
- [ ] Replace custom button components with reusable button components
- [ ] Replace custom layout components with reusable layout components
- [ ] Replace inline styles with Tailwind utilities
- [ ] Update all component imports
- [ ] Update all component tests
- [ ] Update component documentation

### **MANDATORY**: Post-Migration Checklist
- [ ] Run all tests and ensure they pass
- [ ] Test accessibility with screen readers
- [ ] Test keyboard navigation
- [ ] Test responsive design
- [ ] Test performance with large datasets
- [ ] Update component documentation
- [ ] Remove unused custom components
- [ ] Update migration guide with lessons learned

---

## Troubleshooting

### Common Migration Issues

#### Component Not Found
**Problem**: ShadCN component not available
**Solution**: Check ShadCN documentation, use existing reusable component, or create new reusable component

#### Styling Issues
**Problem**: Visual appearance changed after migration
**Solution**: Use Tailwind utilities to match original styling, check design system guidelines

#### Functionality Missing
**Problem**: ShadCN component doesn't have required functionality
**Solution**: Extend ShadCN component with custom props, or create specialized component

#### Performance Issues
**Problem**: Component performance degraded after migration
**Solution**: Use React.memo, useCallback, useMemo, and other optimization techniques

#### Test Failures
**Problem**: Tests failing after component migration
**Solution**: Update tests to match new component API, test new functionality

### Getting Help
- **Check ShadCN documentation**: https://ui.shadcn.com/
- **Check component library documentation**: `component-library.md`
- **Check design system guidelines**: `design-system-guidelines.md`
- **Review existing implementations**: Look at similar components in the codebase

---

## Migration Examples

### Complete Migration Example: Button Component

#### Before Migration
```tsx
// CustomButton.tsx
interface CustomButtonProps {
  variant: 'primary' | 'secondary' | 'danger';
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export const CustomButton = ({ variant, children, onClick, disabled, loading }: CustomButtonProps) => {
  const baseClasses = 'px-4 py-2 rounded font-medium transition-colors';
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
    danger: 'bg-red-600 text-white hover:bg-red-700'
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]}`}
      onClick={onClick}
      disabled={disabled || loading}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
};
```

#### After Migration
```tsx
// Using reusable button components
import { PrimaryButton, SecondaryButton, DangerButton } from '@/components/ui/reusable-buttons';

// Replace CustomButton usage with appropriate reusable component
<PrimaryButton onClick={handleSave} loading={isLoading}>
  Save
</PrimaryButton>

<SecondaryButton onClick={handleCancel}>
  Cancel
</SecondaryButton>

<DangerButton onClick={handleDelete} loading={isDeleting}>
  Delete
</DangerButton>
```

### Complete Migration Example: Form Component

#### Before Migration
```tsx
// CustomForm.tsx
interface CustomFormProps {
  onSubmit: (data: any) => void;
  children: React.ReactNode;
}

export const CustomForm = ({ onSubmit, children }: CustomFormProps) => {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {children}
    </form>
  );
};

// CustomInput.tsx
interface CustomInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export const CustomInput = ({ label, value, onChange, error }: CustomInputProps) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm ${
          error ? 'border-red-500' : ''
        }`}
      />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};
```

#### After Migration
```tsx
// Using reusable form components
import { FormContainer, FormField, TextInput, FormActions } from '@/components/ui/reusable-forms';
import { PrimaryButton, SecondaryButton } from '@/components/ui/reusable-buttons';

<FormContainer onSubmit={handleSubmit}>
  <FormField label="Name" error={errors.name} required>
    <TextInput
      value={name}
      onChange={setName}
      placeholder="Enter your name"
    />
  </FormField>
  
  <FormField label="Email" error={errors.email} required>
    <TextInput
      value={email}
      onChange={setEmail}
      type="email"
      placeholder="Enter your email"
    />
  </FormField>
  
  <FormActions>
    <PrimaryButton type="submit" loading={isSubmitting}>
      Submit
    </PrimaryButton>
    <SecondaryButton type="button" onClick={handleCancel}>
      Cancel
    </SecondaryButton>
  </FormActions>
</FormContainer>
```

---

## Conclusion

This migration guide provides a comprehensive approach to migrating existing components to use the **mandatory ShadCN + Tailwind first approach** and the new reusable component library.

**Key Principles**:
1. **Always check ShadCN first** - Use ShadCN components when available
2. **Use existing reusable components** - Leverage the component library
3. **Follow the migration hierarchy** - Tables → Forms → Buttons → Layouts
4. **Maintain accessibility** - Ensure all components meet WCAG guidelines
5. **Optimize for performance** - Use React optimization techniques
6. **Test thoroughly** - Ensure all functionality works correctly

**Remember**: The goal is to create a consistent, maintainable, and accessible component system that follows established design patterns and reduces development overhead.

---

**Note**: This migration guide should be updated as new components are added or existing components are modified. All component migration should follow these established guidelines. 