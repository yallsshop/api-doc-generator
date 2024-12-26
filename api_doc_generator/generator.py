import os
import markdown
from typing import Dict, List
import json
import time
import google.generativeai as genai

class ModelConfig:
    """Configuration for different Gemini model variants"""
    
    # Available model variants
    MODELS = {
        "gemini-2.0-flash": {
            "description": "Next generation features, superior speed, native tool use, and multimodal generation",
            "capabilities": ["text", "images", "audio", "video"],
            "experimental": True
        },
        "gemini-1.5-flash": {
            "description": "Fast and versatile performance across diverse tasks",
            "capabilities": ["text", "images", "audio", "video"],
            "experimental": False
        },
        "gemini-1.5-flash-8b": {
            "description": "High volume and lower intelligence tasks",
            "capabilities": ["text", "images", "audio", "video"],
            "experimental": False
        },
        "gemini-1.5-pro": {
            "description": "Complex reasoning tasks requiring more intelligence",
            "capabilities": ["text", "images", "audio", "video"],
            "experimental": False
        },
        "gemini-2.0-flash-thinking-exp": {
            "description": "Reasoning for complex problems with Thinking mode",
            "capabilities": ["text"],
            "experimental": True
        },
        "gemini-exp-1206": {
            "description": "Quality improvements, celebrate 1 year of Gemini",
            "capabilities": ["text"],
            "experimental": True
        }
    }
    
    @classmethod
    def get_model_config(cls, model_name: str, temperature: float = 0.3) -> dict:
        """Get configuration for specified model"""
        if model_name not in cls.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Available models: {', '.join(cls.MODELS.keys())}")
            
        return {
            "model_name": model_name,
            "experimental": cls.MODELS[model_name]["experimental"],
            "generation_config": {
                "temperature": temperature,
                "top_k": 20,
                "top_p": 0.8,
                "max_output_tokens": 2048,
                "stop_sequences": ["\n---\n"],
                "candidate_count": 1,
                "presence_penalty": 0.2,
                "frequency_penalty": 0.2
            },
            "safety_settings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }

class DocumentationGenerator:
    def __init__(self, api_docs: Dict[str, dict], output_dir: str, 
                 model_name: str = "gemini-1.5-pro", temperature: float = 0.3):
        """
        Initialize the documentation generator
        
        Args:
            api_docs (Dict[str, dict]): Collected API documentation
            output_dir (str): Directory to save generated documentation
            model_name (str): Name of the Gemini model to use
            temperature (float): Temperature for model generation (0.0-1.0)
        """
        self.api_docs = api_docs
        self.output_dir = output_dir
        self.model_name = model_name
        self.temperature = temperature
        os.makedirs(output_dir, exist_ok=True)
        
    def _generate_markdown(self) -> str:
        """Generate markdown documentation from API docs"""
        sections = []
        
        # Add header
        sections.append("# API Integration Guide\n")
        sections.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Process each page
        for url, doc in self.api_docs.items():
            # Add page title
            title = doc.get('title', 'Untitled Page')
            sections.append(f"\n## {title}\n")
            
            # Add description if available
            if doc.get('description'):
                sections.append(f"\n{doc['description']}\n")
            
            # Add URL reference
            sections.append(f"\nSource: [{url}]({url})\n")
            
            # Add main content
            if doc.get('content'):
                sections.append("\n### Content\n")
                sections.append(doc['content'])
            
            # Add code samples if available
            if doc.get('code_samples'):
                sections.append("\n### Code Examples\n")
                for i, sample in enumerate(doc['code_samples'], 1):
                    sections.append(f"\nExample {i}:\n")
                    sections.append(f"```\n{sample}\n```\n")
            
            # Add related links if available
            if doc.get('links'):
                sections.append("\n### Related Links\n")
                for text, link in doc['links'].items():
                    sections.append(f"- [{text}]({link})\n")
        
        return "\n".join(sections)
    
    def _generate_html(self, markdown_content: str) -> str:
        """Convert markdown to HTML with styling"""
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['fenced_code', 'tables', 'toc']
        )
        
        # Create HTML with styling
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            margin-top: 2rem;
        }}
        h1 {{ font-size: 2.5rem; }}
        h2 {{ font-size: 2rem; }}
        h3 {{ font-size: 1.5rem; }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        pre {{
            background: #f8f9fa;
            border-radius: 4px;
            padding: 1rem;
            overflow-x: auto;
        }}
        code {{
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 0.9rem;
            background: #f8f9fa;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 1rem 0;
            padding: 0.5rem 1rem;
            background: #f8f9fa;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        hr {{
            border: none;
            border-top: 2px solid #eee;
            margin: 2rem 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 0.5rem;
            text-align: left;
        }}
        th {{
            background: #f8f9fa;
        }}
        @media (max-width: 600px) {{
            body {{
                padding: 1rem;
            }}
            h1 {{ font-size: 2rem; }}
            h2 {{ font-size: 1.5rem; }}
            h3 {{ font-size: 1.25rem; }}
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
    
    def _generate_ai_review_prompt(self, source_url: str, markdown_content: str) -> str:
        """Generate a prompt for AI to review the documentation"""
        return f"""You are a technical documentation expert. Please review this API integration documentation and provide feedback.

SOURCE URL: {source_url}
GOAL: Create comprehensive documentation for API integration from the source URL.

REVIEW TASKS:
1. Completeness Check:
   - Are all essential API integration steps covered?
   - Are there any missing prerequisites or setup instructions?
   - Are authentication and authorization flows properly documented?

2. Technical Accuracy:
   - Are code examples correct and following best practices?
   - Are all API endpoints, parameters, and responses documented?
   - Are security considerations properly addressed?

3. Structure and Clarity:
   - Is the documentation well-organized and easy to follow?
   - Are technical concepts clearly explained?
   - Are there sufficient examples and use cases?

4. Additional Resources:
   - What additional information or examples would improve this documentation?
   - Are there related topics that should be covered?
   - Should we include links to other relevant documentation?

DOCUMENTATION TO REVIEW:
{markdown_content}

Please provide:
1. An assessment of the documentation's completeness and accuracy
2. Specific areas that need improvement
3. Suggestions for additional content or examples needed
4. Recommendations for better organization or clarity
5. Links to additional resources that should be referenced"""

    def _review_documentation(self, source_url: str, markdown_content: str) -> str:
        """Use AI to review and provide feedback on the documentation"""
        import google.generativeai as genai
        import os
        
        # Configure Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        
        try:
            # Get model configuration
            model_config = ModelConfig.get_model_config(self.model_name, self.temperature)
            
            if model_config["experimental"]:
                print(f"Warning: Using experimental model {self.model_name}")
            
            # Create model with configurations
            model = genai.GenerativeModel(
                model_name=model_config["model_name"],
                generation_config=model_config["generation_config"],
                safety_settings=model_config["safety_settings"]
            )
            
            # Generate review prompt
            prompt = self._generate_ai_review_prompt(source_url, markdown_content)
            
            # Configure chat parameters
            chat = model.start_chat(history=[])
            
            # Get AI review with streaming
            response = chat.send_message(
                prompt,
                stream=True,
                generation_config=model_config["generation_config"],
                safety_settings=model_config["safety_settings"]
            )
            
            # Collect streamed response
            review_parts = []
            for chunk in response:
                if chunk.text:
                    review_parts.append(chunk.text)
            review = ''.join(review_parts)
            
            # Add review to documentation with metadata
            final_content = f"""{markdown_content}

---

## AI Documentation Review
Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
Model: {self.model_name}
Description: {ModelConfig.MODELS[self.model_name]["description"]}
Temperature: {self.temperature}
Max Tokens: {model_config["generation_config"]["max_output_tokens"]}
Experimental: {model_config["experimental"]}

{review}"""
            return final_content
            
        except Exception as e:
            print(f"Warning: AI review failed - {str(e)}")
            return markdown_content
    
    def generate(self):
        """Generate both markdown and HTML documentation"""
        # Generate markdown
        markdown_content = self._generate_markdown()
        
        # Get first URL as source
        source_url = next(iter(self.api_docs.keys()))
        
        # Review documentation
        reviewed_content = self._review_documentation(source_url, markdown_content)
        
        # Save markdown
        markdown_path = os.path.join(self.output_dir, 'api_documentation.md')
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(reviewed_content)
            
        # Generate HTML
        html_content = self._generate_html(reviewed_content)
        html_path = os.path.join(self.output_dir, 'api_documentation.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
