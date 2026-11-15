# Development

## Checks

From the repository root:

```
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
.venv/Scripts/python -m mypy
```

From `web/`:

```
npm run build
node --test 'src/**/*.test.ts'
```
