## Development Setup

### Code Style
We use automated tools to maintain code quality:

- **black**: Code formatter
  ```bash
  pip install black
  ```

- **isort**: Import sorter
  ```bash
  pip install isort
  ```

### Editor Settings (Cursor)
Add to your settings.json:

```
{
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