import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = os.getenv("REPO_OWNER", "ruxailab")
REPO_NAME = os.getenv("REPO_NAME", "RUXAILAB")

def get_time_based_metrics(username, contribution_type, headers, time_ranges):
    """
    Generic function to fetch time-based metrics for any contribution type.
    
    Args:
        username: GitHub username
        contribution_type: 'pr', 'issue', or 'commit'
        headers: API request headers
        time_ranges: Dictionary with date ranges
    
    Returns:
        Dictionary with daily, weekly, monthly, and all-time counts
    """
    # Set up query parameters based on contribution type
    if contribution_type == 'pr':
        query_type = 'type:pr+is:merged'
        time_field = 'merged'
    elif contribution_type == 'issue':
        query_type = 'type:issue'
        time_field = 'created'
    elif contribution_type == 'commit':
        # Commits have a different API endpoint
        if contribution_type == 'commit':
            # All-time commits
            commits_url = f"{GITHUB_API_URL}/search/commits?q=repo:{REPO_OWNER}/{REPO_NAME}+author:{username}"
            commits_response = requests.get(commits_url, headers=headers)
            all_time = commits_response.json().get("total_count", 0) if commits_response.status_code == 200 else 0
            
            # GitHub API limitations make time-based commit queries more complex
            # For simplicity, we'll use the all-time count for each time range
            # In a production app, you would use pagination and analyze commit dates
            return {
                'daily': 0,
                'weekly': 0,
                'monthly': 0,
                'all_time': all_time
            }
    
    # Get all-time count
    all_time_url = f"{GITHUB_API_URL}/search/issues?q=repo:{REPO_OWNER}/{REPO_NAME}+{query_type}+author:{username}"
    all_time_response = requests.get(all_time_url, headers=headers)
    all_time = all_time_response.json().get("total_count", 0) if all_time_response.status_code == 200 else 0
    
    # Get daily count
    daily_url = f"{GITHUB_API_URL}/search/issues?q=repo:{REPO_OWNER}/{REPO_NAME}+{query_type}+author:{username}+{time_field}:>={time_ranges['today']}"
    daily_response = requests.get(daily_url, headers=headers)
    daily = daily_response.json().get("total_count", 0) if daily_response.status_code == 200 else 0
    
    # Get weekly count
    weekly_url = f"{GITHUB_API_URL}/search/issues?q=repo:{REPO_OWNER}/{REPO_NAME}+{query_type}+author:{username}+{time_field}:>={time_ranges['week_ago']}"
    weekly_response = requests.get(weekly_url, headers=headers)
    weekly = weekly_response.json().get("total_count", 0) if weekly_response.status_code == 200 else 0
    
    # Get monthly count
    monthly_url = f"{GITHUB_API_URL}/search/issues?q=repo:{REPO_OWNER}/{REPO_NAME}+{query_type}+author:{username}+{time_field}:>={time_ranges['month_ago']}"
    monthly_response = requests.get(monthly_url, headers=headers)
    monthly = monthly_response.json().get("total_count", 0) if monthly_response.status_code == 200 else 0
    
    return {
        'daily': daily,
        'weekly': weekly,
        'monthly': monthly,
        'all_time': all_time
    }

