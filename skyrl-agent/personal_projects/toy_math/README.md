# Project 1: Toy Math Agent

A minimal end-to-end math agent that exercises the full SkyRL-Agent stack: tool-centric agent loop, transition recording, and RL training.

## Overview

This project implements:
- **Environment**: Simple arithmetic and word problems
- **Tools**: `python_eval` (evaluate Python expressions), `finish` (submit answer)
- **Reward**: +1 if answer matches ground truth, 0 otherwise
- **Backend**: Tinker or SkyRL-train with GRPO-style training

## Project Structure

```
toy_math/
├── toy_math_task.py          # Math task implementation (BaseTask)
├── python_eval_tool.py        # Python eval tool (BaseTool)
├── create_dataset.py          # Dataset generator
├── toy_math.yaml             # Task configuration
├── run_toy_math_tinker.sh    # Tinker training script
├── run_toy_math_skyrl.sh     # SkyRL-train training script
├── README.md                  # This file
└── data/                      # Generated datasets (created by create_dataset.py)
    ├── train.parquet
    └── val.parquet
```

## Setup

1. **Generate the dataset**:
   ```bash
   cd skyrl-agent/personal_projects/toy_math
   python create_dataset.py
   ```
   This creates `data/train.parquet` (100 examples) and `data/val.parquet` (20 examples).

2. **Ensure tools are registered**:
   The `python_eval` tool is automatically registered when the task module is imported (via `@register_tool` decorator). The `ToyMathTask` class imports the tool to ensure registration.

3. **Verify setup** (optional):
   ```bash
   cd skyrl-agent
   uv run --isolated python personal_projects/toy_math/test_imports.py
   ```

## Running Training

### With Tinker Backend

```bash
cd personal_projects/toy_math
bash run_toy_math_tinker.sh
```

Configuration (via environment variables):
- `MODEL_NAME`: Model to use (default: `Qwen/Qwen2.5-1.5B-Instruct`)
- `BATCH_SIZE`: Training batch size (default: 8)
- `MAX_STEPS`: Number of training steps (default: 50)
- `GROUP_SIZE`: GRPO group size, should match `num_trajectories` in YAML (default: 4)

### With SkyRL-train Backend

```bash
cd personal_projects/toy_math
bash run_toy_math_skyrl.sh
```

## Success Criteria

- [x] Can run N rollouts (4 rollouts per problem)
- [x] Transitions are logged (via `@record_transition` decorator)
- [x] Training step executes without errors
- [ ] Reward/success rate improves on held-out problem set over training
- [ ] Can swap between Tinker and SkyRL-train backends via config

## Key Components

### ToyMathTask

Implements `BaseTask` with:
- `get_instruction()`: Formats math problems as OpenAI messages
- `evaluate_result()`: Compares agent answer to ground truth (+1 if match, 0 otherwise)

### PythonEvalTool

Implements `BaseTool` with:
- Safe Python expression evaluation
- Timeout protection (2 seconds)
- Restricted to basic math operations (no imports, no dangerous functions)

### Dataset Format

Each example in the parquet file has:
- `prompt`: List of messages with the math problem
- `raw_prompt`: Same as prompt (for training format)
- `reward_model.ground_truth`: Expected answer (string)
- `data_source`: "toy_math"
- `extra_info.problem_type`: "arithmetic" or "word_problem"

## Notes

- The tool registration happens automatically when the module is imported (via `@register_tool` decorator)
- Make sure the `personal_projects` directory is in your Python path or use relative imports
- For Tinker, you'll need a `.env` file with Tinker API configuration
- For SkyRL-train, ensure the model is accessible (HuggingFace or local path)
