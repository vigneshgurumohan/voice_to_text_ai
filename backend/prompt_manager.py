"""
Prompt Manager for Voice-to-Text AI Application

This module handles the dynamic loading and management of prompts from text files.
It provides functionality to list, load, and manage prompts without requiring application restarts.
"""

import os
import glob
from typing import Dict, List, Optional
from pathlib import Path


class PromptManager:
    """Manages prompts loaded from text files in the prompts directory."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize the PromptManager.
        
        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = Path(prompts_dir)
        self.prompts_cache: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load all prompt files from the prompts directory."""
        if not self.prompts_dir.exists():
            print(f"Warning: Prompts directory {self.prompts_dir} does not exist")
            return
        
        # Clear existing cache
        self.prompts_cache.clear()
        
        # Load all .txt files in the prompts directory
        for prompt_file in self.prompts_dir.rglob("*.txt"):
            if prompt_file.name == "README.md":
                continue  # Skip README files
                
            prompt_name = self._get_prompt_name(prompt_file)
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    self.prompts_cache[prompt_name] = content
                    print(f"Loaded prompt: {prompt_name}")
            except Exception as e:
                print(f"Error loading prompt {prompt_file}: {e}")
    
    def _get_prompt_name(self, prompt_file: Path) -> str:
        """
        Extract prompt name from file path.
        
        Args:
            prompt_file: Path to the prompt file
            
        Returns:
            Prompt name (e.g., 'general_summary', 'custom_templates.project_plan')
        """
        # Get relative path from prompts directory
        relative_path = prompt_file.relative_to(self.prompts_dir)
        
        # Convert path to dot notation (e.g., custom_templates/project_plan.txt -> custom_templates.project_plan)
        prompt_name = str(relative_path).replace('/', '.').replace('\\', '.').replace('.txt', '')
        
        return prompt_name
    
    def reload_prompts(self) -> None:
        """Reload all prompts from the prompts directory."""
        print("Reloading prompts...")
        self._load_prompts()
        print(f"Loaded {len(self.prompts_cache)} prompts")
    
    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """
        Get a specific prompt by name.
        
        Args:
            prompt_name: Name of the prompt (e.g., 'general_summary')
            
        Returns:
            Prompt content or None if not found
        """
        return self.prompts_cache.get(prompt_name)
    
    def get_all_prompts(self) -> Dict[str, str]:
        """
        Get all loaded prompts.
        
        Returns:
            Dictionary of prompt names to content
        """
        return self.prompts_cache.copy()
    
    def list_prompts(self) -> List[str]:
        """
        List all available prompt names.
        
        Returns:
            List of prompt names
        """
        return list(self.prompts_cache.keys())
    
    def add_prompt(self, prompt_name: str, content: str) -> bool:
        """
        Add a new prompt file.
        
        Args:
            prompt_name: Name for the prompt (will be used as filename)
            content: Prompt content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle custom templates (they go in custom_templates subdirectory)
            if prompt_name.startswith('custom_templates.'):
                # Extract the actual filename from the prompt name
                actual_name = prompt_name.replace('custom_templates.', '')
                # Create custom_templates directory
                custom_dir = self.prompts_dir / "custom_templates"
                custom_dir.mkdir(exist_ok=True)
                # Create the prompt file in custom_templates directory
                prompt_file = custom_dir / f"{actual_name}.txt"
            else:
                # Ensure prompts directory exists
                self.prompts_dir.mkdir(exist_ok=True)
                # Create the prompt file in main prompts directory
                prompt_file = self.prompts_dir / f"{prompt_name}.txt"
            
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Reload prompts to include the new one
            self.reload_prompts()
            return True
        except Exception as e:
            print(f"Error adding prompt {prompt_name}: {e}")
            return False
    
    def update_prompt(self, prompt_name: str, content: str) -> bool:
        """
        Update an existing prompt.
        
        Args:
            prompt_name: Name of the prompt to update
            content: New prompt content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the prompt file
            prompt_file = None
            for file_path in self.prompts_dir.rglob("*.txt"):
                if self._get_prompt_name(file_path) == prompt_name:
                    prompt_file = file_path
                    break
            
            if not prompt_file:
                print(f"Prompt {prompt_name} not found")
                return False
            
            # Update the file
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update cache
            self.prompts_cache[prompt_name] = content
            return True
        except Exception as e:
            print(f"Error updating prompt {prompt_name}: {e}")
            return False
    
    def delete_prompt(self, prompt_name: str) -> bool:
        """
        Delete a prompt file.
        
        Args:
            prompt_name: Name of the prompt to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the prompt file
            prompt_file = None
            for file_path in self.prompts_dir.rglob("*.txt"):
                if self._get_prompt_name(file_path) == prompt_name:
                    prompt_file = file_path
                    break
            
            if not prompt_file:
                print(f"Prompt {prompt_name} not found")
                return False
            
            # Delete the file
            prompt_file.unlink()
            
            # Remove from cache
            if prompt_name in self.prompts_cache:
                del self.prompts_cache[prompt_name]
            
            # If it was a custom template and the directory is now empty, remove the directory
            if prompt_name.startswith('custom_templates.'):
                custom_dir = self.prompts_dir / "custom_templates"
                if custom_dir.exists() and not any(custom_dir.iterdir()):
                    custom_dir.rmdir()
                    print(f"Removed empty custom_templates directory")
            
            return True
        except Exception as e:
            print(f"Error deleting prompt {prompt_name}: {e}")
            return False
    
    def format_prompt(self, prompt_name: str, **kwargs) -> Optional[str]:
        """
        Format a prompt with dynamic content.
        
        Args:
            prompt_name: Name of the prompt to format
            **kwargs: Variables to substitute in the prompt
            
        Returns:
            Formatted prompt content or None if not found
        """
        prompt_content = self.get_prompt(prompt_name)
        if not prompt_content:
            return None
        
        try:
            return prompt_content.format(**kwargs)
        except KeyError as e:
            print(f"Error formatting prompt {prompt_name}: Missing variable {e}")
            return prompt_content


# Global prompt manager instance
prompt_manager = PromptManager()


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    return prompt_manager


def reload_prompts() -> None:
    """Reload all prompts."""
    prompt_manager.reload_prompts()


def get_prompt(prompt_name: str) -> Optional[str]:
    """Get a specific prompt."""
    return prompt_manager.get_prompt(prompt_name)


def format_prompt(prompt_name: str, **kwargs) -> Optional[str]:
    """Format a prompt with dynamic content."""
    return prompt_manager.format_prompt(prompt_name, **kwargs)


def list_prompts() -> List[str]:
    """List all available prompts."""
    return prompt_manager.list_prompts()


if __name__ == "__main__":
    # Test the prompt manager
    print("Available prompts:")
    for prompt_name in list_prompts():
        print(f"  - {prompt_name}")
    
    print(f"\nTotal prompts loaded: {len(list_prompts())}") 