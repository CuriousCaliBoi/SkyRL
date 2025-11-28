"""Test script to verify imports and tool registration work correctly."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import tool to register it
from personal_projects.toy_math.python_eval_tool import PythonEvalTool
from personal_projects.toy_math.toy_math_task import ToyMathTask

# Check tool registration
from skyrl_agent.tools.base import TOOL_REGISTRY

print("Registered tools:", list(TOOL_REGISTRY.keys()))
assert "python_eval" in TOOL_REGISTRY, "python_eval tool not registered!"
print("✓ python_eval tool is registered")

# Test tool instantiation
tool = TOOL_REGISTRY["python_eval"]()
print(f"✓ Tool instantiated: {tool.name}")

# Test tool call
result = tool.call({"code": "2 + 3"})
print(f"✓ Tool call test: 2 + 3 = {result}")

# Test task
task = ToyMathTask
print(f"✓ Task imported: {task.__name__}")

print("\nAll imports and registrations successful!")
