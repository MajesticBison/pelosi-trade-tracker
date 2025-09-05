# Contributing to Pelosi Trade Tracker

Thank you for your interest in contributing to the Pelosi Trade Tracker! This project helps monitor financial disclosures from members of Congress and provides transparency into their trading activities.

## How to Contribute

### 🐛 Bug Reports
- Use the GitHub Issues tab
- Include steps to reproduce the bug
- Provide error messages and logs
- Specify your operating system and Python version

### ✨ Feature Requests
- Use the GitHub Issues tab with the "enhancement" label
- Describe the feature and its use case
- Consider if it fits the project's scope (Congressional financial transparency)

### 🔧 Code Contributions
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Create a Pull Request

## Development Setup

### Prerequisites
- Python 3.7+
- Git
- Discord webhook URL (for testing)

### Local Setup
```bash
# Clone your fork
git clone https://github.com/your-username/pelosi-trade-tracker.git
cd pelosi-trade-tracker

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env
# Edit .env with your Discord webhook URL

# Test the setup
python pelosi_tracker.py --dry-run
```

## Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Include type hints where appropriate
- Keep functions focused and small

## Testing

Before submitting a PR:
- Run the dry-run test: `python pelosi_tracker.py --dry-run`
- Test Discord integration: `python pelosi_tracker.py --test-discord`
- Check status: `python check_status.py` (or `./check_status.sh` on macOS)

## Areas for Contribution

### 🎯 High Priority
- **Additional Politicians**: Add support for other members of Congress
- **Enhanced Parsing**: Improve PDF parsing accuracy
- **Better Error Handling**: More robust error recovery
- **Performance**: Optimize scraping and parsing speed

### 🔧 Medium Priority
- **Web Interface**: Create a simple web dashboard
- **Database Improvements**: Better data structure and queries
- **Notification Channels**: Support for Slack, email, etc.
- **Analytics**: Trade pattern analysis and reporting

### 📚 Documentation
- **API Documentation**: Document internal APIs
- **Tutorials**: Step-by-step setup guides
- **Examples**: Sample configurations and use cases

## Legal and Ethical Considerations

- This project is for educational and transparency purposes
- Respect rate limits and terms of service
- Don't use for commercial purposes without permission
- Be mindful of privacy and data protection

## Questions?

- Open an issue for questions
- Check existing issues first
- Be respectful and constructive

## Recognition

Contributors will be recognized in the README and release notes. Thank you for helping make Congressional financial transparency more accessible!
