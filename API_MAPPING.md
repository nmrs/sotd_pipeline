# API Standardization Mapping Document

## Current API Structure Analysis

### Current Router Prefixes
- `/api/analyze` - analysis endpoints (analysis.py)
- `/api/soap-analyzer` - soap endpoints (soap_analyzer.py)
- `/api/brush-splits` - brush split endpoints (brush_splits.py)
- `/api/brush-validation` - brush validation endpoints (brush_validation.py)
- `/api/brush-matching` - brush matching endpoints (brush_matching.py)
- `/api/catalogs` - catalog endpoints (catalogs.py)
- `/api/files` - file endpoints (files.py)
- `/api/filtered` - filtered entries endpoints (filtered.py)
- `/api/monthly-user-posts` - monthly user posts endpoints (monthly_user_posts.py)

## Proposed Standardized Structure

### New Router Prefixes
- `/api/analysis` - all analysis endpoints
- `/api/soaps` - all soap-related endpoints
- `/api/brushes` - all brush-related endpoints (consolidated)
- `/api/catalogs` - all catalog endpoints
- `/api/files` - all file endpoints
- `/api/filtered` - all filtered entries endpoints
- `/api/users` - all user-related endpoints

## Detailed Endpoint Mapping

### Analysis Endpoints (`/api/analyze` → `/api/analysis`)
| Current Path | New Path | Method | Description |
|--------------|----------|--------|-------------|
| `/api/analyze/comment/{comment_id}` | `/api/analysis/comment/{comment_id}` | GET | Get comment detail |
| `/api/analyze/match-phase` | `/api/analysis/match-phase` | POST | Run match phase analysis |
| `/api/analyze/unmatched` | `/api/analysis/unmatched` | POST | Run unmatched analysis |
| `/api/analyze/debug/version` | `/api/analysis/debug/version` | GET | Get debug version |
| `/api/analyze/clear-validator-cache` | `/api/analysis/clear-validator-cache` | POST | Clear validator cache |
| `/api/analyze/mismatch` | `/api/analysis/mismatch` | POST | Run mismatch analysis |
| `/api/analyze/correct-matches/{field}` | `/api/analysis/correct-matches/{field}` | GET | Get correct matches |
| `/api/analyze/mark-correct` | `/api/analysis/mark-correct` | POST | Mark matches as correct |
| `/api/analyze/remove-correct` | `/api/analysis/remove-correct` | POST | Remove from correct matches |
| `/api/analyze/correct-matches/{field}` | `/api/analysis/correct-matches/{field}` | DELETE | Delete correct matches |
| `/api/analyze/correct-matches` | `/api/analysis/correct-matches` | DELETE | Delete all correct matches |
| `/api/analyze/validate-catalog` | `/api/analysis/validate-catalog` | POST | Validate catalog |
| `/api/analyze/remove-catalog-entries` | `/api/analysis/remove-catalog-entries` | POST | Remove catalog entries |

### Soap Endpoints (`/api/soap-analyzer` → `/api/soaps`)
| Current Path | New Path | Method | Description |
|--------------|----------|--------|-------------|
| `/api/soap-analyzer/duplicates` | `/api/soaps/duplicates` | GET | Get soap duplicates |
| `/api/soap-analyzer/pattern-suggestions` | `/api/soaps/pattern-suggestions` | GET | Get pattern suggestions |
| `/api/soap-analyzer/neighbor-similarity` | `/api/soaps/neighbor-similarity` | GET | Get neighbor similarity |
| `/api/soap-analyzer/group-by-matched` | `/api/soaps/group-by-matched` | GET | Group by matched string |