def calculate_streaks(username, contribution_type, headers, month_ago_date):
    """
    Calculate contribution streaks for any contribution type.
    
    Args:
        username: GitHub username
        contribution_type: 'pr', 'issue', or 'commit'
        headers: API request headers
        month_ago_date: Date 30 days ago
    
    Returns:
        Dictionary with current_streak and longest_streak
    """
    # Cannot calculate streaks for commits via the API in the same way
    if contribution_type == 'commit':
        return {
            'current_streak': 0,
            'longest_streak': 0
        }
    
    # Set up query parameters based on contribution type
    if contribution_type == 'pr':
        query_type = 'type:pr+is:merged'
        time_field = 'merged'
        date_field = 'merged_at'
    elif contribution_type == 'issue':
        query_type = 'type:issue'
        time_field = 'created'
        date_field = 'created_at'
    
    # Get contribution data for the last 30 days
    streak_url = f"{GITHUB_API_URL}/search/issues?q=repo:{REPO_OWNER}/{REPO_NAME}+{query_type}+author:{username}+{time_field}:>={month_ago_date}&sort={time_field}&order=desc&per_page=100"
    streak_response = requests.get(streak_url, headers=headers)
    
    current_streak = 0
    longest_streak = 0
    
    if streak_response.status_code == 200:
        items = streak_response.json().get("items", [])
        
        # Get dates when contributions occurred
        dates = []
        for item in items:
            if contribution_type == 'pr' and not item.get("pull_request"):
                continue
                
            date_str = item.get(date_field, "").split("T")[0]  # Get just the date part
            if date_str:
                dates.append(date_str)
        
        # Calculate streaks
        dates.sort(reverse=True)  # Most recent first
        
        if dates:
            # Calculate current streak
            last_date = datetime.strptime(dates[0], '%Y-%m-%d')
            current_streak = 1
            
            for i in range(1, len(dates)):
                date = datetime.strptime(dates[i], '%Y-%m-%d')
                if (last_date - date).days <= 1:  # Consecutive days
                    current_streak += 1
                else:
                    break
                last_date = date
            
            # Calculate longest streak
            longest_streak = 1
            temp_streak = 1
            
            for i in range(1, len(dates)):
                prev_date = datetime.strptime(dates[i-1], '%Y-%m-%d')
                curr_date = datetime.strptime(dates[i], '%Y-%m-%d')
                
                if (prev_date - curr_date).days <= 1:  # Consecutive days
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
            
            longest_streak = max(longest_streak, temp_streak)
    
    return {
        'current_streak': current_streak,
        'longest_streak': longest_streak
    }

def get_contributions(username):
    """
    Fetch comprehensive contribution data for a user.
    This includes all-time counts as well as time-based metrics for PRs, issues, and commits.
    """
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get current date and calculate time ranges
    now = datetime.now()
    today_date = now.strftime('%Y-%m-%d')
    week_ago_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    month_ago_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    current_month = now.strftime("%B")
    
    time_ranges = {
        'today': today_date,
        'week_ago': week_ago_date,
        'month_ago': month_ago_date
    }
    
    # Get metrics for each contribution type
    pr_metrics = get_time_based_metrics(username, 'pr', headers, time_ranges)
    issue_metrics = get_time_based_metrics(username, 'issue', headers, time_ranges)
    commit_metrics = get_time_based_metrics(username, 'commit', headers, time_ranges)
    
    # Calculate streaks for each contribution type
    pr_streaks = calculate_streaks(username, 'pr', headers, month_ago_date)
    issue_streaks = calculate_streaks(username, 'issue', headers, month_ago_date)
    commit_streaks = calculate_streaks(username, 'commit', headers, month_ago_date)
    
    # Calculate average per day for current month
    days_this_month = min(now.day, 30)  # Use actual days passed this month, max 30
    pr_avg_per_day = round(pr_metrics['monthly'] / max(days_this_month, 1), 1)
    issue_avg_per_day = round(issue_metrics['monthly'] / max(days_this_month, 1), 1)
    commit_avg_per_day = round(commit_metrics['monthly'] / max(days_this_month, 1), 1)
    
    # Build the complete contribution data structure
    return {
        "pr_count": pr_metrics['all_time'],
        "issues_count": issue_metrics['all_time'],
        "commits_count": commit_metrics['all_time'],
        "stats": {
            "tracking_since": "March 24, 2025",  # Example date - adjust as needed
            "current_month": current_month,
            "prs": {
                "daily": pr_metrics['daily'],
                "weekly": pr_metrics['weekly'],
                "monthly": pr_metrics['monthly'],
                "all_time": pr_metrics['all_time'],
                "current_streak": pr_streaks['current_streak'],
                "longest_streak": pr_streaks['longest_streak'],
                "avg_per_day": pr_avg_per_day
            },
            "issues": {
                "daily": issue_metrics['daily'],
                "weekly": issue_metrics['weekly'],
                "monthly": issue_metrics['monthly'],
                "all_time": issue_metrics['all_time'],
                "current_streak": issue_streaks['current_streak'],
                "longest_streak": issue_streaks['longest_streak'],
                "avg_per_day": issue_avg_per_day
            },
            "commits": {
                "daily": commit_metrics['daily'],
                "weekly": commit_metrics['weekly'],
                "monthly": commit_metrics['monthly'],
                "all_time": commit_metrics['all_time'],
                "current_streak": commit_streaks['current_streak'],
                "longest_streak": commit_streaks['longest_streak'],
                "avg_per_day": commit_avg_per_day
            }
        }
    }

