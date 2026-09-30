# truco-rl

[![ci](https://github.com/nickolascheidt/truco-rl/actions/workflows/ci.yml/badge.svg)](https://github.com/nickolascheidt/truco-rl/actions/workflows/ci.yml)

*[Leia em português](README.pt-BR.md)*

A rule engine for 1v1 **Truco Gaúcho** (the trick-taking card game from southern Brazil) and a
reinforcement-learning agent that learns to play it through self-play, with no human games
and no hand-written strategy.

This is a portfolio project. The interesting parts are turning a game full of bluffing and
betting into a clean RL environment, and measuring the agent honestly.

## Results

The agent was trained for 5M steps by playing against snapshots of itself, then scored over
2,000 games against two opponents it **never trained against**:

- **Random** picks a uniformly random legal action.
- **Heuristic** is a rule-based bot that plays like a cautious beginner: bets envido only with
  a good score, calls truco with a strong card or a won round, and plays the cheapest card
  that wins each round. It beats Random 89% of the time.

| Checkpoint | vs Random | vs Heuristic |
|---:|---:|---:|
| 250k steps | 89.6% | 38.0% |
| 750k | 88.4% | 54.1% |
| 1.25M | 83.5% | 63.9% |
| **2.25M** | **83.9%** | **73.1%** |
| 3.0M | 81.5% | 60.1% |
| 3.5M | 79.0% | 52.6% |
| 5.0M (final) | 80.2% | 62.8% |

Win rates have a 95% margin of about ±2 points. For scale: Random vs Random wins 51%, and
Heuristic vs Heuristic wins 50.5%.

**What the curve shows.** The agent passes the heuristic bot at around 750k steps and peaks at
73% at 2.25M. After that it *gets worse*, dropping to 53% before recovering to about 60%.
This is the textbook failure of naive self-play: the opponent is always the latest snapshot,
so the agent specializes against its current self and forgets strategies that beat older
versions. The usual fix is an opponent pool (a league of past snapshots plus fixed bots),
which is the obvious next step and is not implemented here.

Reproduce with `python train.py` (about an hour on a laptop CPU, no GPU needed) and
`python evaluate.py models/truco_2250000_steps`. Trained models are not committed.

## How it works

- **Environment** (`truco/rl/env.py`): a [Gymnasium](https://gymnasium.farama.org/) env where
  the agent always acts as one player and the opponent policy runs inside `step()`. A game
  goes to 24 points. The reward is +1/−1 at the end of the game, plus a small shaping term
  proportional to points won or lost in each step, so envido and truco bets get a signal
  before the game ends.
- **Observation** (`truco/rl/obs.py`): 39 floats covering the agent's cards, the cards played
  in each round, the score, who is mano, round results, the state of each bet, and the envido
  score. The opponent's hand is hidden, as it is at the table.
- **Actions** (`truco/rl/actions.py`): 16 discrete actions (play one of three cards, call or
  answer each bet). An action mask marks the legal ones at every step, and
  [MaskablePPO](https://sb3-contrib.readthedocs.io/) from sb3-contrib only samples from those.
- **Self-play** (`truco/rl/self_play.py`): every 20k steps the current weights are copied into
  the opponent.

## Rules implemented

The engine covers 1v1 play. It follows the common Gaúcho rules as far as I know them;
regional variants differ, and where a choice had to be made it is listed here.

- **Cards**: 40-card Spanish deck. The fixed trumps (manilhas) are 1 of espadas, 1 of paus,
  7 of espadas and 7 of ouros, followed by 3, 2, the other aces, 12, 11, 10, the other 7s, 6, 5, 4.
- **Hand**: best of three rounds. A tied round is decided by the others (a tie after a won round
  keeps the winner of the first); if all three tie, the mano wins.
- **Truco**: Truco (2) → Retruco (3) → Vale Quatro (4). Refusing gives the caller the value before
  the raise.
- **Envido**: only in the first round, before the caller has played a card. The raise chain
  only goes up: Envido at most twice, Real Envido once, then Falta Envido, which ends it.
  Envido is worth 2 and Real Envido 3, added to what is already on the table; Falta Envido is
  worth what the losing side still needs to win the game. Ties go to the mano.
- **Flor** (three cards of one suit): cancels envido. Answering with *me achico* gives the
  declarer 4 and the other side 2; *contra flor* leads to a showdown worth 6 or to
  *contra flor al resto*.

Simplifications: there are no 2v2 or 3v3 teams, and no signs (señas) between partners.

## Project layout

```
truco/entities/   Card, Deck, Player, Team, Round, Hand, Game
truco/states/     betting state machines: Truco, Envido, Flor
truco/rl/         env, observation and action encoding, self-play, heuristic bot
tests/            pytest suite for the engine and the heuristic bot
train.py          MaskablePPO + self-play training
evaluate.py       win rate against the baselines, with a 95% interval
play.py           play against the agent in the terminal
watch.py          watch the agent play a full game
```

## Usage

Requires Python 3.11+.

```bash
pip install -e ".[rl,dev]"

pytest                                             # engine and bot tests

python train.py                                    # 5M steps, checkpoints every 250k
python train.py --steps 20000                      # quick smoke test
python train.py --load models/truco_1000000_steps  # resume

python evaluate.py models/truco_final              # vs random and heuristic
python evaluate.py heuristic                       # score a baseline the same way

python play.py models/truco_final                  # you vs the agent
python watch.py models/truco_final --opponent heuristic
```

## License

[MIT](LICENSE)
