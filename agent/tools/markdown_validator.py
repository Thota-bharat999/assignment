"""
Markdown Validator Tool

A comprehensive Python tool for validating Markdown files.
Detects formatting issues, broken links, and structural problems.
"""

import re
import os
from typing import Optional
from dataclasses import dataclass, asdict
import requests
from urllib.parse import urlparse, urljoin


@dataclass
class ValidationIssue:
    """Represents a single validation issue found in the Markdown file."""
    line_number: int
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    original_text: str
    suggested_fix: str


class MarkdownValidator:
    """
    A comprehensive Markdown validator that checks for various issues
    including formatting problems and broken links.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the validator with a file path.
        
        Args:
            file_path: Path to the Markdown file to validate
        """
        self.file_path = file_path
        self.content = ""
        self.lines = []
        self.issues = []
        self.base_dir = os.path.dirname(os.path.abspath(file_path))
    
    def load_file(self) -> bool:
        """
        Load the Markdown file content.
        
        Returns:
            True if file loaded successfully, False otherwise
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            self.lines = self.content.split('\n')
            return True
        except FileNotFoundError:
            self.issues.append(ValidationIssue(
                line_number=0,
                issue_type="file_error",
                severity="error",
                description=f"File not found: {self.file_path}",
                original_text="",
                suggested_fix="Verify the file path is correct"
            ))
            return False
        except Exception as e:
            self.issues.append(ValidationIssue(
                line_number=0,
                issue_type="file_error",
                severity="error",
                description=f"Error reading file: {str(e)}",
                original_text="",
                suggested_fix="Check file permissions and encoding"
            ))
            return False
    
    def validate_headers(self) -> None:
        """Check for header formatting issues."""
        header_pattern = re.compile(r'^(#{1,6})\s*(.*)$')
        prev_level = 0
        
        for i, line in enumerate(self.lines, 1):
            # Check for ATX-style headers
            match = header_pattern.match(line)
            if match:
                hashes = match.group(1)
                text = match.group(2).strip()
                level = len(hashes)
                
                # Check for missing space after hashes
                if line[len(hashes):len(hashes)+1] != ' ' and text:
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="header_format",
                        severity="warning",
                        description="Missing space after header hashes",
                        original_text=line,
                        suggested_fix=f"{hashes} {text}"
                    ))
                
                # Check for empty header
                if not text:
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="empty_header",
                        severity="warning",
                        description="Empty header text",
                        original_text=line,
                        suggested_fix="Add descriptive header text"
                    ))
                
                # Check for header level skipping
                if prev_level > 0 and level > prev_level + 1:
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="header_hierarchy",
                        severity="info",
                        description=f"Header level skipped from H{prev_level} to H{level}",
                        original_text=line,
                        suggested_fix=f"{'#' * (prev_level + 1)} {text}"
                    ))
                
                prev_level = level
            
            # Check for trailing hashes in ATX headers
            if match and text.endswith('#'):
                clean_text = text.rstrip('#').rstrip()
                self.issues.append(ValidationIssue(
                    line_number=i,
                    issue_type="trailing_hashes",
                    severity="info",
                    description="Trailing hashes in header (not recommended)",
                    original_text=line,
                    suggested_fix=f"{hashes} {clean_text}"
                ))
    
    def validate_links(self) -> None:
        """Check for broken or malformed links."""
        # Pattern for inline links [text](url)
        link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]*)\)')
        # Pattern for reference links [text][ref]
        ref_link_pattern = re.compile(r'\[([^\]]+)\]\[([^\]]*)\]')
        # Pattern for reference definitions [ref]: url
        ref_def_pattern = re.compile(r'^\[([^\]]+)\]:\s*(.+)$')
        
        reference_definitions = {}
        reference_usages = []
        
        # First pass: collect reference definitions
        for i, line in enumerate(self.lines, 1):
            for match in ref_def_pattern.finditer(line):
                ref_id = match.group(1).lower()
                reference_definitions[ref_id] = (i, match.group(2))
        
        # Second pass: validate links
        for i, line in enumerate(self.lines, 1):
            # Check inline links
            for match in link_pattern.finditer(line):
                link_text = match.group(1)
                url = match.group(2).strip()
                
                # Check for empty link text
                if not link_text:
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="empty_link_text",
                        severity="warning",
                        description="Empty link text",
                        original_text=match.group(0),
                        suggested_fix=f"[descriptive text]({url})"
                    ))
                
                # Check for empty URL
                if not url:
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="empty_url",
                        severity="error",
                        description="Empty URL in link",
                        original_text=match.group(0),
                        suggested_fix=f"[{link_text}](https://example.com)"
                    ))
                    continue
                
                # Validate URL format and accessibility
                self._validate_url(i, url, match.group(0))
            
            # Check reference links
            for match in ref_link_pattern.finditer(line):
                ref_id = match.group(2).lower() if match.group(2) else match.group(1).lower()
                if ref_id not in reference_definitions:
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="undefined_reference",
                        severity="error",
                        description=f"Undefined link reference: [{ref_id}]",
                        original_text=match.group(0),
                        suggested_fix=f"Add reference definition: [{ref_id}]: https://example.com"
                    ))
    
    def _validate_url(self, line_num: int, url: str, original: str) -> None:
        """
        Validate a URL for format and optionally accessibility.
        
        Args:
            line_num: Line number where URL appears
            url: The URL to validate
            original: Original matched text for context
        """
        # Handle anchor links
        if url.startswith('#'):
            anchor_id = url[1:]
            # Check if anchor exists in document
            anchor_pattern = re.compile(
                rf'{{#\s*{re.escape(anchor_id)}\s*}}|'
                rf'id\s*=\s*["\']?{re.escape(anchor_id)}["\']?|'
                rf'^#+\s*.*$',
                re.MULTILINE
            )
            # Simplified check - just validate format
            return
        
        # Handle relative file paths
        if not url.startswith(('http://', 'https://', 'mailto:', 'tel:')):
            # It's a relative path
            full_path = os.path.join(self.base_dir, url.split('#')[0])
            if not os.path.exists(full_path):
                self.issues.append(ValidationIssue(
                    line_number=line_num,
                    issue_type="broken_local_link",
                    severity="error",
                    description=f"Local file not found: {url}",
                    original_text=original,
                    suggested_fix=f"Verify file exists at: {full_path}"
                ))
            return
        
        # Validate external URLs
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                self.issues.append(ValidationIssue(
                    line_number=line_num,
                    issue_type="invalid_url_format",
                    severity="error",
                    description=f"Invalid URL format: {url}",
                    original_text=original,
                    suggested_fix=f"Use full URL with scheme: https://{url}"
                ))
                return
            
            # Optional: Check if URL is accessible (with timeout)
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    self.issues.append(ValidationIssue(
                        line_number=line_num,
                        issue_type="broken_external_link",
                        severity="error",
                        description=f"Broken link (HTTP {response.status_code}): {url}",
                        original_text=original,
                        suggested_fix="Update URL or remove the link"
                    ))
            except requests.exceptions.Timeout:
                self.issues.append(ValidationIssue(
                    line_number=line_num,
                    issue_type="link_timeout",
                    severity="warning",
                    description=f"Link timed out: {url}",
                    original_text=original,
                    suggested_fix="Verify URL is accessible"
                ))
            except requests.exceptions.RequestException:
                # Network issues - don't report as error
                pass
        except Exception:
            pass
    
    def validate_code_blocks(self) -> None:
        """Check for unclosed or malformed code blocks."""
        in_fenced_block = False
        block_start_line = 0
        fence_char = None
        fence_count = 0
        
        for i, line in enumerate(self.lines, 1):
            # Check for fenced code blocks
            fence_match = re.match(r'^(`{3,}|~{3,})(\w*)$', line.strip())
            
            if fence_match:
                current_char = fence_match.group(1)[0]
                current_count = len(fence_match.group(1))
                
                if not in_fenced_block:
                    in_fenced_block = True
                    block_start_line = i
                    fence_char = current_char
                    fence_count = current_count
                elif current_char == fence_char and current_count >= fence_count:
                    in_fenced_block = False
                    fence_char = None
            
            # Check for inline code with unmatched backticks
            if not in_fenced_block:
                backtick_count = line.count('`')
                # Simple check: odd number of single backticks (excluding triple)
                triple_count = line.count('```')
                single_count = backtick_count - (triple_count * 3)
                if single_count % 2 != 0 and not line.strip().startswith('```'):
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="unmatched_backticks",
                        severity="warning",
                        description="Possible unmatched inline code backticks",
                        original_text=line,
                        suggested_fix="Ensure backticks are properly paired"
                    ))
        
        # Check for unclosed fenced block
        if in_fenced_block:
            self.issues.append(ValidationIssue(
                line_number=block_start_line,
                issue_type="unclosed_code_block",
                severity="error",
                description="Unclosed fenced code block",
                original_text=self.lines[block_start_line - 1],
                suggested_fix=f"Add closing fence: {'`' * fence_count if fence_char == '`' else '~' * fence_count}"
            ))
    
    def validate_lists(self) -> None:
        """Check for list formatting issues."""
        list_item_pattern = re.compile(r'^(\s*)([-*+]|\d+[.)])\s+(.*)$')
        prev_indent = -1
        prev_was_list = False
        
        for i, line in enumerate(self.lines, 1):
            match = list_item_pattern.match(line)
            
            if match:
                indent = len(match.group(1))
                marker = match.group(2)
                content = match.group(3)
                
                # Check for inconsistent indentation
                if prev_was_list and indent > 0 and indent % 2 != 0 and indent % 4 != 0:
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="inconsistent_indent",
                        severity="info",
                        description="Non-standard list indentation (use 2 or 4 spaces)",
                        original_text=line,
                        suggested_fix=f"{'  ' * (indent // 2)}{marker} {content}"
                    ))
                
                # Check for empty list item
                if not content.strip():
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="empty_list_item",
                        severity="warning",
                        description="Empty list item",
                        original_text=line,
                        suggested_fix="Add content or remove empty item"
                    ))
                
                prev_indent = indent
                prev_was_list = True
            else:
                if line.strip():  # Non-empty, non-list line
                    prev_was_list = False
    
    def validate_images(self) -> None:
        """Check for image formatting issues."""
        image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]*)\)')
        
        for i, line in enumerate(self.lines, 1):
            for match in image_pattern.finditer(line):
                alt_text = match.group(1)
                url = match.group(2).strip()
                
                # Check for missing alt text
                if not alt_text:
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="missing_alt_text",
                        severity="warning",
                        description="Image missing alt text (accessibility issue)",
                        original_text=match.group(0),
                        suggested_fix=f"![descriptive alt text]({url})"
                    ))
                
                # Check for empty image URL
                if not url:
                    self.issues.append(ValidationIssue(
                        line_number=i,
                        issue_type="empty_image_url",
                        severity="error",
                        description="Empty image URL",
                        original_text=match.group(0),
                        suggested_fix=f"![{alt_text}](path/to/image.png)"
                    ))
                    continue
                
                # Check if local image exists
                if not url.startswith(('http://', 'https://', 'data:')):
                    img_path = os.path.join(self.base_dir, url)
                    if not os.path.exists(img_path):
                        self.issues.append(ValidationIssue(
                            line_number=i,
                            issue_type="missing_image",
                            severity="error",
                            description=f"Image file not found: {url}",
                            original_text=match.group(0),
                            suggested_fix=f"Add image at: {img_path}"
                        ))
    
    def validate_emphasis(self) -> None:
        """Check for unmatched emphasis markers."""
        for i, line in enumerate(self.lines, 1):
            # Skip code blocks and inline code
            if line.strip().startswith('```') or line.strip().startswith('~~~'):
                continue
            
            # Remove inline code spans for analysis
            line_without_code = re.sub(r'`[^`]+`', '', line)
            
            # Check for unmatched bold markers
            bold_double = re.findall(r'\*\*', line_without_code)
            if len(bold_double) % 2 != 0:
                self.issues.append(ValidationIssue(
                    line_number=i,
                    issue_type="unmatched_bold",
                    severity="warning",
                    description="Possibly unmatched bold markers (**)",
                    original_text=line,
                    suggested_fix="Ensure ** markers are properly paired"
                ))
            
            # Check for unmatched underscore bold
            bold_underscore = re.findall(r'__', line_without_code)
            if len(bold_underscore) % 2 != 0:
                self.issues.append(ValidationIssue(
                    line_number=i,
                    issue_type="unmatched_bold",
                    severity="warning",
                    description="Possibly unmatched bold markers (__)",
                    original_text=line,
                    suggested_fix="Ensure __ markers are properly paired"
                ))
    
    def validate_tables(self) -> None:
        """Check for table formatting issues."""
        in_table = False
        table_start = 0
        header_cols = 0
        
        for i, line in enumerate(self.lines, 1):
            # Check if line looks like a table row
            if '|' in line:
                stripped = line.strip()
                if stripped.startswith('|') or stripped.endswith('|'):
                    cols = len([c for c in stripped.split('|') if c.strip() or c == ''])
                    
                    if not in_table:
                        in_table = True
                        table_start = i
                        header_cols = cols
                    else:
                        # Check for inconsistent column count
                        if cols != header_cols and not re.match(r'^[\s|:-]+$', stripped):
                            self.issues.append(ValidationIssue(
                                line_number=i,
                                issue_type="table_column_mismatch",
                                severity="error",
                                description=f"Table has inconsistent columns (expected {header_cols}, found {cols})",
                                original_text=line,
                                suggested_fix=f"Adjust to {header_cols} columns"
                            ))
            else:
                if in_table and line.strip():  # Non-empty line outside table
                    in_table = False
    
    def validate_all(self) -> list:
        """
        Run all validation checks on the Markdown file.
        
        Returns:
            List of ValidationIssue objects
        """
        if not self.load_file():
            return [asdict(issue) for issue in self.issues]
        
        # Run all validators
        self.validate_headers()
        self.validate_links()
        self.validate_code_blocks()
        self.validate_lists()
        self.validate_images()
        self.validate_emphasis()
        self.validate_tables()
        
        # Sort issues by line number
        self.issues.sort(key=lambda x: x.line_number)
        
        return [asdict(issue) for issue in self.issues]


def validate_markdown_file(file_path: str) -> dict:
    """
    Main function to validate a Markdown file.
    
    This function is designed to be called by the ADK agent as a tool.
    
    Args:
        file_path: Path to the Markdown file to validate
        
    Returns:
        Dictionary containing validation results with:
        - file_path: The validated file path
        - total_issues: Count of issues found
        - errors: Count of error-level issues
        - warnings: Count of warning-level issues
        - info: Count of info-level issues
        - issues: List of detailed issue objects
    """
    validator = MarkdownValidator(file_path)
    issues = validator.validate_all()
    
    # Categorize issues by severity
    errors = [i for i in issues if i['severity'] == 'error']
    warnings = [i for i in issues if i['severity'] == 'warning']
    info = [i for i in issues if i['severity'] == 'info']
    
    return {
        "file_path": file_path,
        "total_issues": len(issues),
        "errors": len(errors),
        "warnings": len(warnings),
        "info": len(info),
        "issues": issues,
        "summary": f"Found {len(errors)} errors, {len(warnings)} warnings, and {len(info)} info messages"
    }


# For testing directly
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) > 1:
        result = validate_markdown_file(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python markdown_validator.py <path_to_markdown_file>")
