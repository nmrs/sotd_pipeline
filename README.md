# 🧸 SOTD Pipeline

A Python data processing pipeline that extracts, processes, and analyzes "Shave of the Day" posts from Reddit's r/wetshaving community.

## 🚀 Quick Start

### Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### Development Workflow
```bash
# Fast development testing (recommended during development)
make test-fast

# Complete validation (run before commits)
make format lint typecheck test

# Run pipeline phases
python run.py fetch --month 2025-05 --force
python run.py extract --month 2025-05 --force
python run.py match --month 2025-05 --force
python run.py enrich --month 2025-05 --force
python run.py aggregate --month 2025-05 --force
python run.py report --month 2025-05 --force

# Or run complete pipeline
python run.py pipeline --month 2025-05 --force
```

## 📊 Pipeline Overview

The pipeline consists of 6 sequential phases:

1. **Fetch** - Extract Reddit threads and comments
2. **Extract** - Parse product mentions from comments
3. **Match** - Normalize product names against catalogs
4. **Enrich** - Extract additional metadata
5. **Aggregate** - Generate statistical summaries
6. **Report** - Create human-readable reports

## 🛠️ Development Features

### Optimized Testing Strategy
- **Fast Tests**: `make test-fast` (~4.6s, 57% faster than sequential)
- **Complete Validation**: `make test` (~10.8s, full coverage)
- **Performance Analysis**: `make test-slow` (identify bottlenecks)
- **Test Count**: 1,255 optimized tests (5.8% reduction from baseline)

### Quality Assurance
- **Code Formatting**: Black + Ruff
- **Linting**: Ruff (E, F, I rules)
- **Type Checking**: Pyright
- **Test Coverage**: pytest-cov

## 📚 Documentation

- **[Pipeline Specification](docs/SOTD_Pipeline_Spec.md)** - Complete pipeline documentation
- **[Development Workflow](docs/SOTD_Pipeline_Spec.md#-development-workflow)** - Optimized testing and development process
- **[Phase Specifications](docs/)** - Detailed specifications for each pipeline phase

## 🔧 Configuration

- **Python**: 3.11
- **Environment**: Virtual environment with `.venv`
- **Dependencies**: See `requirements.txt` and `requirements-dev.txt`
- **Configuration**: `pyproject.toml`, `pyrightconfig.json`

## 📁 Project Structure

```
sotd_pipeline/
├── sotd/                    # Main pipeline modules
│   ├── fetch/              # Reddit data extraction
│   ├── extract/            # Product mention parsing
│   ├── match/              # Product name normalization
│   ├── enrich/             # Metadata enrichment
│   ├── aggregate/          # Statistical aggregation
│   └── report/             # Report generation
├── tests/                  # Comprehensive test suite
├── data/                   # Pipeline data storage
├── docs/                   # Detailed documentation
├── run.py                  # Pipeline orchestration
└── Makefile               # Development commands
```

## 🤝 Contributing

1. Follow the **Pipeline --force Rule**: Always use `--force` flag during development
2. Use **Test-First Development**: Write tests before implementing features
3. Run **Fast Tests** during development: `make test-fast`
4. Run **Complete Validation** before commits: `make format lint typecheck test`
5. Update documentation with code changes

## 📈 Performance

- **Test Execution**: 57% improvement with parallel execution
- **Test Coverage**: 71% with comprehensive edge case coverage
- **Development Speed**: Fast feedback loop with optimized testing strategy

---

For detailed information, see the [Pipeline Specification](docs/SOTD_Pipeline_Spec.md). 