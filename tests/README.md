# Transportation Tool Tests

This directory contains comprehensive unit tests for the transportation tool and related functionality.

## Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_tools/              # Tests for tools module
│   └── test_transportation.py  # Transportation tool tests
└── README.md               # This file
```

## Running Tests

### All tests (excluding integration tests)
```bash
pytest
```

### All tests including integration tests (requires API keys)
```bash
pytest -m ""
```

### Only integration tests
```bash
pytest -m integration
```

### Specific test file
```bash
pytest tests/test_tools/test_transportation.py -v
```

### With coverage
```bash
pytest --cov=tools.transportation.transportation --cov-report=html
```

## Test Categories

### Unit Tests
- **TestValidateISOCountryCode**: ISO country code validation
- **TestCacheOperations**: File-based caching functionality
- **TestRateLimiting**: API rate limiting with proper timing
- **TestDistanceCalculations**: Distance calculations (great circle, searoute)
- **TestGeocoding**: Nominatim and LLM fallback geocoding
- **TestLLMIntegration**: LLM transportation plan generation
- **TestMainWorkflow**: End-to-end transportation analysis
- **TestDataModels**: Pydantic model validation

### Integration Tests
- **test_full_integration**: Full workflow with real API calls (requires API keys)

## Fixtures

The `conftest.py` file provides shared fixtures:

- `temp_cache_dir`: Temporary directory for cache testing
- `mock_nominatim_location`: Mock Nominatim API response
- `mock_llm_response`: Mock LLM coordinate response
- `reset_rate_limiter`: Reset rate limiting state between tests

## Test Features

✅ **Comprehensive mocking** of external APIs (Nominatim, OpenAI, searoute)  
✅ **Async test support** with proper pytest-asyncio decorators  
✅ **Rate limiting verification** ensuring 2-second gaps between API calls  
✅ **Cache testing** with temporary directories  
✅ **Error handling** for API failures and invalid inputs  
✅ **Data model validation** including Literal type enforcement  
✅ **Integration tests** for real API testing (optional)  

## Dependencies

Required packages (already in requirements.txt):
- `pytest==8.0.0`
- `pytest-asyncio==0.23.5`

Optional for coverage:
- `pytest-cov`

## Notes

- Unit tests use comprehensive mocking to avoid real API calls
- Integration tests are marked and excluded by default
- All tests maintain the 2-second rate limiting for Nominatim
- Temporary cache directories are automatically cleaned up
- Tests verify both success and error handling scenarios