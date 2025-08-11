# 🤝 Contributing to Mangaku API

First off, thank you for considering contributing to Mangaku API! 🎉 It's people like you that make this project such a great tool for the manga community.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Pledge

- **Be welcoming** to newcomers
- **Be respectful** of differing viewpoints and experiences
- **Accept constructive criticism** gracefully
- **Focus on what is best** for the community
- **Show empathy** towards other community members

## 🌟 How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check the existing issues as you might find that the problem has already been reported. When creating a bug report, please include:

- **Clear and descriptive title**
- **Exact steps to reproduce** the problem
- **Expected behavior** vs **actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Code samples** or **error messages**

### 💡 Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Clear and descriptive title**
- **Detailed description** of the suggested enhancement
- **Use cases** and **examples**
- **Possible implementation** approach (if you have ideas)

### 🔧 Code Contributions

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Add tests** for new functionality
5. **Ensure** all tests pass
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to your branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

## 🚀 Development Setup

### Prerequisites

- Python 3.7+
- pip or pipenv
- Git

### Local Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/badruzbby/mangaku-api.git
cd mangaku-api

# 2. Create virtual environment
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install development dependencies
pip install -r requirements-dev.txt

# 5. Run tests to ensure everything works
python -m pytest

# 6. Start the development server
python app.py
```

### 🐳 Docker Development

```bash
# Build and run with Docker
docker build -t mangaku-api-dev .
docker run -p 5000:5000 -v $(pwd):/app mangaku-api-dev
```

## 📝 Pull Request Process

### Before Submitting

- [ ] **Read** the contributing guidelines
- [ ] **Search** existing PRs to avoid duplicates
- [ ] **Test** your changes thoroughly
- [ ] **Update** documentation if needed
- [ ] **Follow** the coding style guidelines

### PR Checklist

- [ ] **Descriptive title** and detailed description
- [ ] **Reference** related issues (`Fixes #123`)
- [ ] **Add tests** for new features
- [ ] **Update documentation** if needed
- [ ] **Ensure CI passes** (tests, linting)
- [ ] **Keep commits atomic** and well-described

### PR Template

```markdown
## 📋 Description
Brief description of what this PR does.

## 🔗 Related Issue
Fixes #(issue number)

## 🧪 Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## ✅ Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## 📸 Screenshots (if applicable)
Add screenshots to help explain your changes.
```

## 🎨 Style Guidelines

### Python Code Style

We follow **PEP 8** with some modifications:

```python
# Good
def get_manga_list(page: int = 1) -> List[Dict[str, Any]]:
    """Get paginated list of manga.
    
    Args:
        page: Page number for pagination
        
    Returns:
        List of manga dictionaries
    """
    pass

# Bad
def getMangaList(page=1):
    pass
```

### Key Guidelines

- **Line length**: 88 characters (Black formatter)
- **Imports**: Use absolute imports, group them properly
- **Docstrings**: Use Google-style docstrings
- **Type hints**: Use them for function parameters and return types
- **Variable names**: Use descriptive names (`manga_list` not `ml`)

### Code Formatting

We use automated formatting tools:

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

### Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add search endpoint for manga
fix(scraper): handle missing image URLs
docs(readme): update installation instructions
```

## 🐛 Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
## 🐛 Bug Description
A clear description of what the bug is.

## 🔄 Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. See error

## ✅ Expected Behavior
What you expected to happen.

## ❌ Actual Behavior
What actually happened.

## 🖥️ Environment
- OS: [e.g. Windows 10]
- Python Version: [e.g. 3.9.0]
- API Version: [e.g. 1.0.0]

## 📋 Additional Context
Add any other context about the problem here.
```

### Feature Requests

Use the feature request template:

```markdown
## 💡 Feature Description
A clear description of the feature you'd like to see.

## 🎯 Problem Statement
What problem does this feature solve?

## 💭 Proposed Solution
How would you like this feature to work?

## 🔄 Alternatives Considered
Any alternative solutions you've considered.

## 📋 Additional Context
Any other context or screenshots about the feature request.
```

## 🏷️ Labels

We use labels to categorize issues and PRs:

- **Type**: `bug`, `enhancement`, `documentation`, `question`
- **Priority**: `high`, `medium`, `low`
- **Status**: `needs-review`, `work-in-progress`, `blocked`
- **Area**: `api`, `scraper`, `docs`, `tests`, `ci`

## 🌍 Community

### Getting Help

- 📚 **Documentation**: Check the README and API docs first
- 🐛 **Issues**: Search existing issues before creating new ones
- 💬 **Discussions**: Use GitHub Discussions for questions
- 📧 **Email**: badzzhaxor@gmail.com for private matters

### Recognition

Contributors are recognized in:

- **README.md**: Contributors section
- **CHANGELOG.md**: Release notes
- **GitHub**: Contributor graphs and stats

## 🎉 Thank You!

Your contributions make this project better for everyone. Whether it's:

- 🐛 **Reporting a bug**
- 💡 **Suggesting a feature**
- 📝 **Improving documentation**
- 🔧 **Contributing code**
- ⭐ **Starring the repository**
- 📢 **Spreading the word**

Every contribution matters! 🙏

---

**Happy Contributing! 🚀** 