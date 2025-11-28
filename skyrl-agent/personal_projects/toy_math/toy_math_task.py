from typing import Dict, Any, List
from skyrl_agent.tasks.base import BaseTask

# Import to ensure python_eval tool is registered
try:
    from personal_projects.toy_math.python_eval_tool import PythonEvalTool
except ImportError:
    # Fallback if import path doesn't work
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from personal_projects.toy_math.python_eval_tool import PythonEvalTool


class ToyMathTask(BaseTask):
    """Simple math task for toy agent - arithmetic and word problems."""

    @classmethod
    async def initialize_runtime(cls, *args, **kwargs) -> Any:
        """No runtime initialization needed for math problems."""
        pass

    @classmethod
    def get_instruction(cls, instance: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get the initial instruction for the agent in OpenAI messages format."""
        # Handle both "prompt" (inference) and "raw_prompt" (training) formats
        if "raw_prompt" in instance:
            import numpy
            assert isinstance(
                instance.get("raw_prompt"), numpy.ndarray
            ), f"Raw prompt must be a numpy array, but got {type(instance.get('raw_prompt'))}"
            assert (
                len(instance.get("raw_prompt")) == 1
            ), f"Raw prompt must have only one element, but got {len(instance.get('raw_prompt'))}"
            prompt = list(instance.get("raw_prompt"))
        else:
            prompt = instance.get("prompt", [])

        # Ensure prompt is a list of messages
        if isinstance(prompt, str):
            prompt = [{"role": "user", "content": prompt}]
        elif not isinstance(prompt, list):
            raise ValueError(f"Prompt must be a list or string, but got {type(prompt)}")

        # Add system prompt if not present
        has_system = any(msg.get("role") == "system" for msg in prompt)
        if not has_system:
            system_prompt = {
                "role": "system",
                "content": (
                    "You are a helpful math assistant. Solve the given math problem step by step.\n"
                    "You can use the python_eval tool to evaluate mathematical expressions.\n"
                    "When you have the final answer, use the finish tool with your answer.\n"
                    "Format: <function=finish>\n<parameter=answer>Your answer here</parameter>\n</function>"
                ),
            }
            prompt = [system_prompt] + prompt

        return prompt

    @classmethod
    def complete_runtime(cls, *args, **kwargs) -> Dict[str, Any]:
        """No runtime completion needed."""
        return {}

    @classmethod
    async def evaluate_result(
        cls, result: Any, instance: Dict[str, Any], data_source: str, instance_id: int, trajectory_id: int
    ) -> float:
        """Evaluate the agent's answer against ground truth.
        
        Returns:
            float: 1.0 if answer matches ground truth, 0.0 otherwise
        """
        if not result:
            return 0.0

        ground_truth = instance.get("reward_model", {}).get("ground_truth", "")
        if not ground_truth:
            return 0.0

        # Extract answer from result (should be string from finish tool)
        answer = str(result).strip() if result else ""
        ground_truth_str = str(ground_truth).strip()

        # Normalize: remove whitespace, convert to lowercase for comparison
        answer_normalized = answer.lower().replace(" ", "").replace(",", "")
        ground_truth_normalized = ground_truth_str.lower().replace(" ", "").replace(",", "")

        # Try numeric comparison if both are numbers
        try:
            answer_num = float(answer_normalized)
            ground_truth_num = float(ground_truth_normalized)
            is_correct = abs(answer_num - ground_truth_num) < 1e-6
        except ValueError:
            # Fall back to string comparison
            is_correct = answer_normalized == ground_truth_normalized

        reward = 1.0 if is_correct else 0.0
        print(f"[ToyMathTask] Evaluating: answer='{answer}' vs ground_truth='{ground_truth_str}' -> reward={reward}")
        
        return reward
