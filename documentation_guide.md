# AI-Powered Documentation Generator

An intelligent system that automatically creates comprehensive, beginner-friendly documentation for software projects by analyzing codebases and generating structured tutorials.

## Features

- **Smart Code Analysis**: Automatically identifies core architectural concepts and their relationships
- **Multi-Language Support**: Generate documentation in multiple natural languages
- **Comprehensive Tutorial Generation**: Creates step-by-step tutorials with examples and diagrams
- **GitHub Integration**: Works with both public repositories and local directories
- **AI Response Caching**: Optimizes performance by caching AI responses
- **Flexible File Filtering**: Customizable inclusion/exclusion patterns

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r dependencies.txt
   ```
3. Set up your AI API key:
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```
4. (Optional) Set up GitHub token for better rate limits:
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   ```

## Usage

### Basic Usage

Generate documentation for a GitHub repository:
```bash
python tutorial_builder.py --repo https://github.com/owner/repository
```

Generate documentation for a local directory:
```bash
python tutorial_builder.py --dir /path/to/your/project
```

### Advanced Options

```bash
python tutorial_builder.py --repo https://github.com/owner/repo \
  --name "Custom Project Name" \
  --output ./documentation \
  --language spanish \
  --max-abstractions 8 \
  --include "*.py" "*.js" \
  --exclude "tests/*" "docs/*" \
  --max-size 150000
```

### Parameters

- `--repo`: GitHub repository URL
- `--dir`: Local directory path
- `--name`: Custom project name (auto-detected if not provided)
- `--token`: GitHub API token (or use GITHUB_TOKEN env var)
- `--output`: Output directory (default: ./output)
- `--include`: File patterns to include
- `--exclude`: File patterns to exclude
- `--max-size`: Maximum file size in bytes
- `--language`: Documentation language (default: english)
- `--no-cache`: Disable AI response caching
- `--max-abstractions`: Maximum concepts to identify (default: 10)

## Architecture

The system consists of several specialized components:

### Core Modules

- **`tutorial_builder.py`**: Main entry point and argument parsing
- **`pipeline_orchestrator.py`**: Workflow coordination and execution
- **`documentation_processors.py`**: Core processing nodes for the documentation pipeline

### Supporting Modules

- **`ai_interface/`**: AI model interaction and response management
  - `model_connector.py`: Language model communication and caching
- **`file_operations/`**: File system and repository operations
  - `repository_scanner.py`: GitHub repository scanning and file retrieval
  - `filesystem_explorer.py`: Local directory exploration and file discovery

### Processing Pipeline

1. **Code Retrieval**: Scans repositories or directories for relevant files
2. **Concept Identification**: Uses AI to identify core architectural concepts
3. **Relationship Analysis**: Analyzes how concepts interact and depend on each other
4. **Chapter Organization**: Determines optimal order for explaining concepts
5. **Content Generation**: Creates detailed tutorial chapters with examples
6. **Documentation Assembly**: Combines everything into a cohesive tutorial

## Output Structure

The generated documentation includes:

- **`index.md`**: Overview with project summary and navigation
- **Chapter files**: Individual concept explanations with:
  - Clear explanations and analogies
  - Code examples and walkthroughs
  - Mermaid diagrams for complex concepts
  - Cross-references between chapters

## Customization

### File Patterns

Default included files:
- Source code: `*.py`, `*.js`, `*.ts`, `*.go`, `*.java`, `*.c`, `*.cpp`
- Documentation: `*.md`, `*.rst`
- Configuration: `*.yaml`, `*.yml`, `Dockerfile`, `Makefile`

Default excluded paths:
- Build/dist directories, node_modules, test files
- Assets, images, temporary files

### Language Support

The system supports generating documentation in multiple languages. The AI will translate:
- Concept names and descriptions
- Tutorial content and explanations
- Relationship labels and summaries

Code syntax and technical terms remain in their original form for clarity.

## Requirements

- Python 3.7+
- Internet connection for AI model access
- Valid Gemini API key
- (Optional) GitHub token for enhanced repository access

## Contributing

This codebase demonstrates modern Python patterns including:
- Type hints for better code clarity
- Modular architecture with clear separation of concerns
- Comprehensive error handling
- Configurable processing pipeline
- Efficient caching mechanisms

Feel free to extend the system with additional AI models, output formats, or processing capabilities.
