"""
Truco Gaúcho — MaskablePPO self-play training script.

Usage:
    python train.py                         # train from scratch
    python train.py --load models/truco     # resume from checkpoint
    python train.py --steps 500000          # custom step budget

The trained model is saved to models/truco_<step>.zip periodically
and to models/truco_final.zip at the end.
"""
import argparse
import os

from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback, CallbackList
from truco.rl.env import TrucoEnv
from truco.rl.self_play import SelfPlayOpponent, SelfPlayCallback


# ── Hyperparameters ────────────────────────────────────────────────────────────
N_ENVS = 8                 # parallel envs (CPU-bound, no GPU needed)
TOTAL_STEPS = 5_000_000    # total training timesteps
SELF_PLAY_UPDATE = 20_000  # copy model -> opponent every N steps
CHECKPOINT_FREQ = 250_000  # save checkpoint every N steps
LEARNING_RATE = 2e-4
N_STEPS = 512              # rollout buffer length per env
BATCH_SIZE = 256
N_EPOCHS = 6
GAMMA = 0.99
ENT_COEF = 0.005           # lower entropy: exploit more after initial exploration
# Network: two hidden layers of 256 units each (4x larger than default 64)
POLICY_KWARGS = dict(net_arch=[256, 256])
# ──────────────────────────────────────────────────────────────────────────────


def make_env(opponent):
    """Factory: returns a callable that creates a masked TrucoEnv."""
    def _factory():
        env = TrucoEnv(opponent_policy=opponent)
        env = ActionMasker(env, lambda e: e.action_masks())
        return env
    return _factory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--load", type=str, default=None, help="Path to model zip to resume")
    parser.add_argument("--steps", type=int, default=TOTAL_STEPS, help="Total training steps")
    args = parser.parse_args()

    os.makedirs("models", exist_ok=True)

    # Shared opponent object — updated by SelfPlayCallback during training
    opponent = SelfPlayOpponent()

    # Vectorised environment with action masking
    vec_env = make_vec_env(make_env(opponent), n_envs=N_ENVS)

    # Build or load model
    if args.load:
        print(f"Loading model from {args.load}")
        model = MaskablePPO.load(args.load, env=vec_env)
    else:
        model = MaskablePPO(
            "MlpPolicy",
            vec_env,
            learning_rate=LEARNING_RATE,
            n_steps=N_STEPS,
            batch_size=BATCH_SIZE,
            n_epochs=N_EPOCHS,
            gamma=GAMMA,
            ent_coef=ENT_COEF,
            policy_kwargs=POLICY_KWARGS,
            verbose=1,
        )

    # Callbacks
    checkpoint_cb = CheckpointCallback(
        save_freq=max(CHECKPOINT_FREQ // N_ENVS, 1),
        save_path="models/",
        name_prefix="truco",
    )
    self_play_cb = SelfPlayCallback(
        opponent=opponent,
        update_freq=SELF_PLAY_UPDATE,
        verbose=1,
    )

    print(f"Training for {args.steps:,} steps with {N_ENVS} parallel envs …")
    model.learn(
        total_timesteps=args.steps,
        callback=CallbackList([checkpoint_cb, self_play_cb]),
        reset_num_timesteps=args.load is None,
    )

    model.save("models/truco_final")
    print("Saved -> models/truco_final.zip")


if __name__ == "__main__":
    main()
