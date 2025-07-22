# Design System Guidelines

This document outlines the design system guidelines for the SOTD Pipeline WebUI, based on ShadCN UI components and Tailwind CSS.

---

**Note**: This document should be referenced when working on any webui components to ensure consistent design patterns and styling.

---

## Foundation Philosophy

### **MANDATORY**: ShadCN + Tailwind First
- **ALWAYS** use ShadCN components as the foundation for all UI development
- **ALWAYS** use Tailwind CSS for all styling and layout
- **NEVER** create custom components that duplicate ShadCN functionality
- **NEVER** use inline styles or custom CSS when Tailwind classes are available
- **STANDARDIZE** on ShadCN patterns and Tailwind utility classes

### Component Development Hierarchy
1. **Use ShadCN components** (Button, Input, Table, DataTable, etc.)
2. **Use existing reusable components** from our component library
3. **Use Tailwind utilities** for layout, spacing, colors, and styling
4. **Extend ShadCN components** with props/variants when needed
5. **Extend existing reusable components** with additional functionality
6. **Create custom components** only when ShadCN doesn't provide the functionality
7. **Document any deviations** from ShadCN/Tailwind patterns

### Component Reuse Standards
**MANDATORY**: Follow this hierarchy for all component development:

1. **Check ShadCN first** - Does ShadCN provide this component?
2. **Check existing reusable components** - Does our component library have something similar?
3. **Extend existing components** - Can I add props/variants to existing components?
4. **Create new reusable components** - Only when no suitable option exists
5. **Document new components** - Include usage examples and prop documentation

**Decision Framework:**
- ✅ **Create new component when**: ShadCN doesn't provide functionality, no existing component matches, component will be used in multiple places
- ❌ **Don't create new component when**: ShadCN already provides it, existing component can be extended, component is only used in one place

**Reference**: See `component-library.md` for comprehensive documentation of all reusable components.

### ShadCN Component Usage
```typescript
// ✅ CORRECT - Use ShadCN components
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { Input } from '@/components/ui/input';

// ✅ CORRECT - Extend ShadCN with variants
<Button variant="destructive" size="lg">Delete</Button>
<DataTable columns={columns} data={data} resizable={true} />

// ❌ WRONG - Don't create custom components that duplicate ShadCN
// Don't create CustomButton when ShadCN Button exists
// Don't create CustomTable when ShadCN DataTable exists
```

### Tailwind CSS Usage
```typescript
// ✅ CORRECT - Use Tailwind utilities
<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-sm">
  <h2 className="text-lg font-semibold text-gray-900">Title</h2>
  <Button className="bg-blue-600 hover:bg-blue-700">Action</Button>
</div>

// ❌ WRONG - Don't use inline styles or custom CSS
// Don't use style={{ display: 'flex', padding: '16px' }}
// Don't create custom CSS classes when Tailwind provides utilities
```

## Color Palette

