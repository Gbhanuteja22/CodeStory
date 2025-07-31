import requests
import base64
import os
import tempfile
import git
import time
import fnmatch
from typing import Union, Set, List, Dict, Tuple, Any
from urllib.parse import urlparse
from pathlib import Path

class GitHubAPIClient:
    def __init__(self, authentication_token: str = None):
        self.auth_token = authentication_token
        self.api_base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.auth_token:
            self.session.headers.update({"Authorization": f"token {self.auth_token}"})
            
    def fetch_repository_contents(self, owner: str, repository: str, directory_path: str = "", ref: str = "main") -> List[Dict]:
        api_endpoint = f"{self.api_base_url}/repos/{owner}/{repository}/contents/{directory_path}"
        request_params = {"ref": ref}
        
        response = self.session.get(api_endpoint, params=request_params)
        response.raise_for_status()
        
        return response.json()
        
    def download_file_content(self, download_url: str) -> bytes:
        response = self.session.get(download_url)
        response.raise_for_status()
        return response.content

class RepositoryURLParser:
    @staticmethod
    def parse_github_url(repository_url: str) -> Dict[str, str]:
        if repository_url.endswith('.git'):
            repository_url = repository_url[:-4]
            
        if '/tree/' in repository_url:
            base_url, tree_part = repository_url.split('/tree/', 1)
            tree_components = tree_part.split('/')
            branch_or_commit = tree_components[0]
            subdirectory = '/'.join(tree_components[1:]) if len(tree_components) > 1 else ""
        else:
            base_url = repository_url
            branch_or_commit = "main"
            subdirectory = ""
            
        url_parts = base_url.replace('https://github.com/', '').split('/')
        if len(url_parts) < 2:
            raise ValueError(f"Invalid GitHub URL format: {repository_url}")
            
        return {
            "owner": url_parts[0],
            "repository": url_parts[1],
            "reference": branch_or_commit,
            "subdirectory": subdirectory
        }

class FilePatternMatcher:
    def __init__(self, inclusion_patterns: Set[str] = None, exclusion_patterns: Set[str] = None):
        self.inclusion_patterns = inclusion_patterns or set()
        self.exclusion_patterns = exclusion_patterns or set()
        
    def should_include_file(self, file_path: str, file_name: str) -> bool:
        if self.inclusion_patterns:
            matches_inclusion = any(fnmatch.fnmatch(file_name, pattern) for pattern in self.inclusion_patterns)
            if not matches_inclusion:
                return False
                
        if self.exclusion_patterns:
            matches_exclusion = any(fnmatch.fnmatch(file_path, pattern) for pattern in self.exclusion_patterns)
            if matches_exclusion:
                return False
                
        return True

class SSHRepositoryCloner:
    @staticmethod
    def clone_ssh_repository(ssh_url: str, target_directory: str) -> None:
        try:
            git.Repo.clone_from(ssh_url, target_directory)
        except Exception as clone_error:
            raise RuntimeError(f"SSH repository cloning failed: {clone_error}")
            
    @staticmethod
    def is_ssh_url(repository_url: str) -> bool:
        return repository_url.startswith("git@") or repository_url.endswith(".git")

def scan_github_repository(
    repo_url: str,
    token: str = None,
    max_file_size: int = 1024 * 1024,
    use_relative_paths: bool = False,
    include_patterns: Union[str, Set[str]] = None,
    exclude_patterns: Union[str, Set[str]] = None
) -> Dict[str, Any]:
    
    if isinstance(include_patterns, str):
        include_patterns = {include_patterns}
    if isinstance(exclude_patterns, str):
        exclude_patterns = {exclude_patterns}
        
    pattern_matcher = FilePatternMatcher(include_patterns, exclude_patterns)
    
    if SSHRepositoryCloner.is_ssh_url(repo_url):
        return _scan_ssh_repository(repo_url, max_file_size, pattern_matcher, use_relative_paths)
    else:
        return _scan_https_repository(repo_url, token, max_file_size, pattern_matcher, use_relative_paths)

