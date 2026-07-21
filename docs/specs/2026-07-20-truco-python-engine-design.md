# Truco Python Engine — Design Spec

**Date:** 2026-07-20  
**Scope:** Port of `Truco.Core` (C#) to Python, 1v1 only, as the foundation for `truco-rl`.

---

## Goal

Reimplement the Truco Gaúcho game engine in Python as the canonical version of the game logic. The C# repo served as the validation ground; this Python package is where the project lives and evolves. Bugs found during port are fixed here, not in C#.

---

## Architecture

Two top-level packages inside the repo:

- `truco/` — the game engine, installable as a Python package. No dependencies beyond stdlib.
- `env/` — Gymnasium-compatible RL environment. Depends on `gymnasium` and `numpy`. Implemented in a future phase.

```
truco-rl/
├── truco/
│   ├── __init__.py
│   ├── enums.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── card.py
│   │   ├── deck.py
│   │   ├── player.py
│   │   ├── team.py
│   │   ├── round.py
│   │   ├── hand.py
│   │   ├── game.py
│   │   ├── bet_result.py
│   │   └── play_result.py
│   └── states/
│       ├── __init__.py
│       ├── truco_state.py
│       ├── envido_state.py
│       └── flor_state.py
├── env/
│   └── truco_env.py        # future phase
├── tests/
│   ├── entities/
│   │   ├── test_card.py
│   │   ├── test_deck.py
│   │   ├── test_player.py
│   │   ├── test_team.py
│   │   ├── test_round.py
│   │   ├── test_hand.py
│   │   ├── test_hand_envido_flor.py
│   │   ├── test_game.py
│   │   ├── test_bet_envido.py
│   │   ├── test_bet_flor.py
│   │   ├── test_bet_truco.py
│   │   └── test_score.py
│   └── states/
│       ├── test_envido_state.py
│       └── test_flor_state.py
├── pyproject.toml
└── README.md
```

---

## Components

### `enums.py`

| Python | C# source |
|---|---|
| `Suit` | `Naipe` |
| `BetType` | `TipoAposta` |
| `BetResponse` | `RespostaAposta` |
| `FlorResponse` | `RespostaFlor` |
| `BetStatus` | `StatusAposta` |

### `entities/card.py` — `Card`

- `number: int`, `suit: Suit`, `strength: int`, `envido_value: int`
- `strength` computed by `_calc_strength(number, suit)` — exact same hierarchy as C#
- `envido_value = number if number <= 7 else 0`

### `entities/deck.py` — `Deck`

- Valid numbers: `[1, 2, 3, 4, 5, 6, 7, 10, 11, 12]`
- `initialize()`, `shuffle()` (via `random.shuffle`), `deal_hand() -> list[Card]` (3 cards)

### `entities/player.py` — `Player`

- `name: str`, `hand: list[Card]`
- `play_card(card) -> Card`, `clear_hand()`

### `entities/team.py` — `Team`

- `name: str`, `players: list[Player]`, `points: int`
- `add_points(value)` — raises `ValueError` if value <= 0
- 1v1 constraint: always 1 player per team

### `entities/round.py` — `Round`

- `plays: dict[Player, Card]`, `winner: Player | None`, `resolved: bool`
- `register_play(player, card)`, `resolve() -> Player | None`

### `entities/hand.py` — `Hand`

- Holds `rounds`, `truco`, `envido`, `flor` states
- `current_player`, `mano_player` tracking
- `can_envido(player) -> bool`, `can_flor(player) -> bool`
- `envido_value(player) -> int`, `flor_value(player) -> int`
- `has_flor(player) -> bool` (staticmethod)
- `register_play(player, card, all_players) -> Player | None`
- `resolve(teams) -> Team | None` — full tiebreaker logic

### `entities/game.py` — `Game`

Public API mirrors `Jogo.cs`:

- `start_hand()`
- `play_card(player, card) -> PlayResult`
- `can_ask_truco(player) -> bool`
- `ask_truco(player) -> BetResult`
- `respond_truco(player, response) -> BetResult`
- `can_envido(player) -> bool`
- `ask_envido(player, bet_type) -> BetResult`
- `respond_envido(player, response) -> BetResult`
- `can_flor(player) -> bool`
- `declare_flor(player) -> BetResult`
- `respond_flor(player, response) -> BetResult`
- `get_score() -> Score`
- `check_game_over() -> bool`

### `entities/bet_result.py` — `BetResult`

- `bet_pending: bool`, `hand_value: int`, `hand_over: bool`
- `winner_team: Team | None`, `who_responds: Player | None`
- `points_winner: int`, `points_loser: int`

### `entities/play_result.py` — `PlayResult`

- `round_winner: Player | None`, `round_over: bool`
- `hand_winner: Team | None`, `hand_over: bool`
- `next_player: Player | None`, `round_number: int`

### `states/truco_state.py` — `TrucoState`

- `current_value: int` (starts at 1), `value_if_refused: int`, `who_asked: Team | None`, `status: BetStatus`
- `can_ask(team) -> bool`
- `ask(team)`, `accept()`, `refuse()`, `raise_bet(team)`

### `states/envido_state.py` — `EnvidoState`

- `value_accepted: int`, `value_if_refused: int`, `bet_type: BetType | None`, `who_asked: Player | None`, `status: BetStatus`
- `ask(player, bet_type, points_to_win=0)`, `accept()`, `refuse()`

### `states/flor_state.py` — `FlorState`

- `who_declared: Team | None`, `both_declared: bool`, `contra_flor_pending: bool`, `over: bool`, `envido_cancelled: bool`
- `waiting_for_response` (property)
- `declare(team)`, `close()`

---

## Translation Rules

| C# pattern | Python equivalent |
|---|---|
| `get; private set;` | `@property` + `_attr` or public attr set only within class |
| `throw new InvalidOperationException` | `raise RuntimeError(...)` |
| `throw new ArgumentException` | `raise ValueError(...)` |
| `null` | `None` |
| `Dictionary<K,V>` | `dict[K, V]` |
| `List<T>` | `list[T]` |
| `static` method | `@staticmethod` |

---

## Tests

Each file in `tests/` mirrors the corresponding C# test file. Same scenarios, same assertions, translated to `pytest`. No mocking, no fixtures beyond simple object construction.

---

## Packaging

```toml
[project]
name = "truco"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## Out of Scope

- `IJogadorStrategy`, `HumanStrategy`, `SimpleBot` — replaced by RL agents in `env/`
- Unity integration
- `env/truco_env.py` — future phase
- Multi-player teams (2v2, 3v3)
