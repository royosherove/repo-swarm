#!/usr/bin/env python3
"""
Fetch all repositories from the configured GitHub organization
and update repos.json with their information while preserving existing entries.
Only includes non-archived repositories with commits in the past 1 year.
"""

import json
import os
import sys
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Add src directory to path to import config
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from investigator.core.config import Config


def detect_repo_type(repo_data: dict, repo_languages: dict) -> str:
    """
    Detect repository type based on primary language and repository name patterns.
    Uses simplified heuristics based on GitHub API data.
    """
    # Get primary language (handle None values)
    language = repo_data.get("language")
    primary_language = language.lower() if language else ""
    repo_name = repo_data.get("name", "").lower()
    description = (repo_data.get("description") or "").lower()
    
    # Check for mobile indicators
    if any(keyword in repo_name for keyword in ["mobile", "ios", "android", "react-native"]):
        return "mobile"
    if primary_language in ["swift", "kotlin", "java"] and "android" in repo_name:
        return "mobile"
    if primary_language == "swift":
        return "mobile"
    
    # Check for infrastructure indicators
    if any(keyword in repo_name for keyword in ["terraform", "infra", "helm", "k8s", "kubernetes", "ansible", "cloudformation"]):
        return "infra-as-code"
    if primary_language == "hcl":  # Terraform's HCL language
        return "infra-as-code"
    
    # Check for library/SDK indicators
    if any(keyword in repo_name for keyword in ["sdk", "lib", "library", "client", "api-client", "package"]):
        return "libraries"
    if any(keyword in description for keyword in ["sdk", "library", "package", "client library"]):
        return "libraries"
    
    # Check for frontend indicators
    if primary_language in ["javascript", "typescript"]:
        # More specific frontend checks
        if any(keyword in repo_name for keyword in ["frontend", "ui", "web", "portal", "dashboard", "admin"]):
            return "frontend"
        # Check if it's not a backend Node.js service
        if not any(keyword in repo_name for keyword in ["service", "api", "server", "backend", "worker"]):
            # Default JS/TS to frontend unless clearly backend
            if "react" in repo_name or "vue" in repo_name or "angular" in repo_name:
                return "frontend"
    if primary_language == "vue":
        return "frontend"
    
    # Check for backend indicators
    if primary_language in ["python", "ruby", "go", "java", "c#", "rust"]:
        return "backend"
    if any(keyword in repo_name for keyword in ["service", "api", "server", "backend", "worker", "processor"]):
        return "backend"
    
    # Node.js services (JavaScript/TypeScript that are backends)
    if primary_language in ["javascript", "typescript"]:
        if any(keyword in repo_name for keyword in ["service", "api", "server", "backend", "worker"]):
            return "backend"
    
    # Default to generic
    return "generic"


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variables."""
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_ADMIN_ORG_READ_TOKEN")
    if not token:
        print("Warning: No GitHub token found in environment variables.")
        print("Set GITHUB_TOKEN or GITHUB_ADMIN_ORG_READ_TOKEN for better rate limits.")
    return token


def load_skip_repos(skip_file: str) -> Dict[str, str]:
    """
    Load the skip_repos.json file containing repositories to skip.
    
    Args:
        skip_file: Path to skip_repos.json file
    
    Returns:
        Dictionary mapping repo names to skip reasons
    """
    try:
        with open(skip_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_skip_repos(skip_file: str, skip_repos: Dict[str, str]) -> None:
    """
    Save the skip_repos.json file.
    
    Args:
        skip_file: Path to skip_repos.json file
        skip_repos: Dictionary mapping repo names to skip reasons
    """
    with open(skip_file, 'w') as f:
        json.dump(skip_repos, f, indent=2)


def has_recent_activity(repo: Dict, org_name: str, token: Optional[str] = None, years: int = 3) -> bool:
    """
    Check if a repository has had commits in the past N years.
    
    Args:
        repo: Repository data from GitHub API
        org_name: GitHub organization name
        token: GitHub personal access token
        years: Number of years to look back for activity
    
    Returns:
        True if the repository has recent commits, False otherwise
    """
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # Calculate date N years ago
    cutoff_date = datetime.now() - timedelta(days=365 * years)
    since_date = cutoff_date.isoformat() + "Z"
    
    repo_name = repo["name"]
    url = f"https://api.github.com/repos/{org_name}/{repo_name}/commits"
    params = {
        "since": since_date,
        "per_page": 1  # We only need to know if there's at least one commit
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 409:  # Empty repository
            return False
        if response.status_code == 404:  # Repository not found or no access
            return False
        response.raise_for_status()
        
        # If we get any commits back, the repo has recent activity
        commits = response.json()
        return len(commits) > 0
        
    except requests.exceptions.RequestException:
        # If we can't check, assume it's active to avoid accidentally filtering it out
        return True


def fetch_all_organization_repos(org_name: str, token: Optional[str] = None) -> List[Dict]:
    """
    Fetch ALL repositories from a GitHub organization or user account.
    
    Args:
        org_name: GitHub organization name or username
        token: GitHub personal access token (optional, but recommended)
    
    Returns:
        List of repository data dictionaries
    """
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    # First, determine if this is a user or organization
    account_type = _detect_account_type(org_name, headers)
    
    if account_type == "user":
        base_url = f"https://api.github.com/users/{org_name}/repos"
        print(f"📍 Detected '{org_name}' as a GitHub user account")
    elif account_type == "organization":
        base_url = f"https://api.github.com/orgs/{org_name}/repos"
        print(f"📍 Detected '{org_name}' as a GitHub organization")
    else:
        print(f"❌ Could not determine account type for '{org_name}' or account not found")
        return []
    
    repos = []
    page = 1
    per_page = 100  # GitHub API max is 100 per page
    
    while True:
        params = {
            "per_page": per_page,
            "page": page
        }
        
        try:
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
                
            repos.extend(page_repos)
            
            # Check rate limit
            if "X-RateLimit-Remaining" in response.headers:
                remaining = int(response.headers["X-RateLimit-Remaining"])
                if remaining < 100:
                    print(f"Warning: GitHub API rate limit low ({remaining} remaining)")
                    if remaining < 10:
                        print("Rate limit too low, stopping fetch")
                        break
            
            print(f"  Fetched page {page} ({len(page_repos)} repos, total: {len(repos)})")
            page += 1
            time.sleep(0.2)  # Be nice to the API
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories: {e}")
            break
    
    return repos


def _detect_account_type(account_name: str, headers: dict) -> str:
    """
    Detect whether the account is a user or organization.
    
    Args:
        account_name: GitHub account name to check
        headers: HTTP headers for the request
    
    Returns:
        "user", "organization", or "unknown"
    """
    try:
        # Try to get account information
        response = requests.get(f"https://api.github.com/users/{account_name}", headers=headers)
        
        if response.status_code == 200:
            account_data = response.json()
            account_type = account_data.get("type", "").lower()
            
            if account_type == "user":
                return "user"
            elif account_type == "organization":
                return "organization"
        
        return "unknown"
        
    except requests.exceptions.RequestException:
        return "unknown"


def update_repos_json(repos: List[Dict], existing_repos_file: str) -> None:
    """
    Update repos.json with new repository data while preserving ALL existing entries
    and their metadata.
    
    Args:
        repos: List of repository data from GitHub API
        existing_repos_file: Path to existing repos.json file
    """
    # Load existing repos.json
    try:
        with open(existing_repos_file, 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"repos.json file not found at {existing_repos_file}. Please ensure the file exists before running the update script.")
    # Start with ALL existing repositories (preserve everything that's already there)
    all_repos = existing_data.get("repositories", {}).copy()
    
    # Process new repositories from GitHub API
    new_repos_added = 0
    skipped_repos = 0
    
    for repo in repos:
        repo_name = repo["name"]
        
        # Skip if repository already exists in the file (preserve existing metadata)
        if repo_name in all_repos:
            skipped_repos += 1
            continue
        
        # Detect repository type for new repos only
        repo_type = detect_repo_type(repo, repo.get("languages", {}))
        
        # Add new repository entry
        all_repos[repo_name] = {
            "url": repo["html_url"],
            "description": repo.get("description", "No description available") or "No description available",
            "type": repo_type
        }
        new_repos_added += 1
    
    # Update the data structure
    default_repo = existing_data.get("default")
    if default_repo is None:
        raise ValueError("The 'default' field in repos.json cannot be None. Please set a valid default repository URL.")
    
    updated_data = {
        "default": existing_data.get("default", Config.DEFAULT_REPO_URL),
        "_comment": existing_data.get("_comment", "Available types: generic, backend, frontend, mobile, infra-as-code, libraries"),
        "repositories": all_repos
    }
    
    # Write back to file
    with open(existing_repos_file, 'w') as f:
        json.dump(updated_data, f, indent=2)
    
    print(f"✅ Successfully updated {existing_repos_file}")
    print(f"   - Preserved {len(existing_data.get('repositories', {}))} existing repositories")
    print(f"   - Added {new_repos_added} new repositories")
    print(f"   - Skipped {skipped_repos} repositories (already exist)")
    print(f"   - Total repositories: {len(all_repos)}")


def main():
    """Main function to fetch and update repository list."""
    org_name = Config.DEFAULT_ORG_NAME
    
    # Check if account name is properly configured
    if not org_name or org_name in ["your-org", "example-org"]:
        print("❌ GitHub account name not configured!")
        print("Please set the DEFAULT_ORG_NAME environment variable to your GitHub username or organization name.")
        print("Examples:")
        print("  export DEFAULT_ORG_NAME=my-company     # For organization")
        print("  export DEFAULT_ORG_NAME=my-username    # For user account")
        print("Or update your .env file with: DEFAULT_ORG_NAME=your-account-name")
        sys.exit(1)
    
    repos_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts", "repos.json"
    )
    skip_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prompts", "skip_repos.json"
    )
    
    print(f"🚀 Starting repository sync for GitHub account '{org_name}'...")
    print("Filtering: non-archived repos with commits in the past 1 year.")
    print("Existing repositories and their metadata will be preserved.\n")
    
    # Load existing repositories
    try:
        with open(repos_file, 'r') as f:
            existing_data = json.load(f)
            existing_repo_names = set(existing_data.get("repositories", {}).keys())
            print(f"📚 Loaded {len(existing_repo_names)} existing repositories from repos.json")
    except FileNotFoundError:
        existing_repo_names = set()
    
    # Load existing skip list
    skip_repos = load_skip_repos(skip_file)
    if skip_repos:
        print(f"📋 Loaded {len(skip_repos)} previously skipped repositories")
    
    # Get GitHub token
    token = get_github_token()
    if not token:
        print("⚠️  Without a GitHub token, you may hit rate limits quickly.")
        print("   Consider setting GITHUB_TOKEN environment variable.\n")
    
    # Fetch all repositories
    all_repos = fetch_all_organization_repos(org_name, token)
    
    if not all_repos:
        print("❌ Failed to fetch repositories")
        sys.exit(1)
    
    print(f"\n📊 Fetched {len(all_repos)} total repositories")
    
    # Track new skips
    new_skips = {}
    active_repos = []
    
    # Process repositories
    repos_to_check = []
    skipped_from_cache = 0
    already_in_repos_json = 0
    
    for repo in all_repos:
        repo_name = repo["name"]
        
        # Check if repo is already in repos.json (no need to check activity)
        if repo_name in existing_repo_names:
            already_in_repos_json += 1
            continue
        
        # Check if repo is in skip list
        if repo_name in skip_repos:
            skipped_from_cache += 1
            continue
        
        # Check if archived
        if repo.get("archived", False):
            new_skips[repo_name] = "archived"
            print(f"   - Skipping {repo_name} (archived)")
            continue
        
        # Add to list for activity check
        repos_to_check.append(repo)
    
    if already_in_repos_json > 0:
        print(f"✓ {already_in_repos_json} repositories already in repos.json (no activity check needed)")
    
    if skipped_from_cache > 0:
        print(f"⏭️  Skipped {skipped_from_cache} repositories from skip list")
    
    # Check activity for non-archived, non-skipped, non-existing repos
    if repos_to_check:
        print(f"🔍 Checking activity for {len(repos_to_check)} new repositories...")
        print("   (This may take a few minutes...)")
        
        for i, repo in enumerate(repos_to_check, 1):
            repo_name = repo["name"]
            
            if has_recent_activity(repo, org_name, token, years=1):
                active_repos.append(repo)
            else:
                new_skips[repo_name] = f"no commits in past 1 year"
                print(f"   - Skipping {repo_name} (no commits in past 1 year)")
            
            if i % 20 == 0:
                print(f"   Processed {i}/{len(repos_to_check)} repositories...")
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
    
    # Update skip list with new skips
    if new_skips:
        skip_repos.update(new_skips)
        save_skip_repos(skip_file, skip_repos)
        print(f"💾 Added {len(new_skips)} new repositories to skip list")
    
    print(f"🗂️  Total skipped repositories: {len(skip_repos)}")
    print(f"✅ {len(active_repos)} new active repositories to add")
    
    # Update repos.json (only with new active repos, existing ones are preserved)
    update_repos_json(active_repos, repos_file)
    
    # Print summary of repository types
    with open(repos_file, 'r') as f:
        final_data = json.load(f)
    
    type_counts = {}
    for repo_name, repo_info in final_data["repositories"].items():
        repo_type = repo_info.get("type", "generic")
        type_counts[repo_type] = type_counts.get(repo_type, 0) + 1
    
    print("\n📈 Repository type distribution:")
    for repo_type, count in sorted(type_counts.items()):
        print(f"   - {repo_type}: {count}")


if __name__ == "__main__":
    main()
