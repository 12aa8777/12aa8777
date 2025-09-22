import requests
import os
import re
from datetime import datetime

GH_USER = os.environ.get("GH_USER")
GH_TOKEN = os.environ.get("GH_TOKEN")
headers = {"Authorization": f"token {GH_TOKEN}"}

def get_repos(user):
    url = f"https://api.github.com/users/{user}/repos?per_page=100&type=public"
    repos = []
    while url:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        repos.extend(resp.json())
        url = resp.links.get("next", {}).get("url")
    return repos

def get_commit_count(repo_name):
    url = f"https://api.github.com/repos/{GH_USER}/{repo_name}/commits?per_page=1"
    resp = requests.get(url, headers=headers)
    if "Link" in resp.headers:
        # Find last page number from "rel=last"
        import re
        last_page = int(re.findall(r'&page=(\\d+)>; rel=\"last\"', resp.headers["Link"])[0])
        return last_page
    else:
        return len(resp.json())

def main():
    repos = get_repos(GH_USER)
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos)
    total_issues = sum(repo.get("open_issues_count", 0) for repo in repos)
    total_prs = 0
    total_commits = 0

    for repo in repos:
        # Open PRs
        prs_url = f"https://api.github.com/repos/{GH_USER}/{repo['name']}/pulls?state=open&per_page=1"
        prs_resp = requests.get(prs_url, headers=headers)
        if "Link" in prs_resp.headers:
            last_page = int(re.findall(r'&page=(\\d+)>; rel=\"last\"', prs_resp.headers["Link"])[0])
            total_prs += last_page
        else:
            total_prs += len(prs_resp.json())
        # Commits
        total_commits += get_commit_count(repo['name'])

    stats = (
        f"**Total Public Repositories:** {len(repos)}\\n"
        f"**Total Stars:** {total_stars}\\n"
        f"**Total Forks:** {total_forks}\\n"
        f"**Total Open Issues:** {total_issues}\\n"
        f"**Total Open PRs:** {total_prs}\\n"
        f"**Total Commits:** {total_commits}\\n"
        f"_Last updated: UTC {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}_"
    )

    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()
    new_readme = re.sub(
        r"<!--START_SECTION:github_stats-->.*<!--END_SECTION:github_stats-->",
        f"<!--START_SECTION:github_stats-->\\n{stats}\\n<!--END_SECTION:github_stats-->",
        readme, flags=re.DOTALL
    )
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    main()
