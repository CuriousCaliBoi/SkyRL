# Quick Start Guide

## 1. Generate Dataset

```bash
cd skyrl-agent/personal_projects/toy_math
python create_dataset.py
```

This creates:
- `data/train.parquet` (100 math problems)
- `data/val.parquet` (20 math problems)

## 2. Run Training (Tinker Backend)

```bash
cd skyrl-agent/personal_projects/toy_math
bash run_toy_math_tinker.sh
```

Or with custom settings:
```bash
MODEL_NAME="Qwen/Qwen2.5-1.5B-Instruct" \
BATCH_SIZE=8 \
MAX_STEPS=50 \
bash run_toy_math_tinker.sh
```

## 3. Run Training (SkyRL-train Backend)

```bash
cd skyrl-agent/personal_projects/toy_math
bash run_toy_math_skyrl.sh
```

## What to Expect

1. **Rollouts**: The agent will generate 4 trajectories per problem
2. **Transitions**: Each LLM call is recorded as a transition (observation, action, reward)
3. **Training**: GRPO/PPO training updates the model
4. **Metrics**: Watch for reward and success rate improvements

## Troubleshooting

### Tool not found error
If you see `Unknown tool 'python_eval'`, make sure the tool is imported. The task file imports it automatically, but if issues persist:

```python
# Add to your training script or ensure this runs before agent initialization
from personal_projects.toy_math.python_eval_tool import PythonEvalTool
```

### Import errors
Make sure you're running from the `skyrl-agent` directory and using `uv run` with the appropriate extras (`--extra tinker` or `--extra skyrl-train`).

### Dataset not found
Run `python create_dataset.py` first to generate the dataset files.
