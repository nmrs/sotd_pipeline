## 🎨 UI Component Patterns

### ShadCN UI Components
- **Prefer ShadCN components** over native HTML elements
- **Use consistent styling** across all form components
- **Maintain accessibility** with proper ARIA attributes
- **Handle component behavior** in tests (e.g., checkbox states, input values)
- **NEVER create custom components** that duplicate ShadCN functionality

### Form Patterns
```typescript
// Controlled Component Pattern
const [value, setValue] = useState('');
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
};

// Form Validation Pattern
const [errors, setErrors] = useState<Record<string, string>>({});
const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!value.trim()) {
        newErrors.value = 'This field is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
};
```

### Table Patterns
```typescript
// ShadCN DataTable Pattern - ALWAYS use this
import { DataTable } from '@/components/ui/data-table';

interface Column<T> {
    key: string;
    header: string;
    render?: (value: any, row: T) => React.ReactNode;
}

interface DataTableProps<T> {
    data: T[];
    columns: Column<T>[];
    onSort?: (key: string) => void;
    onSelect?: (selected: T[]) => void;
}

// ✅ CORRECT - Use ShadCN DataTable
<DataTable 
    columns={columns} 
    data={data} 
    resizable={true}
    searchKey="name"
    showColumnVisibility={true}
/>

// ❌ WRONG - Don't create custom table implementations
// Don't create VirtualizedTable when DataTable supports virtualization
// Don't create GenericDataTable when DataTable provides all features
```

## 🔧 Utility Patterns

### Data Transformation
```typescript
// Generic Transformer Pattern
interface Transformer<T, U> {
    transform: (data: T) => U;
    validate?: (data: T) => boolean;
}

// Usage Pattern
const brushTransformer: Transformer<BrushData, TransformedBrush> = {
    transform: (data) => ({
        // transformation logic
    }),
    validate: (data) => {
        // validation logic
        return true;
    }
};
```

### API Service Patterns
```typescript
// API Service Pattern
interface ApiService {
    get: <T>(url: string) => Promise<T>;
    post: <T>(url: string, data: any) => Promise<T>;
    put: <T>(url: string, data: any) => Promise<T>;
    delete: <T>(url: string) => Promise<T>;
}

// Error Handling Pattern
const handleApiError = (error: any) => {
    console.warn('API Error:', error);
    // Don't show error to user, just log it
};
```

### Test Utility Patterns
```typescript
// Test Utility Pattern
export const createMockApi = (data: any, error?: Error) => ({
    get: jest.fn().mockResolvedValue(data),
    post: jest.fn().mockResolvedValue(data),
    put: jest.fn().mockResolvedValue(data),
    delete: jest.fn().mockResolvedValue(data)
});

export const createMockMonths = (months: string[]) => 
    months.map(month => ({ value: month, label: month }));
```

## 🚫 Anti-Patterns to Avoid

### Testing Anti-Patterns
- ❌ **Don't test implementation details** - test behavior, not internal state
- ❌ **Don't use complex mocks** - prefer simple, predictable mocks
- ❌ **Don't test multiple concerns** in a single test
- ❌ **Don't write to production files** during testing

### Component Anti-Patterns
- ❌ **Don't create custom components** that duplicate ShadCN functionality
- ❌ **Don't use inline styles** - use Tailwind utility classes
- ❌ **Don't ignore accessibility** - always include proper ARIA attributes
- ❌ **Don't use any type** - always define proper TypeScript types
- ❌ **Don't create custom table implementations** - use ShadCN DataTable

### State Management Anti-Patterns
- ❌ **Don't mutate state directly** - use immutable update patterns
- ❌ **Don't store derived state** - compute it when needed
- ❌ **Don't pass props through multiple levels** - use context for deep prop drilling

## 📋 Development Workflow

### Pre-Development Checklist
- [ ] Check if ShadCN provides the component you need
- [ ] Check if existing custom components handle your use case
- [ ] Plan component hierarchy and data flow
- [ ] Identify test scenarios and edge cases
- [ ] Consider accessibility requirements

### Development Process
1. **Check ShadCN first** - Does ShadCN provide this component?
2. **Check existing components** - Does something similar exist?
3. **Extend existing component** - Can I add props/variants?
4. **Write tests first** (TDD approach)
5. **Implement minimal functionality** to make tests pass
6. **Refactor for clarity** and maintainability
7. **Add comprehensive tests** for edge cases
8. **Verify accessibility** and user experience

### Quality Checks
- [ ] All tests passing (153/153 React tests)
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] Uses ShadCN components where available
- [ ] Uses Tailwind utilities for styling
- [ ] Accessibility requirements met
- [ ] No production data files modified

## 🎯 Component-Specific Patterns

### Form Components
- **Use ShadCN form components** (Input, Select, Checkbox, etc.)
- **Use controlled components** with state management
- **Implement proper validation** and error handling
- **Provide clear user feedback** for all interactions
- **Support keyboard navigation** and screen readers

### Table Components
- **ALWAYS use ShadCN DataTable** as the foundation
- **Extend DataTable** with specialized features (editing, subrows)
- **Leverage TanStack Table features** (sorting, filtering, resizing, virtualization)
- **NEVER create custom table implementations** that duplicate DataTable functionality

### Modal/Dialog Components
- **Use ShadCN Dialog components** when available
- **Use proper focus management**
- **Implement escape key handling**
- **Provide clear close actions**
- **Prevent background scrolling**

### Navigation Components
- **Use consistent navigation patterns**
- **Implement proper active state handling**
- **Support keyboard navigation**
- **Provide clear visual feedback**

