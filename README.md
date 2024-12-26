# API Documentation Generator

A robust Python tool that automatically scrapes API documentation websites and generates comprehensive, well-structured documentation for API integration.

## Features

- Crawls and scrapes API documentation websites
- Extracts API endpoints, descriptions, and code samples
- Generates both Markdown and HTML documentation
- Respects website crawling etiquette with rate limiting
- Progress tracking with progress bars
- Clean and modern HTML output with responsive design

## Installation

1. Clone the repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the tool from the command line:

```bash
python main.py https://api-docs-url.com --output ./docs
```

### Arguments

- `url`: The URL of the API documentation website to scrape (required)
- `--output` or `-o`: Output directory for generated documentation (default: 'output')

## Output

The tool generates two files:
1. `api_documentation.md` - Markdown format documentation
2. `api_documentation.html` - HTML format documentation with modern styling

## Generated Documentation Features

- Table of Contents
- API Endpoints listing
- Code examples
- Parameter descriptions
- Links to original documentation
- Clean and modern design
- Mobile-responsive layout

## Requirements

- Python 3.7+
- See requirements.txt for package dependencies

## Notes

- The tool respects robots.txt and implements rate limiting
- Make sure you have permission to scrape the target website
- Some websites may block automated scraping

## License

MIT License
