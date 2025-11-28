from skyrl_agent.tools.base import BaseTool, register_tool
from typing import Union
import subprocess
import ast
import re


@register_tool("python_eval")
class PythonEvalTool(BaseTool):
    """Tool for evaluating simple Python expressions safely."""
    
    name = "python_eval"
    description = (
        "Evaluates a simple Python expression and returns the result.\n\n"
        "Use this tool to perform mathematical calculations.\n"
        "Examples:\n"
        "- python_eval(code='2 + 3') returns '5'\n"
        "- python_eval(code='10 * 5') returns '50'\n"
        "- python_eval(code='100 / 4') returns '25.0'\n\n"
        "Note: Only basic mathematical operations are supported. No imports or complex operations."
    )
    parameters = {
        "type": "object",
        "required": ["code"],
        "properties": {
            "code": {
                "type": "string",
                "description": "A simple Python expression to evaluate (e.g., '2 + 3', '10 * 5')"
            },
        },
    }

    def __init__(self, cfg: dict = None):
        super().__init__(cfg)
        self.timeout = self.cfg.get("timeout", 2.0)

    def call(self, params: Union[str, dict], **kwargs) -> str:
        """Execute a simple Python expression safely."""
        try:
            params = self._verify_json_format_args(params)
        except ValueError as e:
            return f"Error: Invalid parameters: {str(e)}"

        code = params.get("code", "").strip()
        if not code:
            return "Error: No code provided"

        # Basic safety check: only allow simple expressions
        # Remove whitespace for checking
        code_clean = re.sub(r'\s+', '', code)
        
        # Block dangerous patterns
        dangerous_patterns = [
            'import', 'exec', 'eval', '__', 'open', 'file', 'input',
            'raw_input', 'compile', 'reload', 'exit', 'quit', 'sys',
            'os', 'subprocess', 'globals', 'locals', 'vars', 'dir'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code_clean.lower():
                return f"Error: Forbidden pattern '{pattern}' detected. Only simple mathematical expressions are allowed."

        try:
            # Use ast.literal_eval for safe evaluation of literals
            # But for expressions like "2 + 3", we need a safer approach
            # Try to parse as expression first
            try:
                # Parse as expression to check syntax
                parsed = ast.parse(code, mode='eval')
                
                # Check if it's a simple expression (no function calls, no attributes)
                for node in ast.walk(parsed):
                    if isinstance(node, ast.Call):
                        return "Error: Function calls are not allowed. Use only basic math operations."
                    if isinstance(node, ast.Attribute):
                        return "Error: Attribute access is not allowed. Use only basic math operations."
                    if isinstance(node, ast.Name) and node.id not in ['True', 'False', 'None']:
                        # Allow constants but not variables
                        return f"Error: Variables are not allowed. Use only numbers and basic operations."
                
                # If parsing succeeded, evaluate using subprocess with timeout
                result = subprocess.run(
                    ["python3", "-c", f"print({code})"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=self.timeout,
                    text=True
                )
                
                if result.returncode != 0:
                    return f"Error executing code: {result.stderr.strip()}"
                
                output = result.stdout.strip()
                return output if output else "No output"
                
            except SyntaxError as e:
                return f"Error: Invalid Python syntax: {str(e)}"
                
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out after {self.timeout} seconds"
        except Exception as e:
            return f"Error: {str(e)}"
