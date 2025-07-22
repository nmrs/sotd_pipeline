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

## Next Steps

- Implement DateRangePicker component
- Build AnalysisTable with React Table
- Add ConfigurationPanel for analysis parameters
- Integrate with backend API endpoints 