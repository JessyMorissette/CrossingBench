# Contributing

Thanks for your interest.

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
```

## Guidelines
- Keep runtime dependency-free.
- Keep outputs stable (CSV columns and meanings).
- Prefer small, well-documented changes with tests.
