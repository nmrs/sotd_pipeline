# Linter Errors TODO List

**Created**: 2025-09-03  
**Last Updated**: 2025-09-03  
**Status**: IN_PROGRESS  
**Total Errors**: 2,364  
**Resolved**: 0  
**Remaining**: 2,364

> **Note**: This is a reusable tracking file. Update the "Last Updated" date and error counts whenever you run linter fixes.  

## Error Categories

### E501 - Line Too Long (>100 characters)
**Status**: TODO  
**Count**: 2,255  
**Priority**: HIGH (most common, causes timeout)

#### Files with E501 errors:
- [ ] TBD - Will be populated from linter scan

### F401 - Unused Imports
**Status**: TODO  
**Count**: 85  
**Priority**: MEDIUM

#### Files with F401 errors:
- [ ] TBD - Will be populated from linter scan

### F841 - Unused Variables
**Status**: TODO  
**Count**: 24  
**Priority**: MEDIUM

#### Files with F841 errors:
- [ ] TBD - Will be populated from linter scan

### E401 - Multiple Imports on Same Line
**Status**: TODO  
**Count**: TBD  
**Priority**: LOW

#### Files with E401 errors:
- [ ] TBD - Will be populated from linter scan

### I001 - Import Block Un-sorted/Un-formatted
**Status**: TODO  
**Count**: TBD  
**Priority**: LOW

#### Files with I001 errors:
- [ ] TBD - Will be populated from linter scan

## Progress Tracking

### Phase 1: Error Discovery ✅
- [x] Run comprehensive linter scan
- [x] Create error tracking file
- [ ] Categorize all errors by type
- [ ] Count errors by category

### Phase 2: Systematic Fix Implementation
- [ ] Fix E501 errors (line length)
- [ ] Fix F401 errors (unused imports)
- [ ] Fix F841 errors (unused variables)
- [ ] Fix E401 errors (multiple imports)
- [ ] Fix I001 errors (import sorting)

### Phase 3: Validation and Cleanup
- [ ] Final linter run
- [ ] Verify all errors resolved
- [ ] Update documentation

## Configuration Notes
- **Linter**: Ruff with E, F, I rules
- **Line length limit**: 100 characters
- **Excluded directories**: data/, tests/, .venv/, venv/
- **Per-file ignores**: __init__.py for F401
- **Auto-fix available**: F401, F841, E401, I001
- **Manual fixes needed**: E501 (line length)

## Quick Commands Reference
```bash
# Systematic workflow (recommended)
make lint-systematic

# Get current error counts
make lint-count

# Auto-fix fixable errors
make lint-auto-fix

# Format files (fixes most E501 errors)
make lint-format

# Check specific error types
make lint-e501
make lint-f401
make lint-f841

# Full quality check
make format lint typecheck test
```

## Reusability Instructions
1. **Update "Last Updated" date** when starting new session
2. **Run discovery commands** to get current error counts
3. **Update error counts** in this file
4. **Mark categories as COMPLETE** when done
5. **Add notes** about any complex cases or decisions
6. **Keep this file current** for future linter maintenance
