#!/bin/bash
set -x

# =============================================================================
# SkyRL-train RL Training for Toy Math Agent
# =============================================================================
# This script trains a toy math agent using SkyRL-train backend
# =============================================================================

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Data paths
DATA_DIR="${DATA_DIR:-${SCRIPT_DIR}/data}"
TRAIN_DATA="${TRAIN_DATA:-${DATA_DIR}/train.parquet}"
VAL_DATA="${VAL_DATA:-${DATA_DIR}/val.parquet}"

# Output directory
OUTPUT_DIR="${OUTPUT_DIR:-${SCRIPT_DIR}/outputs/skyrl}"
mkdir -p "$OUTPUT_DIR"

# Model configuration
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-1.5B-Instruct}"

# Training hyperparameters
BATCH_SIZE="${BATCH_SIZE:-8}"
LEARNING_RATE="${LEARNING_RATE:-1e-4}"
MAX_STEPS="${MAX_STEPS:-50}"

# Task configuration
TASK_YAML="${TASK_YAML:-${SCRIPT_DIR}/toy_math.yaml}"

# Check if dataset exists, generate if not
if [ ! -f "$TRAIN_DATA" ]; then
    echo "Dataset not found. Generating dataset..."
    cd "$SCRIPT_DIR"
    python create_dataset.py
    if [ ! -f "$TRAIN_DATA" ]; then
        echo "Error: Failed to generate dataset at $TRAIN_DATA"
        exit 1
    fi
fi

echo "================================================"
echo "SkyRL-train RL Training for Toy Math Agent"
echo "================================================"
echo "Model: $MODEL_NAME"
echo "Train Data: $TRAIN_DATA"
echo "Val Data: $VAL_DATA"
echo "Task YAML: $TASK_YAML"
echo "Batch Size: $BATCH_SIZE"
echo "Max Steps: $MAX_STEPS"
echo "Output: $OUTPUT_DIR"
echo "================================================"

# Run training with SkyRL-train
# Note: This uses the SkyRL-train integration which handles the training loop
uv run --isolated --extra skyrl-train -m skyrl_agent.integrations.skyrl_train.skyrl_train_main \
    trainer.policy.model.path="$MODEL_NAME" \
    data.train_data="['$TRAIN_DATA']" \
    data.val_data="['$VAL_DATA']" \
    skyrl_agent_task_yaml="$TASK_YAML" \
    trainer.trainer.epochs=1 \
    trainer.trainer.max_steps="$MAX_STEPS" \
    trainer.trainer.batch_size="$BATCH_SIZE" \
    trainer.trainer.learning_rate="$LEARNING_RATE" \
    trainer.trainer.output_dir="$OUTPUT_DIR" \
    "$@"

echo "================================================"
echo "Training completed!"
echo "Checkpoints saved to: ${OUTPUT_DIR}"
echo "================================================"
