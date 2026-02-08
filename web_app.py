"""
Web Application for Markdown Validator Agent

A simple web interface for the Markdown Validator using FastAPI.
This provides a user-friendly way to validate Markdown files.
"""

import os
import tempfile
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Load environment variables
load_dotenv()

# Import the validation tool
from agent.tools.markdown_validator import validate_markdown_file

# Create FastAPI app
app = FastAPI(
    title="Markdown Validator Agent",
    description="AI-powered Markdown file validation and fix suggestions",
    version="1.0.0"
)

# Create templates directory if it doesn't exist
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

# HTML template for the web interface (using raw string to avoid escape issues)
HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Validator Agent</title>
    <style>
        :root {
            --primary: #4f46e5;
            --primary-dark: #4338ca;
            --error: #ef4444;
            --warning: #f59e0b;
            --info: #3b82f6;
            --success: #10b981;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        h1 {
            font-size: 2rem;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: var(--text-light);
        }
        
        .card {
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .upload-area {
            border: 2px dashed var(--border);
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: var(--primary);
            background: rgba(79, 70, 229, 0.05);
        }
        
        .upload-area.dragover {
            border-color: var(--primary);
            background: rgba(79, 70, 229, 0.1);
        }
        
        .upload-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .btn:hover {
            background: var(--primary-dark);
        }
        
        .btn:disabled {
            background: var(--text-light);
            cursor: not-allowed;
        }
        
        textarea {
            width: 100%;
            min-height: 200px;
            padding: 1rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.9rem;
            resize: vertical;
        }
        
        .or-divider {
            text-align: center;
            margin: 1.5rem 0;
            color: var(--text-light);
        }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .stat {
            text-align: center;
            padding: 1rem;
            border-radius: 8px;
            background: var(--bg);
        }
        
        .stat.errors { border-left: 4px solid var(--error); }
        .stat.warnings { border-left: 4px solid var(--warning); }
        .stat.info { border-left: 4px solid var(--info); }
        .stat.total { border-left: 4px solid var(--primary); }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
        }
        
        .stat.errors .stat-number { color: var(--error); }
        .stat.warnings .stat-number { color: var(--warning); }
        .stat.info .stat-number { color: var(--info); }
        .stat.total .stat-number { color: var(--primary); }
        
        .stat-label {
            font-size: 0.85rem;
            color: var(--text-light);
        }
        
        .issue {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid;
        }
        
        .issue.error {
            background: rgba(239, 68, 68, 0.1);
            border-color: var(--error);
        }
        
        .issue.warning {
            background: rgba(245, 158, 11, 0.1);
            border-color: var(--warning);
        }
        
        .issue.info {
            background: rgba(59, 130, 246, 0.1);
            border-color: var(--info);
        }
        
        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .issue-type {
            font-weight: 600;
        }
        
        .issue-line {
            font-size: 0.85rem;
            color: var(--text-light);
        }
        
        .issue-description {
            margin-bottom: 0.5rem;
        }
        
        .code-block {
            background: #1e293b;
            color: #e2e8f0;
            padding: 0.5rem 0.75rem;
            border-radius: 4px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.85rem;
            overflow-x: auto;
            margin: 0.5rem 0;
        }
        
        .fix-suggestion {
            background: rgba(16, 185, 129, 0.1);
            border-left: 3px solid var(--success);
            padding: 0.5rem 0.75rem;
            margin-top: 0.5rem;
            border-radius: 0 4px 4px 0;
        }
        
        .fix-suggestion strong {
            color: var(--success);
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 2rem;
        }
        
        .spinner {
            border: 3px solid var(--border);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .success-message {
            text-align: center;
            padding: 2rem;
            color: var(--success);
        }
        
        .success-message .icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        #results {
            display: none;
        }
        
        footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-light);
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📝 Markdown Validator Agent</h1>
            <p class="subtitle">AI-powered Markdown validation and fix suggestions</p>
        </header>
        
        <div class="card">
            <h2>Upload or Paste Markdown</h2>
            
            <form id="uploadForm">
                <div class="upload-area" id="dropZone">
                    <div class="upload-icon">📄</div>
                    <p>Drag and drop a .md file here</p>
                    <p class="subtitle">or click to browse</p>
                    <input type="file" id="fileInput" accept=".md,.markdown">
                </div>
                
                <div class="or-divider">— OR —</div>
                
                <textarea id="markdownContent" placeholder="Paste your Markdown content here..."></textarea>
                
                <div style="text-align: center; margin-top: 1rem;">
                    <button type="submit" class="btn" id="validateBtn">🔍 Validate Markdown</button>
                </div>
            </form>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Analyzing your Markdown file...</p>
        </div>
        
        <div id="results">
            <div class="card">
                <h2>📊 Validation Summary</h2>
                <div class="summary" id="summary"></div>
            </div>
            
            <div class="card">
                <h2>🔍 Detailed Issues</h2>
                <div id="issues"></div>
            </div>
        </div>
    </div>
    
    <footer>
        <p>Built with Google ADK & FastAPI | Markdown Validator Agent v1.0</p>
    </footer>
    
    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const markdownContent = document.getElementById('markdownContent');
        const uploadForm = document.getElementById('uploadForm');
        const loading = document.getElementById('loading');
        const results = document.getElementById('results');
        const validateBtn = document.getElementById('validateBtn');
        
        // Drag and drop handlers
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && (file.name.endsWith('.md') || file.name.endsWith('.markdown'))) {
                handleFile(file);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files[0]) {
                handleFile(e.target.files[0]);
            }
        });
        
        function handleFile(file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                markdownContent.value = e.target.result;
            };
            reader.readAsText(file);
        }
        
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const content = markdownContent.value.trim();
            if (!content) {
                alert('Please provide Markdown content to validate.');
                return;
            }
            
            // Show loading
            loading.style.display = 'block';
            results.style.display = 'none';
            validateBtn.disabled = true;
            
            try {
                const response = await fetch('/api/validate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ content: content })
                });
                
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                alert('Error validating Markdown: ' + error.message);
            } finally {
                loading.style.display = 'none';
                validateBtn.disabled = false;
            }
        });
        
        function displayResults(data) {
            results.style.display = 'block';
            
            // Display summary
            const summaryHtml = `
                <div class="stat total">
                    <div class="stat-number">${data.total_issues}</div>
                    <div class="stat-label">Total Issues</div>
                </div>
                <div class="stat errors">
                    <div class="stat-number">${data.errors}</div>
                    <div class="stat-label">Errors</div>
                </div>
                <div class="stat warnings">
                    <div class="stat-number">${data.warnings}</div>
                    <div class="stat-label">Warnings</div>
                </div>
                <div class="stat info">
                    <div class="stat-number">${data.info}</div>
                    <div class="stat-label">Info</div>
                </div>
            `;
            document.getElementById('summary').innerHTML = summaryHtml;
            
            // Display issues
            const issuesContainer = document.getElementById('issues');
            
            if (data.issues.length === 0) {
                issuesContainer.innerHTML = `
                    <div class="success-message">
                        <div class="icon">✅</div>
                        <h3>No issues found!</h3>
                        <p>Your Markdown file is well-formatted.</p>
                    </div>
                `;
            } else {
                const issuesHtml = data.issues.map(issue => `
                    <div class="issue ${issue.severity}">
                        <div class="issue-header">
                            <span class="issue-type">${formatIssueType(issue.issue_type)}</span>
                            <span class="issue-line">Line ${issue.line_number}</span>
                        </div>
                        <div class="issue-description">${issue.description}</div>
                        ${issue.original_text ? `<div class="code-block">${escapeHtml(issue.original_text)}</div>` : ''}
                        <div class="fix-suggestion">
                            <strong>💡 Suggested Fix:</strong> ${escapeHtml(issue.suggested_fix)}
                        </div>
                    </div>
                `).join('');
                issuesContainer.innerHTML = issuesHtml;
            }
            
            // Scroll to results
            results.scrollIntoView({ behavior: 'smooth' });
        }
        
        function formatIssueType(type) {
            return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
'''


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface."""
    return HTML_TEMPLATE


@app.post("/api/validate")
async def validate_markdown(request: Request):
    """
    API endpoint to validate Markdown content.
    
    Accepts JSON with 'content' field containing Markdown text.
    Returns validation results with issues and suggestions.
    """
    try:
        data = await request.json()
        content = data.get('content', '')
        
        if not content:
            return JSONResponse(
                status_code=400,
                content={"error": "No content provided"}
            )
        
        # Save content to a temporary file for validation
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Run validation
            result = validate_markdown_file(temp_path)
            return JSONResponse(content=result)
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/validate-file")
async def validate_file(file: UploadFile = File(...)):
    """
    API endpoint to validate an uploaded Markdown file.
    
    Accepts a file upload and returns validation results.
    """
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content_str)
            temp_path = f.name
        
        try:
            # Run validation
            result = validate_markdown_file(temp_path)
            return JSONResponse(content=result)
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


def main():
    """Run the web application."""
    print("=" * 60)
    print("🚀 Starting Markdown Validator Web Interface")
    print("=" * 60)
    print("\nOpen http://localhost:8000 in your browser")
    print("Press Ctrl+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
