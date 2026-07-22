"""
Evaluate a trained Truco model against a random opponent.

Usage:
    python evaluate.py models/truco_final        # evaluate saved model
    python evaluate.py models/truco_final --games 1000
"""
import argparse
import numpy as np
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker

from truco.rl.env import TrucoEnv, RandomPolicy


def evaluate(model_path: str, n_games: int = 500) -> dict:
    model = MaskablePPO.load(model_path)

    env = TrucoEnv(opponent_policy=RandomPolicy())
    env = ActionMasker(env, lambda e: e.action_masks())

    wins = 0
    total_steps = 0

    for _ in range(n_games):
        obs, _ = env.reset()
        for step in range(1000):
            masks = env.action_masks()
            action, _ = model.predict(obs, action_masks=masks, deterministic=True)
            obs, reward, done, _, _ = env.step(int(action))
            total_steps += 1
            if done:
                if reward > 0:
                    wins += 1
                break

    win_rate = wins / n_games
    avg_steps = total_steps / n_games
    return {"win_rate": win_rate, "wins": wins, "games": n_games, "avg_steps_per_game": avg_steps}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=str, help="Path to model zip (without .zip)")
    parser.add_argument("--games", type=int, default=500)
    args = parser.parse_args()

    results = evaluate(args.model, args.games)
    print(f"Model : {args.model}")
    print(f"Games : {results['games']}")
    print(f"Wins  : {results['wins']}")
    print(f"Win % : {results['win_rate']:.1%}")
    print(f"Avg steps/game: {results['avg_steps_per_game']:.1f}")


if __name__ == "__main__":
    main()
