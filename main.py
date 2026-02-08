"""
Markdown Validator Agent - Main Entry Point

This is the main entry point for running the Markdown Validator Agent.
Supports both command-line and interactive modes.
"""

import os
import sys
import argparse
import asyncio
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()


def validate_environment() -> bool:
    """
    Validate that required environment variables are set.
    
    Returns:
        True if environment is valid, False otherwise
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_google_api_key_here":
        print("❌ Error: GOOGLE_API_KEY not configured!")
        print("")
        print("Please set up your Google API key:")
        print("1. Copy .env.example to .env")
        print("2. Get your API key from: https://makersuite.google.com/app/apikey")
        print("3. Add it to your .env file")
        return False
    return True


async def run_agent_validation(file_path: str) -> None:
    """
    Run the agent to validate a Markdown file.
    
    Args:
        file_path: Path to the Markdown file to validate
    """
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from agent.agent import create_agent
    
    # Verify file exists
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return
    
    # Get absolute path
    abs_path = os.path.abspath(file_path)
    
    print(f"🔍 Validating: {abs_path}")
    print("-" * 60)
    
    try:
        # Create the agent
        agent = create_agent()
        
        # Create session service and runner
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name="markdown_validator",
            session_service=session_service
        )
        
        # Create a session
        session = await session_service.create_session(
            app_name="markdown_validator",
            user_id="user"
        )
        
        # Create the user message
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=f"Please validate this Markdown file and provide detailed fix suggestions: {abs_path}")]
        )
        
        # Run the agent
        print("🤖 Agent is analyzing the file...\n")
        
        async for event in runner.run_async(
            session_id=session.id,
            user_id="user",
            new_message=user_message
        ):
            # Handle different event types
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(part.text)
            elif hasattr(event, 'actions'):
                # Tool is being called
                for action in event.actions:
                    if hasattr(action, 'tool_name'):
                        print(f"🔧 Calling tool: {action.tool_name}")
        
        print("\n" + "=" * 60)
        print("✅ Validation complete!")
        
    except Exception as e:
        print(f"❌ Error running agent: {str(e)}")
        import traceback
        traceback.print_exc()


async def run_interactive_mode() -> None:
    """
    Run the agent in interactive mode for continuous validation.
    """
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from agent.agent import create_agent
    
    print("=" * 60)
    print("🤖 Markdown Validator Agent - Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  validate <file_path>  - Validate a Markdown file")
    print("  help                  - Show help information")
    print("  exit                  - Exit the program")
    print("\n" + "-" * 60)
    
    try:
        # Create the agent
        agent = create_agent()
        
        # Create session service and runner
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name="markdown_validator",
            session_service=session_service
        )
        
        # Create a persistent session
        session = await session_service.create_session(
            app_name="markdown_validator",
            user_id="user"
        )
        
        while True:
            try:
                user_input = input("\n📝 Enter command: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "exit":
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == "help":
                    print("\n📚 Help:")
                    print("  - Enter a file path to validate a Markdown file")
                    print("  - Ask questions about Markdown formatting")
                    print("  - Type 'exit' to quit")
                    continue
                
                # Handle validate command
                if user_input.lower().startswith("validate "):
                    file_path = user_input[9:].strip()
                    if not os.path.exists(file_path):
                        print(f"❌ File not found: {file_path}")
                        continue
                    user_input = f"Please validate this Markdown file and provide detailed fix suggestions: {os.path.abspath(file_path)}"
                
                # Create the user message
                user_message = types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)]
                )
                
                print("\n🤖 Processing...\n")
                
                # Run the agent
                async for event in runner.run_async(
                    session_id=session.id,
                    user_id="user",
                    new_message=user_message
                ):
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                print(part.text)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                
    except Exception as e:
        print(f"❌ Error creating agent: {str(e)}")


def run_simple_validation(file_path: str) -> None:
    """
    Run simple validation without the agent (for testing).
    
    Args:
        file_path: Path to the Markdown file to validate
    """
    from agent.tools.markdown_validator import validate_markdown_file
    import json
    
    print(f"🔍 Validating: {os.path.abspath(file_path)}")
    print("-" * 60)
    
    result = validate_markdown_file(file_path)
    
    print(f"\n📊 Validation Summary")
    print(f"   Total Issues: {result['total_issues']}")
    print(f"   Errors: {result['errors']} (must fix)")
    print(f"   Warnings: {result['warnings']} (should fix)")
    print(f"   Info: {result['info']} (consider fixing)")
    
    if result['issues']:
        print(f"\n🔍 Detailed Issues:\n")
        for issue in result['issues']:
            severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(issue['severity'], "⚪")
            print(f"   {severity_icon} Line {issue['line_number']}: {issue['issue_type']}")
            print(f"      Problem: {issue['description']}")
            if issue['original_text']:
                print(f"      Original: {issue['original_text'][:80]}...")
            print(f"      Fix: {issue['suggested_fix']}")
            print()
    else:
        print("\n✅ No issues found! Your Markdown file is well-formatted.")


def main():
    """Main entry point for the Markdown Validator Agent."""
    parser = argparse.ArgumentParser(
        description="Markdown Validator Agent - Validate and fix Markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --file samples/sample.md    Validate a specific file
  python main.py --interactive               Run in interactive mode
  python main.py --simple samples/sample.md  Run simple validation (no agent)
        """
    )
    
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to the Markdown file to validate"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--simple", "-s",
        type=str,
        help="Run simple validation without agent (for testing)"
    )
    
    args = parser.parse_args()
    
    # Handle simple validation (no agent needed)
    if args.simple:
        run_simple_validation(args.simple)
        return
    
    # Validate environment for agent-based operations
    if not validate_environment():
        sys.exit(1)
    
    # Run based on mode
    if args.interactive:
        asyncio.run(run_interactive_mode())
    elif args.file:
        asyncio.run(run_agent_validation(args.file))
    else:
        # Default to interactive mode
        asyncio.run(run_interactive_mode())


if __name__ == "__main__":
    main()
