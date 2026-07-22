from __future__ import annotations
import io
import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

from truco.rl.actions import N_ACTIONS


class SelfPlayOpponent:
    """
    Opponent for self-play training.
    Uses BytesIO serialisation to snapshot the model without deepcopy issues.
    Falls back to random play until the first snapshot is loaded.

    Note: designed for DummyVecEnv (single-threaded); no locking required.
    """

    def __init__(self):
        self._snapshot_bytes: bytes | None = None
        self._cached_model = None
        self._cached_version = -1
        self._version = 0

    def update(self, model) -> None:
        """Snapshot the current model weights for future opponent predictions."""
        buf = io.BytesIO()
        model.save(buf)
        buf.seek(0)
        self._snapshot_bytes = buf.read()
        self._version += 1

    def predict(self, obs: np.ndarray, action_masks: np.ndarray | None = None):
        if self._snapshot_bytes is None:
            return self._random(action_masks)

        # Lazy-load: rebuild model only when snapshot changed
        if self._version != self._cached_version:
            from sb3_contrib import MaskablePPO
            buf = io.BytesIO(self._snapshot_bytes)
            self._cached_model = MaskablePPO.load(buf)
            self._cached_version = self._version

        obs_2d = obs[np.newaxis, :]
        masks_2d = action_masks[np.newaxis, :] if action_masks is not None else None
        action, _ = self._cached_model.predict(
            obs_2d, action_masks=masks_2d, deterministic=False
        )
        return int(action[0]), None

    @staticmethod
    def _random(action_masks):
        legal = np.where(action_masks)[0] if action_masks is not None else np.arange(N_ACTIONS)
        return int(np.random.choice(legal)), None


class SelfPlayCallback(BaseCallback):
    """
    Copies the current model into a shared SelfPlayOpponent every `update_freq` steps.

    Pass the same `opponent` object to both this callback and TrucoEnv so
    all envs automatically receive the updated policy.
    """

    def __init__(self, opponent: SelfPlayOpponent, update_freq: int = 10_000, verbose: int = 0):
        super().__init__(verbose)
        self.opponent = opponent
        self.update_freq = update_freq
        self._last_update = 0

    def _on_step(self) -> bool:
        if self.num_timesteps - self._last_update >= self.update_freq:
            self.opponent.update(self.model)
            self._last_update = self.num_timesteps
            if self.verbose >= 1:
                print(f"[SelfPlay] step={self.num_timesteps}: opponent updated")
        return True
