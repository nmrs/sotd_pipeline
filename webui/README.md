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
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

## Backend Integration

The frontend is designed to work with the FastAPI backend running on port 8000. The Vite dev server is configured to proxy API requests to the backend.

## Next Steps

- Implement DateRangePicker component
- Build AnalysisTable with React Table
- Add ConfigurationPanel for analysis parameters
- Integrate with backend API endpoints 