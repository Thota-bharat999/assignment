# AI-Assisted Notes

This document describes how AI tools were used during the development of this project, in accordance with the assignment's Integrity & AI-Tool Usage Policy.

## AI Tools Used

- **GitHub Copilot**: Used for code completion suggestions and syntax help
- **ChatGPT/Claude**: Used for understanding concepts and exploring approaches

## What AI Was Used For

### 1. Learning and Understanding

- **Understanding Google ADK**: I used AI to understand the concepts of Google's Agent Development Kit, including:
  - What agents are and how they work
  - How to define tools and integrate them with agents
  - The async/await patterns used in ADK

- **Markdown Specification**: I consulted AI to understand the CommonMark specification and various Markdown edge cases.

### 2. Exploring APIs and Libraries

- **Requests Library**: Asked about proper timeout handling and exception patterns
- **Regex Patterns**: Got help understanding complex regex patterns for Markdown parsing
- **FastAPI**: Explored best practices for building web APIs

### 3. Design Suggestions

- **Project Structure**: Discussed best practices for organizing Python projects
- **Error Handling**: Explored different approaches to error handling and user feedback
- **Validation Logic**: Discussed what types of Markdown issues should be checked

## How I Converted Learning into My Own Implementation

### Code Ownership

Every line of code in this project was written by me. The AI-assisted learning was converted into my own implementation through the following process:

1. **Concept Understanding**: Used AI to understand concepts, then closed the AI tool
2. **Independent Implementation**: Wrote code from scratch based on my understanding
3. **Problem Solving**: When stuck, I would research specific issues, understand the solution, then implement it myself
4. **Code Review**: Reviewed all code to ensure I understood every line

### Specific Examples

#### Markdown Validator Tool
- **AI Helped With**: Understanding regex patterns for matching Markdown elements
- **My Implementation**: I designed the `MarkdownValidator` class structure, chose which validations to include, and wrote all validation logic myself. The class design, method organization, and error reporting format are my own work.

#### Agent Integration
- **AI Helped With**: Understanding how ADK agents call tools
- **My Implementation**: I structured the agent instructions, designed the response format, and integrated the validation tool with the agent framework.

#### Web Interface
- **AI Helped With**: FastAPI routing patterns
- **My Implementation**: I designed the UI, wrote all HTML/CSS/JavaScript, and created the API endpoints.

## Design Decisions I Made

1. **Dataclass for Issues**: Chose to use `@dataclass` for clean, type-safe issue representation
2. **Severity Levels**: Decided on error/warning/info classification based on impact
3. **Validation Order**: Ordered validators logically (headers first, then content, then formatting)
4. **Tool Architecture**: Separated the validation tool from the agent for testability
5. **Web Interface**: Created a drag-and-drop interface for better UX

## What I Can Explain

I can explain and justify:

- Every class, method, and function in the codebase
- Why I chose specific regex patterns
- The validation logic for each type of Markdown issue
- How the agent orchestrates the validation process
- Error handling strategies
- The web API design

## Conclusion

AI tools were used responsibly as learning aids and for exploring APIs. All code is my own original work, written after understanding the concepts. I am prepared to explain any part of this implementation in detail.
