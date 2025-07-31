import os
import fnmatch
from typing import Dict, Set, Union, Any
from pathlib import Path

class LocalFileSystemExplorer:
    def __init__(self, root_directory: str):
        self.root_path = Path(root_directory)
        if not self.root_path.exists() or not self.root_path.is_dir():
            raise ValueError(f"Invalid directory path: {root_directory}")
            
    def discover_files(
        self,
        inclusion_patterns: Set[str] = None,
        exclusion_patterns: Set[str] = None,
        max_file_size: int = 1024 * 1024,
        use_relative_paths: bool = False
    ) -> Dict[str, Any]:
        
        discovered_files = {}
        skipped_files = []
        
        pattern_checker = FilePatternChecker(inclusion_patterns, exclusion_patterns)
        
        for file_path in self.root_path.rglob('*'):
            if not file_path.is_file():
                continue
                
            try:
                file_size = file_path.stat().st_size
            except OSError as size_error:
                print(f"Cannot access file size for {file_path}: {size_error}")
                continue
                
            if file_size > max_file_size:
                relative_path = file_path.relative_to(self.root_path)
                skipped_files.append((str(relative_path), file_size))
                print(f"Skipping {relative_path}: size {file_size} exceeds limit {max_file_size}")
                continue
                
            relative_file_path = file_path.relative_to(self.root_path)
            file_name = file_path.name
            
            if not pattern_checker.matches_criteria(str(relative_file_path), file_name):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file_handle:
                    file_content = file_handle.read()
                    
                final_path = str(relative_file_path) if use_relative_paths else str(file_path)
                discovered_files[final_path] = file_content
                
            except Exception as read_error:
                print(f"Error reading {relative_file_path}: {read_error}")
                
        return {
            "files": discovered_files,
            "stats": {
                "total_files": len(discovered_files),
                "skipped_files": len(skipped_files),
                "skipped_details": skipped_files
            }
        }

class FilePatternChecker:
    def __init__(self, inclusion_patterns: Set[str] = None, exclusion_patterns: Set[str] = None):
        self.inclusion_patterns = inclusion_patterns or set()
        self.exclusion_patterns = exclusion_patterns or set()
        
    def matches_criteria(self, file_path: str, file_name: str) -> bool:
        if self.inclusion_patterns:
            inclusion_match = any(
                fnmatch.fnmatch(file_name, pattern) for pattern in self.inclusion_patterns
            )
            if not inclusion_match:
                return False
                
        if self.exclusion_patterns:
            exclusion_match = any(
                fnmatch.fnmatch(file_path, pattern) for pattern in self.exclusion_patterns
            )
            if exclusion_match:
                return False
                
        return True

def explore_local_directory(
    directory: str,
    include_patterns: Union[str, Set[str]] = None,
    exclude_patterns: Union[str, Set[str]] = None,
    max_file_size: int = 1024 * 1024,
    use_relative_paths: bool = False
) -> Dict[str, Any]:
    
    if isinstance(include_patterns, str):
        include_patterns = {include_patterns}
    if isinstance(exclude_patterns, str):
        exclude_patterns = {exclude_patterns}
        
    try:
        filesystem_explorer = LocalFileSystemExplorer(directory)
        return filesystem_explorer.discover_files(
            inclusion_patterns=include_patterns,
            exclusion_patterns=exclude_patterns,
            max_file_size=max_file_size,
            use_relative_paths=use_relative_paths
        )
    except Exception as exploration_error:
        return {
            "files": {},
            "stats": {"error": str(exploration_error)}
        }
