import argparse
import os
from api_doc_generator import APIScraper, DocumentationGenerator
import logging

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate API documentation from a documentation website')
    parser.add_argument('url', help='URL of the API documentation website')
    parser.add_argument('--output', '-o', default='output',
                      help='Output directory for generated documentation (default: output)')
    
    args = parser.parse_args()
    
    try:
        # Create output directory
        os.makedirs(args.output, exist_ok=True)
        
        # Initialize and run the scraper
        print(f"Starting to scrape API documentation from {args.url}")
        scraper = APIScraper(args.url)
        api_docs = scraper.crawl()
        
        if not api_docs:
            print("No API documentation content was found. Please check the URL and try again.")
            return
        
        # Generate documentation
        print("\nGenerating documentation...")
        generator = DocumentationGenerator(api_docs, args.output)
        generator.generate()
        
        print(f"\nDocumentation generated successfully!")
        print(f"Markdown file: {os.path.join(args.output, 'api_documentation.md')}")
        print(f"HTML file: {os.path.join(args.output, 'api_documentation.html')}")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