def _scan_ssh_repository(ssh_url: str, max_file_size: int, pattern_matcher: FilePatternMatcher, use_relative_paths: bool) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as temp_directory:
        print(f"Cloning SSH repository {ssh_url} to temporary directory...")
        
        try:
            SSHRepositoryCloner.clone_ssh_repository(ssh_url, temp_directory)
        except Exception as clone_error:
            return {"files": {}, "stats": {"error": str(clone_error)}}
            
        discovered_files = {}
        skipped_files = []
        
        for root_dir, directories, file_names in os.walk(temp_directory):
            for file_name in file_names:
                absolute_path = os.path.join(root_dir, file_name)
                relative_path = os.path.relpath(absolute_path, temp_directory)
                
                try:
                    file_size = os.path.getsize(absolute_path)
                except OSError:
                    continue
                    
                if file_size > max_file_size:
                    skipped_files.append((relative_path, file_size))
                    print(f"Skipping {relative_path}: size {file_size} exceeds limit {max_file_size}")
                    continue
                    
                if not pattern_matcher.should_include_file(relative_path, file_name):
                    continue
                    
                try:
                    with open(absolute_path, 'r', encoding='utf-8') as file_handle:
                        file_content = file_handle.read()
                        
                    final_path = relative_path if use_relative_paths else absolute_path
                    discovered_files[final_path] = file_content
                    
                except Exception as read_error:
                    print(f"Error reading {relative_path}: {read_error}")
                    
        return {
            "files": discovered_files,
            "stats": {
                "total_files": len(discovered_files),
                "skipped_files": len(skipped_files),
                "skipped_details": skipped_files
            }
        }

def _scan_https_repository(https_url: str, auth_token: str, max_file_size: int, pattern_matcher: FilePatternMatcher, use_relative_paths: bool) -> Dict[str, Any]:
    try:
        url_components = RepositoryURLParser.parse_github_url(https_url)
    except Exception as parse_error:
        return {"files": {}, "stats": {"error": f"URL parsing failed: {parse_error}"}}
        
    github_client = GitHubAPIClient(auth_token)
    discovered_files = {}
    skipped_files = []
    
    def scan_directory_recursive(directory_path: str = ""):
        try:
            contents = github_client.fetch_repository_contents(
                url_components["owner"],
                url_components["repository"],
                directory_path,
                url_components["reference"]
            )
            
            for content_item in contents:
                if content_item["type"] == "file":
                    file_path = content_item["path"]
                    file_name = content_item["name"]
                    file_size = content_item["size"]
                    
                    if file_size > max_file_size:
                        skipped_files.append((file_path, file_size))
                        print(f"Skipping {file_path}: size {file_size} exceeds limit {max_file_size}")
                        continue
                        
                    if not pattern_matcher.should_include_file(file_path, file_name):
                        continue
                        
                    try:
                        file_content_bytes = github_client.download_file_content(content_item["download_url"])
                        file_content = file_content_bytes.decode('utf-8')
                        
                        final_path = file_path
                        if use_relative_paths and url_components["subdirectory"]:
                            if file_path.startswith(url_components["subdirectory"]):
                                final_path = file_path[len(url_components["subdirectory"]):].lstrip('/')
                                
                        discovered_files[final_path] = file_content
                        
                    except Exception as download_error:
                        print(f"Error downloading {file_path}: {download_error}")
                        
                elif content_item["type"] == "dir":
                    scan_directory_recursive(content_item["path"])
                    
        except Exception as scan_error:
            print(f"Error scanning directory {directory_path}: {scan_error}")
            
    initial_path = url_components["subdirectory"]
    scan_directory_recursive(initial_path)
    
    return {
        "files": discovered_files,
        "stats": {
            "total_files": len(discovered_files),
            "skipped_files": len(skipped_files),
            "skipped_details": skipped_files
        }
    }
