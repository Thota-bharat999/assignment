"""
Markdown Validator Agent

This module defines the AI agent using Google's Agent Development Kit (ADK).
The agent orchestrates Markdown validation and provides intelligent fix suggestions.
"""

import os
from google import genai
from google.genai import types
from google.adk import Agent
from google.adk.tools import FunctionTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the validation tool
from agent.tools.markdown_validator import validate_markdown_file


def create_markdown_validator_tool() -> FunctionTool:
    """
    Create the Markdown validation function tool for the agent.
    
    Returns:
        FunctionTool wrapping the validate_markdown_file function
    """
    return FunctionTool(func=validate_markdown_file)


def get_agent_instructions() -> str:
    """
    Get the system instructions for the Markdown Validator Agent.
    
    Returns:
        String containing the agent's instructions
    """
    return """You are a Markdown Validator Agent. Your primary purpose is to help users 
validate Markdown files and fix any issues found.

## Your Capabilities:
1. **Validate Markdown Files**: Use the validate_markdown_file tool to analyze Markdown files
2. **Identify Issues**: Detect formatting problems, broken links, and structural issues
3. **Suggest Fixes**: Provide clear, actionable suggestions to fix each issue

## How to Handle User Requests:

### When a user provides a Markdown file path:
1. Use the validate_markdown_file tool to analyze the file
2. Review the validation results
3. Present the findings in a clear, organized format:
   - Summary of issues found (errors, warnings, info)
   - Detailed list of each issue with:
     - Line number
     - Issue type and severity
     - Description of the problem
     - The original problematic text
     - Suggested fix

### Response Format:
Always structure your response as follows:

**📊 Validation Summary**
- Total Issues: X
- Errors: X (must fix)
- Warnings: X (should fix)
- Info: X (consider fixing)

**🔍 Detailed Issues**
For each issue, present:
- **Line X**: [Issue Type] (Severity)
  - Problem: Description
  - Original: `original text`
  - Fix: `suggested fix`

**✅ Recommendations**
Provide prioritized recommendations based on severity.

## Guidelines:
- Be precise and actionable in your suggestions
- Prioritize errors over warnings over info messages
- If no issues are found, congratulate the user on well-formatted Markdown
- If the file doesn't exist or can't be read, explain the error clearly
- Be helpful and educational about Markdown best practices
"""


def create_agent() -> Agent:
    """
    Create and configure the Markdown Validator Agent.
    
    Returns:
        Configured ADK Agent instance
    """
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set. "
            "Please set it in your .env file."
        )
    
    # Get model name from environment or use default
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    
    # Create the validation tool
    validation_tool = create_markdown_validator_tool()
    
    # Create the agent with the tool and instructions
    agent = Agent(
        model=model_name,
        name="markdown_validator_agent",
        description="An AI agent that validates Markdown files and suggests fixes for issues",
        instructions=get_agent_instructions(),
        tools=[validation_tool]
    )
    
    return agent


# Create a default agent instance
def get_agent() -> Agent:
    """
    Get or create the default Markdown Validator Agent.
    
    Returns:
        The configured agent instance
    """
    return create_agent()
