from pathlib import Path
from typing import Dict, List, Set, Optional
import argparse
import os
from dotenv import load_dotenv
from pipeline_orchestrator import DocumentationWorkflow

load_dotenv()

SUPPORTED_FILE_EXTENSIONS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "*Dockerfile",
    "*Makefile", "*.yaml", "*.yml",
}

IGNORED_DIRECTORIES = {
    "assets/*", "data/*", "images/*", "public/*", "static/*", "temp/*",
    "*docs/*", "*venv/*", "*.venv/*", "*test*", "*tests/*", "*examples/*",
    "v1/*", "*dist/*", "*build/*", "*experimental/*", "*deprecated/*",
    "*misc/*", "*legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*",
    "*obj/*", "*bin/*", "*node_modules/*", "*.log"
}

class DocumentationGenerator:
    def __init__(self):
        self.workspace_settings = {}
        
    def configure_workspace(self, configuration: Dict) -> None:
        self.workspace_settings = configuration
        
    def build_documentation(self) -> str:
        workflow = DocumentationWorkflow()
        workflow.execute(self.workspace_settings)
        return self.workspace_settings.get("documentation_output_path", "")

def parse_command_arguments():
    argument_parser = argparse.ArgumentParser(
        description="Create comprehensive documentation for any software project"
    )
    
    source_selection = argument_parser.add_mutually_exclusive_group(required=True)
    source_selection.add_argument(
        "--repo", 
        help="Public GitHub repository URL for documentation generation"
    )
    source_selection.add_argument(
        "--dir", 
        help="Local filesystem path to analyze and document"
    )
    
    argument_parser.add_argument(
        "-n", "--name", 
        help="Custom project identifier (auto-detected if not provided)"
    )
    argument_parser.add_argument(
        "-t", "--token", 
        help="GitHub API authentication token (reads GITHUB_TOKEN env var by default)"
    )
    argument_parser.add_argument(
        "-o", "--output", 
        default="output", 
        help="Documentation output directory path (default: ./output)"
    )
    argument_parser.add_argument(
        "-i", "--include", 
        nargs="+", 
        help="File patterns to include in analysis (e.g., '*.py' '*.js')"
    )
    argument_parser.add_argument(
        "-e", "--exclude", 
        nargs="+", 
        help="File patterns to exclude from analysis (e.g., 'tests/*' 'docs/*')"
    )
    argument_parser.add_argument(
        "-s", "--max-size", 
        type=int, 
        default=100000, 
        help="Maximum individual file size in bytes (default: 100KB)"
    )
    argument_parser.add_argument(
        "--language", 
        default="english", 
        help="Natural language for generated documentation (default: english)"
    )
    argument_parser.add_argument(
        "--no-cache", 
        action="store_true", 
        help="Disable AI response caching for fresh results"
    )
    argument_parser.add_argument(
        "--max-abstractions", 
        type=int, 
        default=10, 
        help="Maximum number of core concepts to identify (default: 10)"
    )
    
    return argument_parser.parse_args()

def setup_authentication(parsed_args):
    api_token = None
    if parsed_args.repo:
        api_token = parsed_args.token or os.environ.get('GITHUB_TOKEN')
        if not api_token:
            print("Notice: No GitHub authentication token provided. API rate limits may apply.")
    return api_token

def initialize_workspace_configuration(parsed_args, api_token):
    return {
        "source_repository": parsed_args.repo,
        "local_filesystem_path": parsed_args.dir,
        "project_identifier": parsed_args.name,
        "github_api_token": api_token,
        "documentation_output_path": parsed_args.output,
        "included_file_patterns": set(parsed_args.include) if parsed_args.include else SUPPORTED_FILE_EXTENSIONS,
        "excluded_file_patterns": set(parsed_args.exclude) if parsed_args.exclude else IGNORED_DIRECTORIES,
        "maximum_file_size_bytes": parsed_args.max_size,
        "target_language": parsed_args.language,
        "enable_ai_caching": not parsed_args.no_cache,
        "maximum_concept_count": parsed_args.max_abstractions,
        "discovered_files": [],
        "identified_concepts": [],
        "concept_relationships": {},
        "chapter_sequence": [],
        "generated_chapters": [],
        "final_documentation_path": None
    }

def display_generation_status(configuration):
    source_description = configuration["source_repository"] or configuration["local_filesystem_path"]
    language_name = configuration["target_language"].capitalize()
    caching_status = "Disabled" if not configuration["enable_ai_caching"] else "Enabled"
    max_chapters = configuration["maximum_concept_count"]
    
    print(f"🚀 Generating documentation for: {source_description}")
    print(f"🌍 Target language: {language_name}")
    print(f"💾 AI response caching: {caching_status}")
    print(f"📊 Maximum chapters to generate: {max_chapters}")
    print(f"─" * 50)

def execute_documentation_generation():
    command_arguments = parse_command_arguments()
    authentication_token = setup_authentication(command_arguments)
    workspace_config = initialize_workspace_configuration(command_arguments, authentication_token)
    
    display_generation_status(workspace_config)
    
    documentation_builder = DocumentationGenerator()
    documentation_builder.configure_workspace(workspace_config)
    output_location = documentation_builder.build_documentation()
    
    return output_location

if __name__ == "__main__":
    execute_documentation_generation()
