# truco-rl

Rule engine for 1v1 Truco Gaúcho, plus a reinforcement-learning agent trained via self-play.

## Structure

- `truco/entities/` — domain model (Card, Deck, Player, Team, Round, Hand, Game).
- `truco/states/` — betting state machines (Truco, Envido, Flor).
- `truco/rl/` — Gymnasium environment (`env.py`), observation/action encoding (`obs.py`, `actions.py`) and self-play (`self_play.py`).
- `tests/` — engine unit tests (pytest).
- `api.py` — FastAPI microservice for Unity integration.
- `train.py` / `evaluate.py` / `play.py` / `watch.py` — training, evaluation, human-vs-agent terminal play, and match visualization scripts.

## Usage

```bash
# install dependencies
pip install -e .

# run the tests
pytest

# train from scratch (MaskablePPO + self-play, 5M steps by default)
python train.py

# resume training from a checkpoint
python train.py --load models/truco_1000000_steps

# short training run to smoke-test the pipeline
python train.py --steps 10000

# evaluate a trained model
python evaluate.py

# play against the agent in the terminal
python play.py

# watch a match (agent vs. agent/random)
python watch.py

# start the API for Unity integration
python api.py
```

Trained models (`models/*.zip`) are not versioned — see `.gitignore`.
