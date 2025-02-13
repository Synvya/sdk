## Development Setup

### Code Quality Tools
We use automated tools to maintain code quality:

1. **Install required tools:**

black (code formater),isort (import sorter) and mypy (type checker) 
  ```bash
  pip install black isort mypy
  ```

2. **Install the package in development mode:**

```bash
pip install -e .[dev]
```

3. **Run the tools before committing:**

```bash
isort .
black .
mypy src/ examples/ tests/
# test the package
pytest tests/ -v
# build the package
rm -rf dist/ build/ *.egg-info
python -m build
```

### Editor Settings (Cursor)

1. **Install recommended extensions on Cursor or VSCode:**
 - Black Formatter
 - Mypy Type Checker
 - isort

2. **Add to your settings.json:**

```
{
    "python.createEnvironment.trigger": "off",
    "git.autofetch": true,
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        }
    }
}
```