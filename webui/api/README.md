# SOTD Pipeline Analyzer API

FastAPI backend for the SOTD pipeline analyzer web UI.

## Setup

**Note:** The API uses the main project's virtual environment to access the SOTD pipeline modules.

1. Activate the main project's virtual environment:
```bash
# From the project root
source .venv/bin/activate
```

2. Install API dependencies (if not already installed):
```bash
pip install fastapi uvicorn[standard] pydantic python-multipart httpx pytest
```

3. Run the development server:
```bash
# From the webui/api directory
cd webui/api
python main.py
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

### Important Notes

- **Virtual Environment**: Always use the main project's virtual environment (`.venv` in project root), not a separate one
- **Python Path**: The API needs access to the `sotd` module from the main project
- **Dependencies**: All API dependencies are available in the main project's virtual environment

### Quick Start

```bash
# From project root
source .venv/bin/activate
cd webui/api
python main.py
``` 