def fetch_all_contributors():
    """Fetch all contributors to the repository."""
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json"
    }
    contributors_url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/contributors"
    response = requests.get(contributors_url, headers=headers)
    if response.status_code == 200:
        return [contributor['login'] for contributor in response.json()]
    else:
        print(f"Failed to fetch contributors: {response.status_code}")
        return []

def calculate_rankings(all_contributions):
    """Calculate rankings for each contributor across different metrics."""
    contributors = list(all_contributions.keys())
    if not contributors:
        return all_contributions
        
    # Calculate rankings for all contribution types
    ranking_types = {
        "pr": lambda user: all_contributions[user]["pr_count"],
        "issue": lambda user: all_contributions[user]["issues_count"],
        "commit": lambda user: all_contributions[user]["commits_count"]
    }
    
    for time_period in ["daily", "weekly", "monthly", "all_time"]:
        ranking_types[f"pr_{time_period}"] = lambda user, period=time_period: all_contributions[user]["stats"]["prs"][period]
        ranking_types[f"issue_{time_period}"] = lambda user, period=time_period: all_contributions[user]["stats"]["issues"][period]
        ranking_types[f"commit_{time_period}"] = lambda user, period=time_period: all_contributions[user]["stats"]["commits"][period]
    
    # Calculate and add all rankings
    for username in contributors:
        all_contributions[username]["rankings"] = {}
        
        for rank_type, key_func in ranking_types.items():
            sorted_users = sorted(contributors, key=key_func, reverse=True)
            all_contributions[username]["rankings"][rank_type] = sorted_users.index(username) + 1
    
    return all_contributions

if __name__ == "__main__":
    all_contributions = {}
    contributors = fetch_all_contributors()
    
    print("Fetching contribution data...")
    for username in contributors:
        contributions = get_contributions(username)
        all_contributions[username] = contributions
        print(f"User: {username}")
        print(f"PRs: {contributions['pr_count']} (Daily: {contributions['stats']['prs']['daily']}, Weekly: {contributions['stats']['prs']['weekly']}, Monthly: {contributions['stats']['prs']['monthly']})")
        print(f"PR Streak: Current {contributions['stats']['prs']['current_streak']}, Longest: {contributions['stats']['prs']['longest_streak']}")
        print(f"Issues: {contributions['issues_count']} (Daily: {contributions['stats']['issues']['daily']}, Weekly: {contributions['stats']['issues']['weekly']}, Monthly: {contributions['stats']['issues']['monthly']})")
        print(f"Issue Streak: Current {contributions['stats']['issues']['current_streak']}, Longest: {contributions['stats']['issues']['longest_streak']}")
        print(f"Commits: {contributions['commits_count']} (Daily: {contributions['stats']['commits']['daily']}, Weekly: {contributions['stats']['commits']['weekly']}, Monthly: {contributions['stats']['commits']['monthly']})")
    
    # Calculate and add rankings
    all_contributions = calculate_rankings(all_contributions)
    
    # Save to a JSON file for the Discord bot to use
    with open("contributions.json", "w") as f:
        json.dump(all_contributions, f, indent=2)
    
    print("Contribution data saved to contributions.json") 