### Brush Endpoints (Consolidated under `/api/brushes`)
| Current Path | New Path | Method | Description |
|--------------|----------|--------|-------------|
| `/api/brush-splits/load` | `/api/brushes/splits/load` | GET | Load brush splits |
| `/api/brush-splits/validate` | `/api/brushes/splits/validate` | GET | Validate brush splits |
| `/api/brush-splits/save` | `/api/brushes/splits/save` | POST | Save brush splits |
| `/api/brush-splits/validate-save` | `/api/brushes/splits/validate-save` | POST | Validate and save splits |
| `/api/brush-splits/statistics` | `/api/brushes/splits/statistics` | GET | Get split statistics |
| `/api/brush-splits/yaml` | `/api/brushes/splits/yaml` | GET | Get YAML brush splits |
| `/api/brush-validation/months` | `/api/brushes/validation/months` | GET | Get validation months |
| `/api/brush-validation/data/{month}/{system}` | `/api/brushes/validation/data/{month}/{system}` | GET | Get validation data |
| `/api/brush-validation/statistics/{month}` | `/api/brushes/validation/statistics/{month}` | GET | Get validation statistics |
| `/api/brush-validation/statistics/{month}/strategy-distribution` | `/api/brushes/validation/statistics/{month}/strategy-distribution` | GET | Get strategy distribution |
| `/api/brush-validation/action` | `/api/brushes/validation/action` | POST | Perform validation action |
| `/api/brush-matching/analyze` | `/api/brushes/matching/analyze` | POST | Analyze brush matching |
| `/api/brush-matching/health` | `/api/brushes/matching/health` | GET | Health check |

### Catalog Endpoints (`/api/catalogs` → `/api/catalogs`)
| Current Path | New Path | Method | Description |
|--------------|----------|--------|-------------|
| `/api/catalogs/` | `/api/catalogs/` | GET | Get all catalogs |
| `/api/catalogs/{field}` | `/api/catalogs/{field}` | GET | Get specific catalog |

### File Endpoints (`/api/files` → `/api/files`)
| Current Path | New Path | Method | Description |
|--------------|----------|--------|-------------|
| `/api/files/available-months` | `/api/files/available-months` | GET | Get available months |
| `/api/files/{month}` | `/api/files/{month}` | GET | Get month data |
| `/api/files/{month}/summary` | `/api/files/{month}/summary` | GET | Get month summary |

### Filtered Endpoints (`/api/filtered` → `/api/filtered`)
| Current Path | New Path | Method | Description |
|--------------|----------|--------|-------------|
| `/api/filtered/` | `/api/filtered/` | GET | Get filtered entries |
| `/api/filtered/` | `/api/filtered/` | POST | Create filtered entry |
| `/api/filtered/{category}` | `/api/filtered/{category}` | GET | Get filtered entries by category |
| `/api/filtered/check` | `/api/filtered/check` | POST | Check filtered status |

### User Endpoints (`/api/monthly-user-posts` → `/api/users`)
| Current Path | New Path | Method | Description |
|--------------|----------|--------|-------------|
| `/api/monthly-user-posts/months` | `/api/users/months` | GET | Get user months |
| `/api/monthly-user-posts/users/{month}` | `/api/users/users/{month}` | GET | Get users for month |
| `/api/monthly-user-posts/analysis/{month}/{username}` | `/api/users/analysis/{month}/{username}` | GET | Get user analysis |
| `/api/monthly-user-posts/health` | `/api/users/health` | GET | Health check |

## Change Order Plan

1. **Backend Router Updates** (Low Risk)
   - Update router prefixes in all API files
   - Test that all routers load without conflicts

2. **Frontend API Call Updates** (Medium Risk)
   - Update all API calls in `webui/src/services/api.ts`
   - Search for hardcoded API paths in components

3. **Integration Testing** (High Value)
   - Test all endpoints work with new paths
   - Test frontend functionality

4. **Documentation Update** (Low Risk)
   - Update README and documentation

## Risk Assessment

### Low Risk
- Router prefix changes (backend only)
- Documentation updates

### Medium Risk
- Frontend API call updates (many files to update)
- Potential for missed hardcoded paths

### High Risk
- Integration testing (could reveal breaking changes)
- User workflow testing (could reveal UX issues)

## Success Criteria
- All API endpoints accessible at new standardized paths
- All frontend functionality works with new API structure
- No 404 errors for expected endpoints
- Performance not degraded
- Clear, maintainable API structure
