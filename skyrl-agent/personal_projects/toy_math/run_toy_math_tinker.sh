#!/bin/bash
set -x

# =============================================================================
# Tinker RL Training for Toy Math Agent
# =============================================================================
# This script trains a toy math agent using Tinker backend with GRPO/PPO
# =============================================================================

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Data paths - use local data directory
DATA_DIR="${DATA_DIR:-${SCRIPT_DIR}/data}"
DATASET_FILE="${DATASET_FILE:-${DATA_DIR}/train.parquet}"
EVAL_DATASET_FILE="${EVAL_DATASET_FILE:-${DATA_DIR}/val.parquet}"

# Output directory
OUTPUT_DIR="${OUTPUT_DIR:-${SCRIPT_DIR}/outputs/tinker}"
mkdir -p "$OUTPUT_DIR"

# Model configuration
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-1.5B-Instruct}"
LORA_RANK="${LORA_RANK:-16}"

# Training hyperparameters
BATCH_SIZE="${BATCH_SIZE:-8}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-4}"
LEARNING_RATE="${LEARNING_RATE:-1e-4}"
MAX_STEPS="${MAX_STEPS:-50}"
SAVE_EVERY="${SAVE_EVERY:-10}"
EVAL_EVERY="${EVAL_EVERY:-5}"

# RL configuration
LOSS_FN="${LOSS_FN:-ppo}"
GROUP_SIZE="${GROUP_SIZE:-4}"  # Should match num_trajectories in YAML
NORMALIZE_ADVANTAGES="${NORMALIZE_ADVANTAGES:-false}"

# Logging
WANDB_PROJECT="${WANDB_PROJECT:-toy-math-agent}"
WANDB_NAME="${WANDB_NAME:-toy-math-tinker-$(date +%Y%m%d_%H%M%S)}"
RESUME_EXP_NAME="${RESUME_EXP_NAME:-}"

# Task configuration
TASK_YAML="${TASK_YAML:-${SCRIPT_DIR}/toy_math.yaml}"

# Check if dataset exists, generate if not
if [ ! -f "$DATASET_FILE" ]; then
    echo "Dataset not found. Generating dataset..."
    cd "$SCRIPT_DIR"
    python create_dataset.py
    if [ ! -f "$DATASET_FILE" ]; then
        echo "Error: Failed to generate dataset at $DATASET_FILE"
        exit 1
    fi
fi

echo "================================================"
echo "Tinker RL Training for Toy Math Agent"
echo "================================================"
echo "Model: $MODEL_NAME"
echo "Dataset: $DATASET_FILE"
echo "Eval Dataset: $EVAL_DATASET_FILE"
echo "Task YAML: $TASK_YAML"
echo "Batch Size: $BATCH_SIZE"
echo "Group Size (GRPO): $GROUP_SIZE"
echo "Max Steps: $MAX_STEPS"
echo "Output: $OUTPUT_DIR"
echo "================================================"

# Run training
uv run --isolated --extra tinker --env-file .env -m skyrl_agent.integrations.tinker.tinker_train \
    model_name="$MODEL_NAME" \
    skyrl_agent_task_yaml="$TASK_YAML" \
    dataset_file="$DATASET_FILE" \
    eval_dataset_file="$EVAL_DATASET_FILE" \
    batch_size="$BATCH_SIZE" \
    eval_batch_size="$EVAL_BATCH_SIZE" \
    learning_rate="$LEARNING_RATE" \
    lora_rank="$LORA_RANK" \
    max_steps="$MAX_STEPS" \
    save_every="$SAVE_EVERY" \
    eval_every="$EVAL_EVERY" \
    loss_fn="$LOSS_FN" \
    group_size="$GROUP_SIZE" \
    normalize_advantages="$NORMALIZE_ADVANTAGES" \
    wandb_project="$WANDB_PROJECT" \
    wandb_name="$WANDB_NAME" \
    resume_exp_name="$RESUME_EXP_NAME" \
    log_dir="$OUTPUT_DIR" \
    "$@"

echo "================================================"
echo "Training completed!"
echo "Checkpoints saved to: ${OUTPUT_DIR}/tinker_output/${WANDB_NAME}_*"
echo "================================================"
