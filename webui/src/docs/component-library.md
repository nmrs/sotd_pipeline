# Component Library Documentation

This document provides comprehensive documentation for all reusable components in the SOTD Pipeline WebUI, following the **mandatory ShadCN + Tailwind first approach**.

---

## Table of Contents

1. [Reusable Button Components](#reusable-button-components)
2. [Reusable Form Components](#reusable-form-components)
3. [Reusable Layout Components](#reusable-layout-components)
4. [Specialized Table Components](#specialized-table-components)
5. [Component Reuse Standards](#component-reuse-standards)
6. [Accessibility Guidelines](#accessibility-guidelines)
7. [Performance Guidelines](#performance-guidelines)

---

## Reusable Button Components

### PrimaryButton
**Purpose**: Primary actions and main user interactions
**Foundation**: ShadCN Button with `variant="default"`

```tsx
import { PrimaryButton } from '@/components/ui/reusable-buttons';

<PrimaryButton 
  onClick={handleSave}
  disabled={isLoading}
  loading={isLoading}
>
  Save Changes
</PrimaryButton>
```

**Props**:
- `children`: React.ReactNode - Button content
- `onClick`: () => void - Click handler
- `disabled`: boolean - Disabled state
- `loading`: boolean - Loading state with spinner
- `className`: string - Additional CSS classes

**Accessibility**: Includes proper ARIA attributes, keyboard navigation, and focus management

### SecondaryButton
**Purpose**: Secondary actions and alternative choices
**Foundation**: ShadCN Button with `variant="outline"`

```tsx
import { SecondaryButton } from '@/components/ui/reusable-buttons';

<SecondaryButton 
  onClick={handleCancel}
  disabled={isProcessing}
>
  Cancel
</SecondaryButton>
```

**Props**: Same as PrimaryButton

### DangerButton
**Purpose**: Destructive actions and warnings
**Foundation**: ShadCN Button with `variant="destructive"`

```tsx
import { DangerButton } from '@/components/ui/reusable-buttons';

<DangerButton 
  onClick={handleDelete}
  loading={isDeleting}
>
  Delete Item
</DangerButton>
```

**Props**: Same as PrimaryButton

### SuccessButton
**Purpose**: Positive actions and confirmations
**Foundation**: ShadCN Button with custom green styling

```tsx
import { SuccessButton } from '@/components/ui/reusable-buttons';

<SuccessButton 
  onClick={handleConfirm}
  loading={isConfirming}
>
  Confirm
</SuccessButton>
```

**Props**: Same as PrimaryButton

### IconButton
**Purpose**: Icon-only actions and toolbar buttons
**Foundation**: ShadCN Button with icon support

```tsx
import { IconButton } from '@/components/ui/reusable-buttons';
import { Plus, Edit, Trash } from 'lucide-react';

<IconButton 
  onClick={handleAdd}
  icon={<Plus className="w-4 h-4" />}
  title="Add new item"
>
  Add
</IconButton>
```

**Props**:
- `icon`: React.ReactNode - Icon element
- `title`: string - Tooltip text
- All other props from PrimaryButton

---

## Reusable Form Components

### FormField
**Purpose**: Wrapper for form inputs with labels and error handling
**Foundation**: ShadCN form patterns

```tsx
import { FormField } from '@/components/ui/reusable-forms';

<FormField
  label="Email Address"
  error={errors.email}
  required
>
  <TextInput
    value={email}
    onChange={setEmail}
    placeholder="Enter your email"
    type="email"
  />
</FormField>
```

**Props**:
- `label`: string - Field label
- `error`: string | undefined - Error message
- `required`: boolean - Required field indicator
- `children`: React.ReactNode - Input component

### TextInput
**Purpose**: Text input fields with validation
**Foundation**: ShadCN Input component

```tsx
import { TextInput } from '@/components/ui/reusable-forms';

<TextInput
  value={value}
  onChange={setValue}
  placeholder="Enter text"
  type="text"
  error={errors.field}
  disabled={isLoading}
/>
```

**Props**:
- `value`: string - Input value
- `onChange`: (value: string) => void - Change handler
- `placeholder`: string - Placeholder text
- `type`: string - Input type (text, email, password, etc.)
- `error`: string | undefined - Error message
- `disabled`: boolean - Disabled state
- `className`: string - Additional CSS classes

### SelectInput
**Purpose**: Dropdown selection with options
**Foundation**: ShadCN Select component

```tsx
import { SelectInput } from '@/components/ui/reusable-forms';

<SelectInput
  value={selectedValue}
  onChange={setSelectedValue}
  options={[
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' }
  ]}
  placeholder="Select an option"
  error={errors.selection}
/>
```

**Props**:
- `value`: string - Selected value
- `onChange`: (value: string) => void - Change handler
- `options`: Array<{value: string, label: string}> - Available options
- `placeholder`: string - Placeholder text
- `error`: string | undefined - Error message
- `disabled`: boolean - Disabled state

### CheckboxInput
**Purpose**: Checkbox with label and validation
**Foundation**: ShadCN Checkbox component

```tsx
import { CheckboxInput } from '@/components/ui/reusable-forms';

<CheckboxInput
  checked={isChecked}
  onChange={setIsChecked}
  label="Accept terms and conditions"
  error={errors.terms}
/>
```

**Props**:
- `checked`: boolean - Checked state
- `onChange`: (checked: boolean) => void - Change handler
- `label`: string - Checkbox label
- `error`: string | undefined - Error message
- `disabled`: boolean - Disabled state

### SearchInput
**Purpose**: Search input with debounced functionality
**Foundation**: ShadCN Input with search icon

```tsx
import { SearchInput } from '@/components/ui/reusable-forms';

<SearchInput
  value={searchTerm}
  onChange={setSearchTerm}
  placeholder="Search items..."
  onSearch={handleSearch}
  debounceMs={300}
/>
```

**Props**:
- `value`: string - Search value
- `onChange`: (value: string) => void - Change handler
- `placeholder`: string - Placeholder text
- `onSearch`: (value: string) => void - Search handler
- `debounceMs`: number - Debounce delay in milliseconds

### FormContainer
**Purpose**: Container for form elements with consistent spacing
**Foundation**: Tailwind utilities

```tsx
import { FormContainer } from '@/components/ui/reusable-forms';

<FormContainer onSubmit={handleSubmit}>
  <FormField label="Name" error={errors.name}>
    <TextInput value={name} onChange={setName} />
  </FormField>
  <FormField label="Email" error={errors.email}>
    <TextInput value={email} onChange={setEmail} type="email" />
  </FormField>
  <FormActions>
    <PrimaryButton type="submit">Submit</PrimaryButton>
    <SecondaryButton type="button" onClick={handleCancel}>Cancel</SecondaryButton>
  </FormActions>
</FormContainer>
```

**Props**:
- `onSubmit`: (e: FormEvent) => void - Form submit handler
- `children`: React.ReactNode - Form fields and actions

### FormActions
**Purpose**: Container for form action buttons
**Foundation**: Tailwind utilities

```tsx
import { FormActions } from '@/components/ui/reusable-forms';

<FormActions>
  <PrimaryButton type="submit">Save</PrimaryButton>
  <SecondaryButton type="button" onClick={handleCancel}>Cancel</SecondaryButton>
</FormActions>
```

**Props**:
- `children`: React.ReactNode - Action buttons

---

## Reusable Layout Components

### PageLayout
**Purpose**: Standard page layout with consistent structure
**Foundation**: Tailwind utilities

```tsx
import { PageLayout } from '@/components/ui/reusable-layout';

<PageLayout title="Dashboard" subtitle="Overview of your data">
  <div>Page content goes here</div>
</PageLayout>
```

**Props**:
- `title`: string - Page title
- `subtitle`: string - Page subtitle
- `children`: React.ReactNode - Page content

### CardLayout
**Purpose**: Card container for content sections
**Foundation**: Tailwind utilities with ShadCN Card patterns

```tsx
import { CardLayout } from '@/components/ui/reusable-layout';

<CardLayout title="User Information" subtitle="Personal details">
  <div>Card content goes here</div>
</CardLayout>
```

**Props**:
- `title`: string - Card title
- `subtitle`: string - Card subtitle
- `children`: React.ReactNode - Card content

### SectionLayout
**Purpose**: Section container with consistent spacing
**Foundation**: Tailwind utilities

```tsx
import { SectionLayout } from '@/components/ui/reusable-layout';

<SectionLayout title="Data Analysis" description="Review your data insights">
  <div>Section content goes here</div>
</SectionLayout>
```

**Props**:
- `title`: string - Section title
- `description`: string - Section description
- `children`: React.ReactNode - Section content

### GridLayout
**Purpose**: Responsive grid layout
**Foundation**: Tailwind grid utilities

```tsx
import { GridLayout } from '@/components/ui/reusable-layout';

<GridLayout cols={3} gap={4}>
  <div>Grid item 1</div>
  <div>Grid item 2</div>
  <div>Grid item 3</div>
</GridLayout>
```

**Props**:
- `cols`: number - Number of columns (1-12)
- `gap`: number - Gap between items (1-8)
- `children`: React.ReactNode - Grid items

### FlexLayout
**Purpose**: Flexible layout container
**Foundation**: Tailwind flex utilities

```tsx
import { FlexLayout } from '@/components/ui/reusable-layout';

<FlexLayout direction="row" justify="between" align="center">
  <div>Left content</div>
  <div>Right content</div>
</FlexLayout>
```

**Props**:
- `direction`: 'row' | 'col' - Flex direction
- `justify`: 'start' | 'end' | 'center' | 'between' | 'around' - Justify content
- `align`: 'start' | 'end' | 'center' | 'stretch' - Align items
- `children`: React.ReactNode - Flex items

### StatusCard
**Purpose**: Status indicator with icon and message
**Foundation**: Tailwind utilities with Lucide icons

```tsx
import { StatusCard } from '@/components/ui/reusable-layout';

<StatusCard
  type="success"
  title="Data Updated"
  message="Your data has been successfully updated"
  icon={<CheckCircle className="w-5 h-5" />}
/>
```

**Props**:
- `type`: 'success' | 'error' | 'warning' | 'info' - Status type
- `title`: string - Status title
- `message`: string - Status message
- `icon`: React.ReactNode - Status icon

### LoadingContainer
**Purpose**: Loading state with spinner and message
**Foundation**: Tailwind utilities with loading spinner

```tsx
import { LoadingContainer } from '@/components/ui/reusable-layout';

<LoadingContainer
  isLoading={isLoading}
  message="Loading data..."
  size="lg"
>
  <div>Content that shows when not loading</div>
</LoadingContainer>
```

**Props**:
- `isLoading`: boolean - Loading state
- `message`: string - Loading message
- `size`: 'sm' | 'md' | 'lg' - Spinner size
- `children`: React.ReactNode - Content to show when not loading

### EmptyState
**Purpose**: Empty state with icon and message
**Foundation**: Tailwind utilities with Lucide icons

```tsx
import { EmptyState } from '@/components/ui/reusable-layout';

<EmptyState
  icon={<Inbox className="w-12 h-12" />}
  title="No Data Found"
  message="There are no items to display"
  action={<PrimaryButton onClick={handleAdd}>Add Item</PrimaryButton>}
/>
```

**Props**:
- `icon`: React.ReactNode - Empty state icon
- `title`: string - Empty state title
- `message`: string - Empty state message
- `action`: React.ReactNode - Action button

---

## Specialized Table Components

### BrushSplitDataTable
**Purpose**: Data table for brush split validation with inline editing
**Foundation**: ShadCN DataTable with specialized editing functionality

```tsx
import { BrushSplitDataTable } from '@/components/data/BrushSplitDataTable';

<BrushSplitDataTable
  brushSplits={brushSplits}
  onSave={handleSave}
  onSelectionChange={handleSelectionChange}
  selectedIndices={selectedIndices}
/>
```

**Props**:
- `brushSplits`: BrushSplit[] - Array of brush split data
- `onSave`: (index: number, updatedSplit: BrushSplit) => void - Save handler
- `onSelectionChange`: (selectedIndices: number[]) => void - Selection handler
- `selectedIndices`: number[] - Currently selected indices

### UnmatchedAnalyzerDataTable
**Purpose**: Data table for unmatched analyzer with filtering and virtualization
**Foundation**: ShadCN DataTable with virtualization and filtering

```tsx
import { UnmatchedAnalyzerDataTable } from '@/components/data/UnmatchedAnalyzerDataTable';

<UnmatchedAnalyzerDataTable
  data={unmatchedData}
  filteredStatus={filteredStatus}
  pendingChanges={pendingChanges}
  onFilteredStatusChange={handleFilteredStatusChange}
  onCommentClick={handleCommentClick}
  commentLoading={commentLoading}
  fieldType="brush"
  columnWidths={columnWidths}
/>
```

**Props**:
- `data`: UnmatchedItem[] - Array of unmatched items
- `filteredStatus`: Record<string, boolean> - Filter status for each item
- `pendingChanges`: Record<string, boolean> - Pending changes
- `onFilteredStatusChange`: (itemName: string, isFiltered: boolean) => void - Filter change handler
- `onCommentClick`: (commentId: string) => void - Comment click handler
- `commentLoading`: boolean - Comment loading state
- `fieldType`: 'razor' | 'blade' | 'soap' | 'brush' - Field type
- `columnWidths`: object - Column width configuration

### PerformanceDataTable
**Purpose**: Data table for performance metrics with monitoring
**Foundation**: ShadCN DataTable with performance monitoring

```tsx
import { PerformanceDataTable } from '@/components/data/PerformanceDataTable';

<PerformanceDataTable
  data={performanceData}
/>
```

**Props**:
- `data`: TestData[] - Array of performance data

### BrushDataTable
**Purpose**: Data table for brush data with hierarchical subrows
**Foundation**: ShadCN DataTable with subrow expansion

```tsx
import { BrushDataTable } from '@/components/data/BrushDataTable';

<BrushDataTable
  data={brushData}
/>
```

**Props**:
- `data`: BrushData[] - Array of brush data with subrows

---

## Component Reuse Standards

### **MANDATORY**: Component Reuse Hierarchy
1. **Use ShadCN components** - Always check ShadCN first
2. **Use existing reusable components** - Check our component library
3. **Extend existing components** - Add props/variants when possible
4. **Create new reusable components** - Only when no suitable option exists
5. **Document new components** - Include usage examples and prop documentation

### Decision Framework
**When to create a new component:**
- ✅ ShadCN doesn't provide the functionality
- ✅ No existing reusable component matches the use case
- ✅ The component will be used in multiple places
- ✅ The component has complex logic that should be encapsulated

**When NOT to create a new component:**
- ❌ ShadCN already provides the functionality
- ❌ An existing reusable component can be extended
- ❌ The component is only used in one place
- ❌ The component is just a simple wrapper

### Component Development Process
1. **Check ShadCN** - Does ShadCN provide this component?
2. **Check existing components** - Does something similar exist?
3. **Extend existing component** - Can I add props/variants?
4. **Create new component** - Only if no suitable option exists
5. **Write comprehensive tests** - Test all functionality and edge cases
6. **Document the component** - Include usage examples and prop documentation
7. **Update this documentation** - Add to component library

### Code Review Checklist
- [ ] Uses ShadCN components where available
- [ ] Uses existing reusable components when possible
- [ ] Extends existing components before creating new ones
- [ ] Includes comprehensive tests
- [ ] Documents component usage and props
- [ ] Follows accessibility guidelines
- [ ] Optimizes for performance
- [ ] Uses consistent naming conventions

---

## Accessibility Guidelines

### **MANDATORY**: Accessibility Requirements
- **ARIA attributes** - Include proper ARIA labels and descriptions
- **Keyboard navigation** - All interactive elements must be keyboard accessible
- **Focus management** - Proper focus indicators and focus order
- **Screen reader support** - Semantic HTML and proper text alternatives
- **Color contrast** - Meet WCAG 2.1 AA contrast requirements

### ARIA Implementation
```tsx
// ✅ CORRECT - Proper ARIA attributes
<button
  aria-label="Delete item"
  aria-describedby="delete-description"
  onClick={handleDelete}
>
  <Trash className="w-4 h-4" />
</button>
<div id="delete-description" className="sr-only">
  Permanently delete this item from the system
</div>

// ✅ CORRECT - Semantic HTML
<nav aria-label="Main navigation">
  <ul role="menubar">
    <li role="menuitem">Home</li>
    <li role="menuitem">About</li>
  </ul>
</nav>
```

### Keyboard Navigation
```tsx
// ✅ CORRECT - Keyboard accessible
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
  onClick={handleClick}
>
  Clickable content
</div>
```

### Focus Management
```tsx
// ✅ CORRECT - Proper focus management
const [isOpen, setIsOpen] = useState(false);
const triggerRef = useRef<HTMLButtonElement>(null);

const handleClose = () => {
  setIsOpen(false);
  triggerRef.current?.focus();
};
```

### Color and Contrast
- **Primary text**: `text-gray-900` (#111827) - High contrast
- **Secondary text**: `text-gray-600` (#4b5563) - Medium contrast
- **Disabled text**: `text-gray-400` (#9ca3af) - Low contrast
- **Background**: `bg-white` (#ffffff) - High contrast
- **Borders**: `border-gray-200` (#e5e7eb) - Medium contrast

---

## Performance Guidelines

### **MANDATORY**: Performance Requirements
- **Render time**: <16ms for interactive components
- **Bundle size**: Minimize component bundle impact
- **Memory usage**: Efficient memory management for large datasets
- **Interaction responsiveness**: <100ms for user interactions

### Optimization Techniques
```tsx
// ✅ CORRECT - Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* Expensive rendering logic */}</div>;
});

// ✅ CORRECT - Use useCallback for event handlers
const handleClick = useCallback(() => {
  // Handler logic
}, [dependencies]);

// ✅ CORRECT - Use useMemo for expensive calculations
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);
```

### Virtualization for Large Datasets
```tsx
// ✅ CORRECT - Use virtualization for large lists
import { FixedSizeList as List } from 'react-window';

const VirtualizedList = ({ items }) => (
  <List
    height={400}
    itemCount={items.length}
    itemSize={50}
    itemData={items}
  >
    {({ index, style, data }) => (
      <div style={style}>
        {data[index]}
      </div>
    )}
  </List>
);
```

### Lazy Loading
```tsx
// ✅ CORRECT - Lazy load non-critical components
const LazyComponent = lazy(() => import('./LazyComponent'));

const App = () => (
  <Suspense fallback={<LoadingSpinner />}>
    <LazyComponent />
  </Suspense>
);
```

### Bundle Optimization
```tsx
// ✅ CORRECT - Import only what you need
import { Button } from '@/components/ui/button';
import { CheckCircle } from 'lucide-react';

// ❌ WRONG - Import entire library
import * as LucideIcons from 'lucide-react';
```

---

## Testing Guidelines

### **MANDATORY**: Testing Requirements
- **Unit tests**: Test all component functionality
- **Integration tests**: Test component interactions
- **Accessibility tests**: Test keyboard navigation and screen readers
- **Performance tests**: Test rendering and interaction performance

### Test Structure
```tsx
// ✅ CORRECT - Comprehensive test structure
describe('ComponentName', () => {
  describe('Rendering', () => {
    test('renders correctly with all props', () => {
      // Test basic rendering
    });
    
    test('renders correctly with minimal props', () => {
      // Test with minimal props
    });
  });

  describe('Interactions', () => {
    test('handles click events', () => {
      // Test click handling
    });
    
    test('handles keyboard events', () => {
      // Test keyboard navigation
    });
  });

  describe('Accessibility', () => {
    test('supports keyboard navigation', () => {
      // Test keyboard accessibility
    });
    
    test('has proper ARIA attributes', () => {
      // Test ARIA compliance
    });
  });

  describe('Edge Cases', () => {
    test('handles empty data gracefully', () => {
      // Test empty state
    });
    
    test('handles malformed data gracefully', () => {
      // Test error handling
    });
  });
});
```

### Performance Testing
```tsx
// ✅ CORRECT - Performance testing
test('renders large dataset efficiently', () => {
  const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
    id: i,
    name: `Item ${i}`
  }));

  const startTime = performance.now();
  render(<Component data={largeDataset} />);
  const endTime = performance.now();

  expect(endTime - startTime).toBeLessThan(100);
});
```

---

## Migration Guide

### **MANDATORY**: Migration Process
1. **Identify components to migrate** - List all components that need updating
2. **Check ShadCN alternatives** - Find ShadCN components that can replace custom ones
3. **Update component usage** - Replace custom components with ShadCN equivalents
4. **Update tests** - Ensure all tests pass with new components
5. **Update documentation** - Update component documentation
6. **Remove old components** - Delete unused custom components

### Migration Examples
```tsx
// ❌ OLD - Custom button component
import { CustomButton } from './CustomButton';
<CustomButton onClick={handleClick}>Click me</CustomButton>

// ✅ NEW - ShadCN button component
import { Button } from '@/components/ui/button';
<Button onClick={handleClick}>Click me</Button>

// ❌ OLD - Custom table component
import { CustomTable } from './CustomTable';
<CustomTable data={data} columns={columns} />

// ✅ NEW - ShadCN DataTable component
import { DataTable } from '@/components/ui/data-table';
<DataTable data={data} columns={columns} />
```

### Compatibility Notes
- **Breaking changes**: Some prop names may change when migrating to ShadCN
- **Styling changes**: Visual appearance may change slightly
- **Behavior changes**: Some interactive behaviors may be different
- **Testing updates**: Tests may need updates for new component APIs

### Troubleshooting
- **Component not found**: Check if ShadCN provides the component
- **Styling issues**: Use Tailwind utilities instead of custom CSS
- **Functionality missing**: Extend ShadCN components with custom props
- **Performance issues**: Use React.memo and other optimization techniques

---

## Conclusion

This component library provides a comprehensive set of reusable components that follow the **mandatory ShadCN + Tailwind first approach**. All components are designed to be:

- **Consistent** - Following established design patterns
- **Accessible** - Meeting WCAG 2.1 AA guidelines
- **Performant** - Optimized for speed and efficiency
- **Maintainable** - Well-documented and tested
- **Reusable** - Designed for multiple use cases

**Remember**: Always check ShadCN first, then existing reusable components, before creating new components. This ensures consistency and reduces maintenance overhead.

---

**Note**: This documentation should be updated as new components are added or existing components are modified. All component development should follow these established guidelines. 