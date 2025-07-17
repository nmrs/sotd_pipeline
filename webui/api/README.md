# SOTD Pipeline Analyzer API

FastAPI backend for the SOTD pipeline analyzer web UI.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can view the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run tests with pytest:
```bash
pytest test_main.py
```

## Endpoints

- `GET /` - Root endpoint
- `GET /api/health` - Health check endpoint

## Development

The API is designed to integrate with the existing SOTD pipeline tools and provide web-based access to the analyzer functionality. 