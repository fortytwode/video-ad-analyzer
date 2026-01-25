"""
External prompt management and templating system
"""
import re
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self, prompts_directory=None):
        """Initialize prompt manager with prompts directory"""
        if prompts_directory:
            self.prompts_dir = Path(prompts_directory)
        else:
            # Default to prompts folder at project root (two levels up from core/)
            self.prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        
        self.loaded_prompts = {}
        self.initialized = True
        
        # Load all prompt files on initialization
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompt files from the prompts directory and subdirectories"""
        try:
            if not self.prompts_dir.exists():
                logger.warning(f"Prompts directory not found: {self.prompts_dir}")
                return
            
            # Load from root directory
            for prompt_file in self.prompts_dir.glob("*.md"):
                file_key = prompt_file.stem  # filename without extension
                self.loaded_prompts[file_key] = self._parse_prompt_file(prompt_file)
                logger.info(f"Loaded prompts from {prompt_file.name}")
            
            # Load from subdirectories (for strategic_analysis, etc.)
            for subdir in self.prompts_dir.iterdir():
                if subdir.is_dir():
                    subdir_name = subdir.name
                    if subdir_name not in self.loaded_prompts:
                        self.loaded_prompts[subdir_name] = {}
                    
                    for prompt_file in subdir.glob("*.md"):
                        file_key = prompt_file.stem
                        # Read entire file as template (for strategic_analysis prompts)
                        with open(prompt_file, 'r', encoding='utf-8') as f:
                            self.loaded_prompts[subdir_name][file_key] = f.read()
                        logger.info(f"Loaded prompts from {subdir_name}/{prompt_file.name}")
                
        except Exception as e:
            logger.error(f"Error loading prompts: {str(e)}")
    
    def _parse_prompt_file(self, file_path):
        """Parse a markdown prompt file and extract templates"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract templates using regex
            # Look for ### Template: template_name followed by ``` content ```
            template_pattern = r'### Template: (\w+)\s*```(.*?)```'
            templates = {}
            
            matches = re.findall(template_pattern, content, re.DOTALL)
            for template_name, template_content in matches:
                # Clean up the template content
                cleaned_content = template_content.strip()
                templates[template_name] = cleaned_content
                
            return templates
            
        except Exception as e:
            logger.error(f"Error parsing prompt file {file_path}: {str(e)}")
            return {}
    
    def get_prompt(self, template_name: str, variables=None):
        """
        Get a formatted prompt template with variable substitution
        
        Args:
            template_name: Name of the template (e.g., 'spoken_hooks', 'fomo_and_social')
            variables: Dictionary of variables to substitute in template
            
        Returns:
            Formatted prompt string
        """
        variables = variables or {}
        
        try:
            # Find the template across all loaded files
            template_content = None
            for file_key, templates in self.loaded_prompts.items():
                if template_name in templates:
                    template_content = templates[template_name]
                    break
            
            if not template_content:
                logger.error(f"Template '{template_name}' not found in any prompt file")
                return f"Template '{template_name}' not found"
            
            # Substitute variables using {{variable_name}} format
            formatted_prompt = self._substitute_variables(template_content, variables)
            
            return formatted_prompt
            
        except Exception as e:
            logger.error(f"Error getting prompt '{template_name}': {str(e)}")
            return f"Error loading template: {str(e)}"
    
    def load_variations_prompt(self, analysis_json: str) -> str:
        """
        Load and format the variations generation prompt.
        
        Args:
            analysis_json: JSON string of the complete analysis
            
        Returns:
            str: Formatted prompt ready for Gemini
        """
        return self.get_prompt('variations_generation', {
            'analysis_json': analysis_json
        })
    
    def _substitute_variables(self, template: str, variables: dict):
        """
        Substitute variables in template using {{variable_name}} format
        
        Args:
            template: Template string with {{variable}} placeholders
            variables: Dictionary of variable values
            
        Returns:
            Template with variables substituted
        """
        try:
            # Use regex to find all {{variable_name}} patterns
            def replace_var(match):
                var_name = match.group(1)
                if var_name in variables:
                    return str(variables[var_name])
                else:
                    logger.warning(f"Variable '{var_name}' not provided, leaving placeholder")
                    return match.group(0)  # Return original {{var_name}} if not found
            
            # Replace all {{variable_name}} patterns
            result = re.sub(r'\{\{(\w+)\}\}', replace_var, template)
            
            return result
            
        except Exception as e:
            logger.error(f"Error substituting variables: {str(e)}")
            return template
    
    def list_available_templates(self):
        """Return a list of all available template names"""
        templates = []
        for file_key, file_templates in self.loaded_prompts.items():
            for template_name in file_templates.keys():
                templates.append(f"{file_key}:{template_name}")
        return templates
    
    def get_template_preview(self, template_name: str):
        """Get a preview of a template without variable substitution"""
        for file_key, templates in self.loaded_prompts.items():
            if template_name in templates:
                return templates[template_name][:200] + "..." if len(templates[template_name]) > 200 else templates[template_name]
        return "Template not found"
    
    def get_template(self, category: str, template_name: str):
        """
        Get a template from a specific category/subdirectory.
        
        Args:
            category: Subdirectory name (e.g., 'strategic_analysis')
            template_name: Template filename without extension (e.g., 'pattern_normalization')
        
        Returns:
            Template string or None if not found
        """
        if category in self.loaded_prompts:
            if isinstance(self.loaded_prompts[category], dict):
                return self.loaded_prompts[category].get(template_name)
        return None