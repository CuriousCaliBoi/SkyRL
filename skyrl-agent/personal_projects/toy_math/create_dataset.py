"""Generate toy math problems dataset for training."""
import pandas as pd
import random
from pathlib import Path
from typing import List, Dict, Any


def generate_arithmetic_problem() -> Dict[str, Any]:
    """Generate a simple arithmetic problem."""
    ops = ["+", "-", "*", "/"]
    op = random.choice(ops)
    
    if op == "+":
        a, b = random.randint(1, 100), random.randint(1, 100)
        answer = a + b
        problem = f"What is {a} + {b}?"
    elif op == "-":
        a, b = random.randint(1, 100), random.randint(1, 50)
        answer = a - b
        problem = f"What is {a} - {b}?"
    elif op == "*":
        a, b = random.randint(1, 20), random.randint(1, 20)
        answer = a * b
        problem = f"What is {a} × {b}?"
    else:  # division
        b = random.randint(2, 10)
        a = b * random.randint(1, 10)
        answer = a // b
        problem = f"What is {a} ÷ {b}?"
    
    return {
        "problem": problem,
        "answer": str(answer),
        "type": "arithmetic"
    }


def generate_word_problem() -> Dict[str, Any]:
    """Generate a simple word problem."""
    problem_types = [
        {
            "template": "If a train travels {speed} miles per hour for {time} hours, how far does it travel?",
            "gen": lambda: {
                "speed": random.randint(20, 80),
                "time": random.randint(1, 5)
            },
            "solve": lambda d: d["speed"] * d["time"]
        },
        {
            "template": "Sarah has {apples} apples. She gives away {given} apples. How many apples does she have left?",
            "gen": lambda: {
                "apples": random.randint(10, 50),
                "given": random.randint(1, 10)
            },
            "solve": lambda d: d["apples"] - d["given"]
        },
        {
            "template": "A store sells {items} items for ${price} each. How much money does the store make?",
            "gen": lambda: {
                "items": random.randint(5, 20),
                "price": random.randint(5, 20)
            },
            "solve": lambda d: d["items"] * d["price"]
        },
        {
            "template": "There are {total} students in a class. {boys} are boys. How many are girls?",
            "gen": lambda: {
                "total": random.randint(20, 40),
                "boys": random.randint(10, 20)
            },
            "solve": lambda d: d["total"] - d["boys"]
        },
    ]
    
    problem_type = random.choice(problem_types)
    params = problem_type["gen"]()
    problem = problem_type["template"].format(**params)
    answer = str(problem_type["solve"](params))
    
    return {
        "problem": problem,
        "answer": answer,
        "type": "word_problem"
    }


def create_dataset(num_examples: int, split_name: str = "train") -> pd.DataFrame:
    """Create a dataset of math problems."""
    data = []
    
    for i in range(num_examples):
        # Mix arithmetic and word problems (70% arithmetic, 30% word)
        if random.random() < 0.7:
            item = generate_arithmetic_problem()
        else:
            item = generate_word_problem()
        
        # Format as expected by SkyRL-Agent
        prompt = [
            {
                "role": "user",
                "content": item["problem"]
            }
        ]
        
        data.append({
            "prompt": prompt,
            "raw_prompt": prompt,  # For training format
            "reward_model": {
                "ground_truth": item["answer"]
            },
            "data_source": "toy_math",
            "extra_info": {
                "problem_type": item["type"]
            }
        })
    
    return pd.DataFrame(data)


def main():
    """Generate train and validation datasets."""
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    # Generate datasets
    print("Generating training dataset...")
    train_df = create_dataset(num_examples=100, split_name="train")
    train_path = output_dir / "train.parquet"
    train_df.to_parquet(train_path, index=False)
    print(f"Saved {len(train_df)} examples to {train_path}")
    
    print("Generating validation dataset...")
    val_df = create_dataset(num_examples=20, split_name="val")
    val_path = output_dir / "val.parquet"
    val_df.to_parquet(val_path, index=False)
    print(f"Saved {len(val_df)} examples to {val_path}")
    
    print("\nDataset generation complete!")
    print(f"Train: {train_path}")
    print(f"Val: {val_path}")


if __name__ == "__main__":
    main()