### Primary Colors
- **Blue**: `blue-600` (#2563eb) - Primary actions, links
- **Blue Hover**: `blue-700` (#1d4ed8) - Hover states
- **Blue Light**: `blue-50` (#eff6ff) - Backgrounds, highlights

### Neutral Colors
- **Gray 50**: `gray-50` (#f9fafb) - Table headers, backgrounds
- **Gray 100**: `gray-100` (#f3f4f6) - Borders, dividers
- **Gray 200**: `gray-200` (#e5e7eb) - Borders, disabled states
- **Gray 500**: `gray-500` (#6b7280) - Secondary text
- **Gray 600**: `gray-600` (#4b5563) - Body text
- **Gray 700**: `gray-700` (#374151) - Headers, emphasis
- **Gray 900**: `gray-900` (#111827) - Primary text

### Status Colors
- **Success Green**: `green-600` (#16a34a) - Success states, matched items
- **Success Light**: `green-100` (#dcfce7) - Success backgrounds
- **Error Red**: `red-600` (#dc2626) - Error states, unmatched items
- **Error Light**: `red-100` (#fee2e2) - Error backgrounds
- **Warning Yellow**: `yellow-600` (#ca8a04) - Warning states
- **Warning Light**: `yellow-100` (#fef3c7) - Warning backgrounds

### Interactive Colors
- **Hover Blue**: `hover:bg-blue-50` - Row hover states
- **Focus Blue**: `focus:ring-blue-500` - Focus indicators
- **Active Blue**: `active:bg-blue-100` - Active states

## Typography

### Font Sizes
- **xs**: `text-xs` (12px) - Small labels, metadata
- **sm**: `text-sm` (14px) - Body text, table content
- **base**: `text-base` (16px) - Default text size
- **lg**: `text-lg` (18px) - Headers, emphasis
- **xl**: `text-xl` (20px) - Page titles
- **2xl**: `text-2xl` (24px) - Section headers

### Font Weights
- **Normal**: `font-normal` (400) - Body text
- **Medium**: `font-medium` (500) - Headers, emphasis
- **Semibold**: `font-semibold` (600) - Strong emphasis
- **Bold**: `font-bold` (700) - Page titles

### Text Colors
- **Primary**: `text-gray-900` - Main text
- **Secondary**: `text-gray-600` - Secondary text
- **Muted**: `text-gray-500` - Disabled, metadata
- **Inverted**: `text-white` - Text on dark backgrounds

## Spacing

### Padding
- **xs**: `p-1` (4px) - Tight spacing
- **sm**: `p-2` (8px) - Small spacing
- **md**: `p-3` (12px) - Standard spacing
- **lg**: `p-4` (16px) - Large spacing
- **xl**: `p-6` (24px) - Extra large spacing

### Margins
- **xs**: `m-1` (4px) - Tight margins
- **sm**: `m-2` (8px) - Small margins
- **md**: `m-3` (12px) - Standard margins
- **lg**: `m-4` (16px) - Large margins
- **xl**: `m-6` (24px) - Extra large margins

### Gaps
- **xs**: `gap-1` (4px) - Tight gaps
- **sm**: `gap-2` (8px) - Small gaps
- **md**: `gap-3` (12px) - Standard gaps
- **lg**: `gap-4` (16px) - Large gaps
- **xl**: `gap-6` (24px) - Extra large gaps

## Component Reuse Philosophy

### **MANDATORY**: Component Reuse First
- **ALWAYS** check existing components before creating new ones
- **PREFER** extending existing components over creating new ones
- **REQUIRE** justification for any new component that duplicates existing functionality
- **STANDARDIZE** on existing patterns rather than creating new ones

### Component Reuse Hierarchy
1. **Use existing ShadCN components** (Button, Input, Table, DataTable, etc.)
2. **Use existing custom components** (check what's already built)
3. **Extend existing components** with props/variants when possible
4. **Create new components** only when no suitable existing component exists
5. **Document reuse decisions** in component comments

### Reuse Decision Framework
Before creating any new component, ask:
- Does a ShadCN component handle this use case?
- Does an existing custom component handle this use case?
- Can an existing component be extended with props/variants?
- Is the new component significantly different from existing ones?
- Will this component be used in multiple places?
- Have I checked all existing components in the codebase?

## Table Component Standards

### **MANDATORY**: Use ShadCN DataTable
- **ALWAYS** use ShadCN DataTable as the foundation for all table components
- **NEVER** create custom table implementations that duplicate DataTable functionality
- **EXTEND** DataTable with specialized features (editing, subrows) when needed
- **LEVERAGE** TanStack Table features (sorting, filtering, resizing, virtualization)

### Table Component Architecture
```typescript
// ✅ CORRECT - Use ShadCN DataTable as foundation
import { DataTable } from '@/components/ui/data-table';

// Specialized table with editing features
const BrushSplitTable = (props) => {
  return <DataTable {...props} />; // Add editing logic on top
};

// Specialized table with subrow features  
const BrushTable = (props) => {
  return <DataTable {...props} />; // Add subrow logic on top
};

// ❌ WRONG - Don't create custom table implementations
// Don't create VirtualizedTable when DataTable supports virtualization
// Don't create GenericDataTable when DataTable provides all features
```

### ShadCN DataTable Features
- ✅ **Sorting** - Built-in column sorting
- ✅ **Filtering** - Global and column-specific filters  
- ✅ **Resizable columns** - Column width adjustment
- ✅ **Column visibility** - Show/hide columns
- ✅ **Row selection** - Checkbox selection
- ✅ **Virtualization** - For large datasets
- ✅ **Accessibility** - Built-in ARIA support
- ✅ **Performance** - Optimized with TanStack Table

### Basic Table Structure (for custom tables when needed)
```tsx
<div className="border rounded-lg">
  <div className="overflow-auto">
    <table className="w-full border-collapse">
      <thead className="bg-gray-50">
        <tr className="border-b">
          <th className="p-3 text-left font-medium text-gray-900">
            Header
          </th>
        </tr>
      </thead>
      <tbody>
        <tr className="border-b hover:bg-gray-50">
          <td className="p-3">Content</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

## Form Component Standards

### **MANDATORY**: Use ShadCN Form Components
- **ALWAYS** use ShadCN Input, Select, Checkbox, etc.
- **NEVER** create custom form components that duplicate ShadCN
- **EXTEND** ShadCN form components with validation and error handling
- **CONSISTENT** form patterns across all pages

### Form Patterns
```typescript
// ✅ CORRECT - Use ShadCN form components
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';

<form className="space-y-4">
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">
      Name
    </label>
    <Input 
      type="text" 
      placeholder="Enter your name"
      className="w-full"
    />
  </div>
  
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">
      Category
    </label>
    <Select>
      <SelectTrigger>
        <SelectValue placeholder="Select a category" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
      </SelectContent>
    </Select>
  </div>
</form>
```

### Button Patterns
```tsx
// Primary Button
<button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium">
  Primary Action
</button>

// Secondary Button
<button className="bg-gray-100 hover:bg-gray-200 text-gray-900 px-4 py-2 rounded-lg font-medium">
  Secondary Action
</button>

// Small Button
<button className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-sm">
  Small Action
</button>
```

### Input Patterns
```tsx
// Text Input
<input 
  className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
  placeholder="Enter text..."
/>

// Checkbox
<input 
  type="checkbox"
  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
/>
```

## Layout Component Standards

### **MANDATORY**: Use Tailwind Layout Utilities
- **ALWAYS** use Tailwind flexbox and grid utilities
- **NEVER** create custom layout components when Tailwind provides utilities
- **CONSISTENT** layout patterns across all pages
- **RESPONSIVE** design using Tailwind's responsive utilities

### Layout Patterns
```typescript
// ✅ CORRECT - Use Tailwind layout utilities
<div className="min-h-screen bg-gray-50">
  <div className="max-w-6xl mx-auto p-6">
    <header className="mb-8">
      <h1 className="text-3xl font-bold text-gray-900">Page Title</h1>
    </header>
    
    <main className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Section Title</h2>
        <p className="text-gray-600">Content here</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Another Section</h2>
        <p className="text-gray-600">More content</p>
      </div>
    </main>
  </div>
</div>
```

### Page Structure
```tsx
<div className="min-h-screen bg-gray-50">
  <header className="bg-white border-b border-gray-200 sticky top-0 z-20">
    <div className="max-w-7xl mx-auto px-4 py-4">
      <h1 className="text-xl font-semibold text-gray-900">Page Title</h1>
    </div>
  </header>
  
  <main className="max-w-7xl mx-auto px-4 py-6">
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Page content */}
    </div>
  </main>
</div>
```

### Card Layout
```tsx
<div className="bg-white rounded-lg border border-gray-200 p-6">
  <h2 className="text-lg font-semibold text-gray-900 mb-4">Card Title</h2>
  <div className="space-y-4">
    {/* Card content */}
  </div>
</div>
```

## Status Indicators

### Success Badge
```tsx
<span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
  Matched
</span>
```

### Error Badge
```tsx
<span className="text-xs text-red-600 bg-red-100 px-2 py-1 rounded">
  Unmatched
</span>
```

### Warning Badge
```tsx
<span className="text-xs text-yellow-600 bg-yellow-100 px-2 py-1 rounded">
  Pending
</span>
```

## Interactive States

### Hover States
- **Rows**: `hover:bg-gray-50`
- **Buttons**: `hover:bg-blue-700` (primary), `hover:bg-gray-200` (secondary)
- **Links**: `hover:text-blue-700`

### Focus States
- **Inputs**: `focus:ring-2 focus:ring-blue-500 focus:border-blue-500`
- **Buttons**: `focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`
- **Links**: `focus:outline-none focus:ring-2 focus:ring-blue-500`

### Active States
- **Buttons**: `active:bg-blue-800` (primary), `active:bg-gray-300` (secondary)
- **Rows**: `active:bg-gray-100`

### Disabled States
- **Inputs**: `disabled:opacity-50 disabled:cursor-not-allowed`
- **Buttons**: `disabled:opacity-50 disabled:cursor-not-allowed`

## Accessibility Standards

### **MANDATORY**: Follow WCAG 2.1 AA Guidelines
- **ALWAYS** use semantic HTML elements
- **ALWAYS** provide proper ARIA labels and descriptions
- **ALWAYS** ensure keyboard navigation works
- **ALWAYS** maintain proper color contrast ratios
- **ALWAYS** test with screen readers

### Accessibility Patterns
```typescript
// ✅ CORRECT - Accessible components
<Button 
  aria-label="Delete item"
  aria-describedby="delete-description"
  onClick={handleDelete}
>
  Delete
</Button>
<span id="delete-description" className="sr-only">
  Permanently delete this item from the system
</span>

// ✅ CORRECT - Semantic HTML
<main role="main" aria-label="Main content">
  <section aria-labelledby="section-title">
    <h2 id="section-title">Section Title</h2>
    <p>Content here</p>
  </section>
</main>
```

### ARIA Labels
```tsx
<button aria-label="Sort by name">
  Name ↑
</button>
```

### Keyboard Navigation
```tsx
<button 
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>
  Clickable Element
</button>
```

### Focus Management
```tsx
<div tabIndex={0} onFocus={handleFocus} onBlur={handleBlur}>
  Focusable Content
</div>
```

### Screen Reader Support
```tsx
<span className="sr-only">Hidden text for screen readers</span>
```

## Performance Standards

### **MANDATORY**: Optimize for Performance
- **ALWAYS** use React.memo for expensive components
- **ALWAYS** use useMemo and useCallback for expensive operations
- **ALWAYS** implement proper loading states
- **ALWAYS** handle error states gracefully
- **ALWAYS** optimize bundle size

### Performance Patterns
```typescript
// ✅ CORRECT - Optimized components
const ExpensiveComponent = React.memo(({ data }) => {
  const processedData = useMemo(() => {
    return data.map(item => ({ ...item, processed: true }));
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

### Loading States
```tsx
{loading ? (
  <div className="flex items-center justify-center p-8">
    <div className="text-gray-500">Loading...</div>
  </div>
) : (
  // Content
)}
```

### Empty States
```tsx
{data.length === 0 ? (
  <div className="flex items-center justify-center p-8">
    <div className="text-gray-500">No data available</div>
  </div>
) : (
  // Content
)}
```

## Responsive Design

### Breakpoints
- **sm**: 640px - Small screens
- **md**: 768px - Medium screens
- **lg**: 1024px - Large screens
- **xl**: 1280px - Extra large screens
- **2xl**: 1536px - 2X large screens

### Responsive Patterns
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Responsive grid */}
</div>

<div className="text-sm md:text-base lg:text-lg">
  {/* Responsive typography */}
</div>

<div className="p-4 md:p-6 lg:p-8">
  {/* Responsive spacing */}
</div>
```

## Development Workflow

### **MANDATORY**: Follow Component Reuse Process
1. **Check ShadCN** - Does ShadCN provide this component?
2. **Check existing custom components** - Does something similar exist?
3. **Extend existing component** - Can I add props/variants?
4. **Create new component** - Only if no suitable option exists
5. **Document decision** - Why was this component created?

### Code Review Checklist
- [ ] Uses ShadCN components where available
- [ ] Uses Tailwind utilities for styling
- [ ] Follows accessibility guidelines
- [ ] Implements proper error handling
- [ ] Includes comprehensive tests
- [ ] Documents component usage
- [ ] Optimizes for performance

## Migration Guidelines

### **MANDATORY**: Migrate to ShadCN + Tailwind
- **IMMEDIATE**: Replace custom table implementations with ShadCN DataTable
- **IMMEDIATE**: Replace inline styles with Tailwind utilities
- **IMMEDIATE**: Replace custom form components with ShadCN form components
- **GRADUAL**: Update existing components to use ShadCN patterns
- **ONGOING**: Maintain consistency with ShadCN + Tailwind standards

### Migration Priority
1. **High Priority**: Table components (migrate to ShadCN DataTable)
2. **High Priority**: Form components (migrate to ShadCN form components)
3. **Medium Priority**: Layout components (use Tailwind utilities)
4. **Medium Priority**: Button and input components (use ShadCN)
5. **Low Priority**: Specialized components (extend ShadCN when possible)

## Best Practices

### Naming Conventions
- Use descriptive class names
- Group related styles together
- Use consistent naming patterns

### Code Organization
- Keep components focused and single-purpose
- Use consistent file structure
- Document complex logic

### Testing
- Test all interactive states
- Test accessibility features
- Test responsive behavior
- Test performance with large datasets

### Maintenance
- Keep design system up to date
- Document changes and decisions
- Review and refactor regularly
- Monitor performance metrics

---

**Note**: This document should be updated as new design patterns emerge and lessons are learned. All webui development should follow these established design system guidelines, with ShadCN + Tailwind as the primary foundation. 