## 🔍 Debugging Patterns

### Console Logging
```typescript
// Debug Pattern
console.log('Component received data:', data);
console.log('API response:', response);
console.warn('Non-critical error:', error);
```

### Error Boundaries
```typescript
// Error Boundary Pattern
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return <div>Something went wrong.</div>;
        }
        return this.props.children;
    }
}
```

## 📚 Documentation Requirements

### Code Comments
- Document complex business logic
- Explain non-obvious component behavior
- Document API integration patterns
- Include usage examples for reusable components

### README Updates
- Update component documentation when interfaces change
- Document new utility functions and patterns
- Include setup instructions for new developers
- Maintain changelog for breaking changes

## 🚀 Performance Patterns

### Optimization Techniques
- Use React.memo for expensive components
- Implement proper dependency arrays in useEffect
- Use useCallback for event handlers passed to children
- Use useMemo for expensive calculations

### Bundle Optimization
- Lazy load non-critical components
- Use dynamic imports for large dependencies
- Optimize images and assets
- Minimize bundle size with tree shaking

## 🔒 Security Patterns

### Input Validation
- Validate all user inputs on both client and server
- Sanitize data before rendering
- Use proper Content Security Policy headers
- Implement proper authentication and authorization

### Data Protection
- Never expose sensitive data in client-side code
- Use HTTPS for all API communications
- Implement proper session management
- Follow OWASP security guidelines

## 📈 Monitoring and Analytics

### Error Tracking
- Implement error boundaries for graceful error handling
- Log errors to monitoring service
- Track user interactions for debugging
- Monitor performance metrics

### User Analytics
- Track key user interactions
- Monitor component usage patterns
- Measure performance impact of changes
- Use analytics to inform UX improvements

## 🎨 Design System

### Design System Guidelines
- **Reference**: `@design-system-guidelines.mdc` for comprehensive design system guidelines
- **Foundation**: ShadCN + Tailwind as the primary UI foundation
- **Coverage**: Color palette, typography, spacing, component patterns, interactive states, accessibility guidelines, performance guidelines, responsive design patterns
- **Usage**: Follow established patterns from the design system guidelines for all webui development

### Consistent Styling
- **Use ShadCN UI components** for consistency
- **Follow established color palette** and typography from design system guidelines
- **Use Tailwind utility classes** for all styling and layout
- **Maintain consistent spacing** and layout
- **Use proper semantic HTML elements**

### Accessibility Standards
- Follow WCAG 2.1 AA guidelines
- Implement proper ARIA attributes
- Support keyboard navigation
- Provide alternative text for images

## 🔄 Migration Patterns

### Component Migration
- Migrate one component at a time
- Maintain backward compatibility during migration
- Update tests to match new component behavior
- Document breaking changes

### Library Updates
- Test thoroughly after dependency updates
- Update TypeScript types when needed
- Verify all tests pass after updates
- Document any breaking changes

## 📝 Code Review Checklist

### Functionality
- [ ] All requirements implemented
- [ ] Edge cases handled
- [ ] Error states managed
- [ ] Loading states implemented

### Code Quality
- [ ] TypeScript types properly defined
- [ ] No linting errors
- [ ] Code follows established patterns
- [ ] Proper error handling

### Testing
- [ ] Unit tests written and passing
- [ ] Integration tests cover main flows
- [ ] Edge cases tested
- [ ] No production data modified

### Accessibility
- [ ] ARIA attributes properly implemented
- [ ] Keyboard navigation supported
- [ ] Screen reader compatibility
- [ ] Color contrast meets standards

### Performance
- [ ] No unnecessary re-renders
- [ ] Proper memoization used
- [ ] Bundle size impact considered
- [ ] Performance metrics acceptable

### ShadCN + Tailwind Compliance
- [ ] Uses ShadCN components where available
- [ ] Uses Tailwind utilities for styling
- [ ] No custom components that duplicate ShadCN
- [ ] No inline styles or custom CSS
- [ ] Follows ShadCN patterns and conventions

## 🎯 Success Metrics

### Quality Metrics
- **Test Coverage**: >90% for new code
- **TypeScript Coverage**: 100% for all new code
- **Linting Errors**: 0 errors
- **Accessibility**: WCAG 2.1 AA compliance
- **ShadCN Usage**: >95% of components use ShadCN where available

### Performance Metrics
- **Component Render Time**: <16ms for interactive components
- **Bundle Size**: <2MB total
- **First Contentful Paint**: <1.5s
- **Time to Interactive**: <3s

### User Experience Metrics
- **Error Rate**: <1% of user interactions
- **Loading Time**: <2s for data fetching
- **User Satisfaction**: >4.5/5 rating
- **Accessibility Score**: 100% on automated tests

## 📚 References

- [React Best Practices](https://react.dev/learn)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Testing Library Guidelines](https://testing-library.com/docs/guiding-principles)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ShadCN UI Documentation](https://ui.shadcn.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

## 🔄 Version History

- **2025-07-22**: Updated to emphasize ShadCN + Tailwind as foundation
- **Patterns established**: Component structure, testing patterns, utility patterns
- **Anti-patterns identified**: Testing anti-patterns, component anti-patterns
- **Quality standards defined**: Performance, accessibility, security patterns
- **ShadCN + Tailwind focus**: Mandatory use of ShadCN components and Tailwind utilities

---

**Note**: This document should be updated as new patterns emerge and lessons are learned. All webui development should follow these established patterns and practices, with ShadCN + Tailwind as the primary foundation. 