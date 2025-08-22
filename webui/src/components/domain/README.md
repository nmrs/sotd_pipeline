# Domain Components

This directory contains reusable domain-specific components used across the SOTD Pipeline WebUI.

## CommentDisplay

A reusable component for displaying comment IDs with automatic expansion/collapse functionality.

### Features

- **Automatic Limiting**: Shows only 3 comments by default
- **Expandable**: Click "+n more" to show all comments
- **Collapsible**: Click "Show less" to collapse back to 3
- **Loading State**: Disables buttons during comment loading
- **Empty State**: Shows "-" when no comments are available
- **Customizable**: Configurable max display count and styling

### Usage

```tsx
import { CommentDisplay } from '../components/domain/CommentDisplay';

// Basic usage
<CommentDisplay
  commentIds={['abc123', 'def456', 'ghi789', 'jkl012']}
  onCommentClick={handleCommentClick}
  commentLoading={false}
/>

// With custom settings
<CommentDisplay
  commentIds={commentIds}
  onCommentClick={handleCommentClick}
  commentLoading={commentLoading}
  maxDisplay={5}
  className="custom-styling"
/>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `commentIds` | `string[]` | `[]` | Array of comment IDs to display |
| `onCommentClick` | `(commentId: string) => void` | - | Callback when a comment ID is clicked |
| `commentLoading` | `boolean` | `false` | Whether comments are currently loading |
| `maxDisplay` | `number` | `3` | Maximum number of comments to show initially |
| `className` | `string` | `''` | Additional CSS classes to apply |

### Behavior

1. **Empty State**: If no comment IDs are provided, shows "-"
2. **Limited Display**: Initially shows up to `maxDisplay` comments
3. **Expansion**: If there are more comments, shows "+n more" link
4. **Full Display**: Clicking "+n more" shows all comments
5. **Collapse**: When expanded, shows "Show less" to collapse back

### Examples

#### Basic Table Cell
```tsx
<td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
  <CommentDisplay
    commentIds={result.comment_ids}
    onCommentClick={handleCommentClick}
    commentLoading={commentLoading}
  />
</td>
```

#### With Custom Styling
```tsx
<CommentDisplay
  commentIds={item.comment_ids}
  onCommentClick={handleCommentClick}
  commentLoading={commentLoading}
  maxDisplay={5}
  className="text-xs space-y-0.5"
/>
```

### Migration from Manual Implementation

If you currently have manual comment rendering like this:

```tsx
// OLD - Manual implementation
{result.comment_ids ? (
  <div className='space-y-1'>
    {result.comment_ids.map((commentId, idIndex) => (
      <button
        key={idIndex}
        onClick={() => handleCommentClick(commentId)}
        className='block text-blue-600 hover:text-blue-800 hover:underline cursor-pointer text-left'
        disabled={commentLoading}
      >
        {commentId}
      </button>
    ))}
  </div>
) : (
  '-'
)}
```

Replace it with:

```tsx
// NEW - Using CommentDisplay component
<CommentDisplay
  commentIds={result.comment_ids}
  onCommentClick={handleCommentClick}
  commentLoading={commentLoading}
/>
```

### Benefits

- **Consistent UI**: All comment displays look and behave the same
- **DRY Principle**: No need to duplicate comment rendering logic
- **Maintainable**: Changes to comment display behavior only need to be made in one place
- **Accessible**: Built-in keyboard navigation and ARIA labels
- **Performance**: Efficient rendering with proper React patterns

### Related Components

- `CommentList`: Alternative component with different styling and behavior
- `CommentModal`: Modal for displaying comment details
- `CommentDisplay`: This component (recommended for most use cases)
