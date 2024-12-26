from api_doc_generator.scraper import APIScraper
from api_doc_generator.generator import DocumentationGenerator, ModelConfig
import os
import asyncio
import time
from pathlib import Path

def print_available_models():
    """Print available Gemini models and their descriptions"""
    print("\nAvailable Models:")
    print("-" * 80)
    for model_name, info in ModelConfig.MODELS.items():
        exp_tag = "[Experimental]" if info["experimental"] else ""
        print(f"{model_name} {exp_tag}")
        print(f"  Description: {info['description']}")
        print(f"  Capabilities: {', '.join(info['capabilities'])}")
        print()

async def main():
    # Print available models
    print_available_models()
    
    # Test with Supabase Auth0 Integration documentation
    base_url = "https://supabase.com/partners/integrations/auth0"
    output_dir = "generated_docs"
    
    # Model configuration
    model_name = "gemini-1.5-pro"  # Default model
    temperature = 0.3  # Default temperature
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("\n[1/2] Scraping API documentation...")
    print(f"Base URL: {base_url}")
    print("This may take a few minutes depending on the size of the documentation.")
    
    start_time = time.time()
    scraper = APIScraper(base_url=base_url)
    api_docs = scraper.crawl()
    
    print(f"\nScraping completed in {time.time() - start_time:.2f} seconds")
    print(f"Found {len(api_docs)} pages")
    
    print("\n[2/2] Generating documentation...")
    print(f"Using model: {model_name} (temperature: {temperature})")
    
    generator = DocumentationGenerator(
        api_docs, 
        output_dir,
        model_name=model_name,
        temperature=temperature
    )
    generator.generate()
    
    # Show results
    md_path = os.path.join(output_dir, 'api_documentation.md')
    html_path = os.path.join(output_dir, 'api_documentation.html')
    
    print(f"\nDocumentation generated successfully!")
    print(f"\nFiles generated:")
    print(f"1. Markdown: {md_path}")
    print(f"2. HTML: {html_path}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise
