# SOTD Pipeline Analyzer Web UI

React frontend for the SOTD pipeline analyzer, providing web-based interfaces for the unmatched_analyzer.py and mismatch_analyzer.py tools.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Development

- **Port**: 3000 (configured in vite.config.ts)
- **API Proxy**: Requests to `/api/*` are proxied to `http://localhost:8000` (FastAPI backend)
- **TypeScript**: Full TypeScript support with strict mode
- **Routing**: React Router for navigation between analyzers

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/         # Page components
├── services/      # API service layer
├── utils/         # Utility functions
└── types/         # TypeScript type definitions
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint with error reporting
- `npm run lint:fix` - Run ESLint with auto-fix
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting with Prettier
- `npm run preview` - Preview production build

## Code Quality & Linting

This project uses ESLint and Prettier for code quality and formatting:

### ESLint Configuration
- **TypeScript**: Full TypeScript support with strict rules
- **React**: React-specific linting rules and best practices
- **Hooks**: React Hooks linting rules
- **Prettier Integration**: ESLint works with Prettier for consistent formatting

### Prettier Configuration
- **Formatting**: Consistent code formatting across the project
- **Line Length**: 100 characters
- **Quotes**: Single quotes
- **Semicolons**: Always included
- **Trailing Commas**: ES5 style

### Running Linting
```bash
# Check for linting errors
npm run lint

# Auto-fix linting errors
npm run lint:fix

# Format code with Prettier
npm run format

# Check formatting without making changes
npm run format:check
```

### Current Status
- **Formatting**: ✅ All files are properly formatted
- **Linting**: ⚠️ 286 issues remaining (mostly TypeScript `any` types and React imports)
- **Auto-fix**: Most formatting issues can be auto-fixed

## Backend Integration

The frontend is designed to work with the FastAPI backend running on port 8000. The Vite dev server is configured to proxy API requests to the backend.

### API Endpoints

The backend provides a standardized REST API with the following endpoint structure:

#### Analysis Endpoints (`/api/analysis/`)
- `GET /api/analysis/comment/{comment_id}` - Get comment detail
- `POST /api/analysis/match-phase` - Run match phase analysis
- `POST /api/analysis/unmatched` - Run unmatched analysis
- `POST /api/analysis/mismatch` - Run mismatch analysis
- `GET /api/analysis/correct-matches/{field}` - Get correct matches
- `POST /api/analysis/mark-correct` - Mark matches as correct
- `POST /api/analysis/remove-correct` - Remove from correct matches
- `DELETE /api/analysis/correct-matches/{field}` - Delete correct matches
- `DELETE /api/analysis/correct-matches` - Delete all correct matches
- `POST /api/analysis/validate-catalog` - Validate catalog
- `POST /api/analysis/remove-catalog-entries` - Remove catalog entries

#### Soap Endpoints (`/api/soaps/`)
- `GET /api/soaps/duplicates` - Get soap duplicates
- `GET /api/soaps/pattern-suggestions` - Get pattern suggestions
- `GET /api/soaps/neighbor-similarity` - Get neighbor similarity
- `GET /api/soaps/group-by-matched` - Group by matched string

#### Brush Endpoints (`/api/brushes/`)
- `GET /api/brushes/splits/load` - Load brush splits
- `GET /api/brushes/splits/validate` - Validate brush splits
- `POST /api/brushes/splits/save` - Save brush splits
- `GET /api/brushes/splits/yaml` - Get YAML brush splits
- `GET /api/brushes/validation/months` - Get validation months
- `GET /api/brushes/validation/data/{month}/{system}` - Get validation data
- `GET /api/brushes/validation/statistics/{month}` - Get validation statistics
- `POST /api/brushes/validation/action` - Perform validation action
- `POST /api/brushes/matching/analyze` - Analyze brush matching

#### Product Usage Endpoints (`/api/product-usage/`)
- `GET /api/product-usage/products/{month}/{product_type}` - Get list of available products for a month and product type
  - Query parameters: `search` (optional) - Filter products by brand/model
  - Product types: `razor`, `blade`, `brush`, `soap`
  - Returns: List of products with `key`, `brand`, `model`, `usage_count`, `unique_users`
- `GET /api/product-usage/analysis/{month}/{product_type}/{brand}/{model}` - Get product usage analysis
  - Returns: Product usage analysis with users, usage counts, dates, and comment IDs
- `GET /api/product-usage/yearly-summary/{month}/{product_type}/{brand}/{model}` - Get yearly summary for a product
  - Returns: Yearly summary with monthly statistics (shaves, unique users, rank) for the past 12 months
  - Uses aggregated data files for performance
  - Returns data for selected month and previous 11 months
- `GET /api/product-usage/health` - Health check endpoint

#### Other Endpoints
- `GET /api/catalogs/` - Get all catalogs
- `GET /api/catalogs/{field}` - Get specific catalog
- `GET /api/files/available-months` - Get available months
- `GET /api/files/{month}` - Get month data
- `GET /api/filtered/` - Get filtered entries
- `GET /api/users/months` - Get user months
- `GET /api/users/users/{month}` - Get users for month

## Next Steps

- Implement DateRangePicker component
- Build AnalysisTable with React Table
- Add ConfigurationPanel for analysis parameters
- Integrate with backend API endpoints 