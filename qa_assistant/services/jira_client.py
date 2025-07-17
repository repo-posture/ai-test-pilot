import os
import logging
from jira import JIRA
from typing import List, Optional
from utils.config import JIRA_URL, JIRA_USER, JIRA_TOKEN

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Jira client
try:
    jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_USER, JIRA_TOKEN))
    logger.info(f"Connected to Jira at {JIRA_URL}")
except Exception as e:
    logger.error(f"Failed to connect to Jira: {str(e)}")
    raise

def create_jira_bug(
    summary: str, 
    description: str = None, 
    assignee: str = None, 
    team_category: str = None
) -> str:
    """
    Create a Jira bug with the provided information.
    
    Args:
        summary: Bug title
        description: Detailed description of the bug
        assignee: Username of the assignee
        labels: List of labels to apply to the bug
    
    Returns:
        URL to the created Jira ticket
    """
    # If description is not provided, use summary
    if description is None:
        description = summary
    
    # Prepare issue fields
    issue_dict = {
        "project": "ENGTAI",
        "summary": summary[:255],
        "description": description,
        "issuetype": {"name": "Bug"},
        "customfield_12544": {"value": team_category},
        "labels": ["BUG_BY_MATS"],
        "components": [{"name": "E2E Test Automation"}],
        "priority": {"name": "P0"}
    }
    
    logger.info(f"Creating Jira issue in project ENGTAI with summary: {summary[:50]}...")
    
    try:
        if assignee:
            # For Jira Cloud, use accountId
            user_id = get_jira_account_id(assignee)
            if user_id:
                issue_dict["assignee"] = {"accountId": user_id}
            else:
                logger.warning(f"Could not find accountId for {assignee}, leaving ticket unassigned")
        
        # logger.info(f"Issue dictionary: {issue_dict}")
        # Create the issue
        issue = jira.create_issue(**issue_dict)
        
        issue_url = f"{JIRA_URL}/browse/{issue.key}"
        logger.info(f"Successfully created issue: {issue_url}")
        return issue_url
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to create Jira issue: {error_msg}")
        
        # If there's an error with custom fields, try to get field info
        if "customfield" in error_msg:
            try:
                # Get information about fields to help with troubleshooting
                fields = jira.fields()
                for field in fields:
                    if field['id'] == 'customfield_12544' or 'Product Area' in field.get('name', ''):
                        logger.info(f"Field info: {field}")
                        break
            except Exception as field_error:
                logger.error(f"Failed to get field info: {str(field_error)}")
        
        raise

def get_jira_account_id(email):
    """Convert email to Jira account ID"""
    try:
        # Look up the user by email
        users = jira.search_users(query=email)
        if users:
            # Return the first matching user's accountId
            return users[0].accountId
        logger.warning(f"No Jira user found with email: {email}")
        return None
    except Exception as e:
        logger.error(f"Error finding Jira user by email: {e}")
        return None