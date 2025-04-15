# Contributing to Synvya SDK

Thank you for your interest in contributing to the Synvya SDK! Your contributions are invaluable in helping us build a robust and user-friendly toolkit for AI-commerce on the Nostr network.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
  - [Reporting Issues](#reporting-issues)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Submitting Pull Requests](#submitting-pull-requests)
- [Development Setup](#development-setup)
- [Style Guide](#style-guide)
- [Testing](#testing)
- [Community Engagement](#community-engagement)
- [License](#license)

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms.

## How to Contribute

We welcome various forms of contributions, including:

- Reporting bugs and issues
- Suggesting new features or enhancements
- Writing or updating documentation
- Writing code (new features, bug fixes, refactoring)
- Reviewing pull requests

### Reporting Issues

If you encounter a bug, performance issue, or have a feature request, please [open an issue](https://github.com/synvya/sdk/issues/new). Provide as much detail as possible to help us understand and address the problem effectively. When reporting issues, please include:

- A clear and descriptive title
- A detailed description of the issue
- Steps to reproduce the issue
- Expected and actual behavior
- Screenshots or code snippets, if applicable
- Any other relevant information, such as your environment (OS, SDK version)

### Suggesting Enhancements

To propose enhancements or new features, please [open an issue](https://github.com/synvya/sdk/issues/new) and provide the following information:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- The motivation and use case for the enhancement
- Any relevant examples or references

### Submitting Pull Requests

1. **Fork the Repository**: Click the "Fork" button at the top right of the [repository page](https://github.com/synvya/sdk) to create your own copy.

2. **Clone Your Fork**:
   ```shell
   git clone https://github.com/your-username/sdk.git
   cd sdk
   ```
3. Create a New Branch:
    ```shell
    git checkout -b feature/your-feature-name
    ```
4. Make Your Changes: Implement your feature or fix, adhering to the project’s [Style Guide](#style-guide).
5. Commit Your changes:
    ```shell
    git commit -m "Brief description of your changes"
    ```
6. Push to Your Fork:
   ```shell
   git push origin feature/your-feature-name
   ```
7. Open a Pull Request: Navigate to the original repository and click the “New Pull Request” button. Provide a clear description of your changes and any relevant context.

### Development Setup
To set up a local development environment:
1. Clone the Repository:
    ```shell
    git clone https://github.com/synvya/sdk.git
    cd sdk
    ```
2. Create a Virtual Environment:
   ```shell
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install Dependencies:
   ```shell
   pip install -r requirements.txt
   ```

### Install Pre-commit Hooks
This project uses [pre-commit](https://pre-commit.com/)to ensure code consistency and quality. Before committing, ensure you’ve installed and set up pre-commit hooks as follows:

   ```shell
   pip install pre-commit detect-secrets
   pre-commit install
   pre-commit autoupdate
   ```
Generate a secrets baseline to prevent false positives:
  ```shell
  detect-secrets scan > .secrets.baseline
  git add .secrets.baseline
  git commit -m "Add detect-secrets baseline"
  ```
### Style Guide
- Code Formatting: Use Black for code formatting.
- Linting: Follow Pylint recommendations.
- Type Hinting: Include type hints in function signatures and variable declarations.
- Commit Messages: Follow the Conventional Commits specification.

### Testing
Ensure that your changes do not break existing functionality:
1. Run Tests
   ```shell
   pytest -s tests/
   ```
2. Add Tests: If you’ve added new features, include corresponding tests in the `tests/` directory.

### Community Engagement

We encourage you to engage with the community:
- Discussions: Participate in discussions on our [GitHub Discussions page](https://github.com/synvya/sdk/discussions).
- Meetings: Join our regular community meetings. Details are posted on our [community calendar](https://github.com/synvya/sdk/wiki/Community-Calendar).
- Chat: Connect with us on channel TBD.

### License
By contributing to the Synvya SDK, you agree that your contributions will be licensed under the [MIT License](LICENSE).
