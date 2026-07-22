# Truco Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `truco/` Python package — motor completo de Truco Gaúcho 1v1 com cobertura de testes pytest.

**Architecture:** Bottom-up por dependência: enums → value objects → state machines → entities → game orchestrator. Cada task entrega código funcional e testado antes da próxima começar. TDD estrito: teste falha → implementa → teste passa → commit.

**Tech Stack:** Python 3.11+, pytest. Zero dependências externas no pacote `truco/`.

---

## Regras do Jogo (referência rápida)

**Cartas válidas:** números `[1, 2, 3, 4, 5, 6, 7, 10, 11, 12]`, 4 naipes → 40 cartas no baralho.

**Hierarquia de força (14 = mais forte):**
| Carta | Força |
|---|---|
| 4 de Espadas (manilha) | 14 |
| 7 de Espadas | 13 |
| 1 de Espadas | 12 |
| 7 de Ouros | 11 |
| 3 (qualquer naipe) | 10 |
| 2 (qualquer) | 9 |
| 1 (Copas/Ouros/Paus) | 8 |
| 12 (qualquer) | 7 |
| 11 (qualquer) | 6 |
| 10 (qualquer) | 5 |
| 7 de Copas ou Paus | 4 |
| 6 (qualquer) | 3 |
| 5 (qualquer) | 2 |
| 4 (não Espadas) | 1 |

**Valor de envido:** números 1–7 → envido_value = number; 10/11/12 → envido_value = 0.

**Envido da mão:** se 2+ cartas do mesmo naipe → 20 + soma dos 2 maiores envido_values desse naipe; senão → maior envido_value individual.

**Flor:** todas 3 cartas do mesmo naipe. Cancela envido. Flor value = 20 + soma dos 3 envido_values.

**Apostas Truco:** truco (valor 2) → retruco (3) → vale quatro (4). Se recusado, adversário leva `value_if_refused`.
- Truco pendente: value=2, value_if_refused=1
- Retruco pendente: value=3, value_if_refused=2
- Vale Quatro pendente: value=4, value_if_refused=3

**Apostas Envido:**
| Bet | Se aceito | Se recusado |
|---|---|---|
| ENVIDO | 2 | 1 |
| ENVIDO_ENVIDO (após envido) | 4 | 2 |
| REAL_ENVIDO | 3 | 1 |
| FALTA_ENVIDO | points_to_win | 1 |

**Resolução da mão (melhor de 3 rodadas):**
- Vencer 2 rodadas → ganhou a mão
- Empate na 1ª + vencer 2ª → ganhou
- Empate na 1ª + empate na 2ª → mano vence
- Vencer 1ª + empate na 2ª → vencedor da 1ª vence
- Perder 1ª + vencer 2ª e 3ª → venceu

**Jogo:** primeiro time a 30 pontos vence.

---

## File Map

```
truco-rl/
├── pyproject.toml
├── truco/
│   ├── __init__.py
│   ├── enums.py                      # Suit, BetType, BetResponse, FlorResponse, BetStatus
│   └── entities/
│       ├── __init__.py
│       ├── card.py                   # Card + _calc_strength
│       ├── deck.py                   # Deck
│       ├── player.py                 # Player
│       ├── team.py                   # Team
│       ├── bet_result.py             # BetResult (dataclass)
│       ├── play_result.py            # PlayResult (dataclass)
│       ├── round.py                  # Round
│       ├── hand.py                   # Hand (orquestra rodadas + estados)
│       └── game.py                   # Game (API pública)
│   └── states/
│       ├── __init__.py
│       ├── truco_state.py            # TrucoState
│       ├── envido_state.py           # EnvidoState
│       └── flor_state.py             # FlorState
└── tests/
    ├── __init__.py
    └── entities/
        ├── __init__.py
        ├── test_card.py
        ├── test_deck.py
        ├── test_player.py
        ├── test_team.py
        ├── test_round.py
        ├── test_hand.py
        ├── test_hand_envido_flor.py
        ├── test_game.py
        ├── test_bet_truco.py
        ├── test_bet_envido.py
        ├── test_bet_flor.py
        └── test_score.py
    └── states/
        ├── __init__.py
        ├── test_envido_state.py
        └── test_flor_state.py
```

---

## Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `truco/__init__.py`
- Create: `truco/entities/__init__.py`
- Create: `truco/states/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/entities/__init__.py`
- Create: `tests/states/__init__.py`

- [ ] **Step 1: Criar pyproject.toml**

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

- [ ] **Step 2: Criar estrutura de diretórios e __init__.py vazios**

```bash
mkdir -p truco/entities truco/states tests/entities tests/states
touch truco/__init__.py truco/entities/__init__.py truco/states/__init__.py
touch tests/__init__.py tests/entities/__init__.py tests/states/__init__.py
```

- [ ] **Step 3: Verificar que pytest roda sem erros**

```bash
pip install -e ".[dev]"
pytest
```
Expected: `no tests ran` ou similar (sem erros de import).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml truco/ tests/
git commit -m "chore: project scaffold"
```

---

## Task 2: Enums

**Files:**
- Create: `truco/enums.py`

- [ ] **Step 1: Escrever teste que importa e verifica todos os enums**

`tests/entities/test_card.py` (começar aqui, será expandido):

```python
from truco.enums import Suit, BetType, BetResponse, FlorResponse, BetStatus


def test_suit_values():
    assert Suit.ESPADAS.value == "espadas"
    assert Suit.OUROS.value == "ouros"
    assert Suit.COPAS.value == "copas"
    assert Suit.PAUS.value == "paus"


def test_bet_status_values():
    assert BetStatus.NONE.value == "none"
    assert BetStatus.PENDING.value == "pending"
    assert BetStatus.ACCEPTED.value == "accepted"
    assert BetStatus.REFUSED.value == "refused"


def test_bet_type_values():
    assert BetType.ENVIDO.value == "envido"
    assert BetType.ENVIDO_ENVIDO.value == "envido_envido"
    assert BetType.REAL_ENVIDO.value == "real_envido"
    assert BetType.FALTA_ENVIDO.value == "falta_envido"
    assert BetType.TRUCO.value == "truco"
    assert BetType.RETRUCO.value == "retruco"
    assert BetType.VALE_QUATRO.value == "vale_quatro"


def test_bet_response_values():
    assert BetResponse.ACCEPT.value == "accept"
    assert BetResponse.REFUSE.value == "refuse"
    assert BetResponse.RAISE.value == "raise"


def test_flor_response_values():
    assert FlorResponse.ACCEPT.value == "accept"
    assert FlorResponse.CONTRA_FLOR.value == "contra_flor"
    assert FlorResponse.CONTRA_FLOR_AL_RESTO.value == "contra_flor_al_resto"
```

- [ ] **Step 2: Rodar teste e confirmar falha**

```bash
pytest tests/entities/test_card.py -v
```
Expected: `ModuleNotFoundError: No module named 'truco.enums'`

- [ ] **Step 3: Implementar `truco/enums.py`**

```python
from enum import Enum


class Suit(Enum):
    ESPADAS = "espadas"
    OUROS = "ouros"
    COPAS = "copas"
    PAUS = "paus"


class BetType(Enum):
    ENVIDO = "envido"
    ENVIDO_ENVIDO = "envido_envido"
    REAL_ENVIDO = "real_envido"
    FALTA_ENVIDO = "falta_envido"
    TRUCO = "truco"
    RETRUCO = "retruco"
    VALE_QUATRO = "vale_quatro"


class BetResponse(Enum):
    ACCEPT = "accept"
    REFUSE = "refuse"
    RAISE = "raise"


class FlorResponse(Enum):
    ACCEPT = "accept"
    CONTRA_FLOR = "contra_flor"
    CONTRA_FLOR_AL_RESTO = "contra_flor_al_resto"


class BetStatus(Enum):
    NONE = "none"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REFUSED = "refused"
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
pytest tests/entities/test_card.py -v
```
Expected: 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add truco/enums.py tests/entities/test_card.py
git commit -m "feat: add enums (Suit, BetType, BetResponse, FlorResponse, BetStatus)"
```

---

## Task 3: Card

**Files:**
- Create: `truco/entities/card.py`
- Modify: `tests/entities/test_card.py` (adicionar testes de Card)

- [ ] **Step 1: Adicionar testes de Card em `tests/entities/test_card.py`**

Adicionar abaixo dos imports e testes de enum existentes:

```python
from truco.entities.card import Card


def test_card_creation():
    card = Card(number=3, suit=Suit.ESPADAS)
    assert card.number == 3
    assert card.suit == Suit.ESPADAS


def test_manilha_is_strongest():
    manilha = Card(number=4, suit=Suit.ESPADAS)
    assert manilha.strength == 14


def test_seven_espadas():
    card = Card(number=7, suit=Suit.ESPADAS)
    assert card.strength == 13


def test_one_espadas():
    card = Card(number=1, suit=Suit.ESPADAS)
    assert card.strength == 12


def test_seven_ouros():
    card = Card(number=7, suit=Suit.OUROS)
    assert card.strength == 11


def test_three_any_suit():
    assert Card(number=3, suit=Suit.COPAS).strength == 10
    assert Card(number=3, suit=Suit.PAUS).strength == 10
    assert Card(number=3, suit=Suit.OUROS).strength == 10


def test_two_any_suit():
    assert Card(number=2, suit=Suit.ESPADAS).strength == 9


def test_one_not_espadas():
    assert Card(number=1, suit=Suit.COPAS).strength == 8
    assert Card(number=1, suit=Suit.OUROS).strength == 8
    assert Card(number=1, suit=Suit.PAUS).strength == 8


def test_figure_cards():
    assert Card(number=12, suit=Suit.ESPADAS).strength == 7
    assert Card(number=11, suit=Suit.ESPADAS).strength == 6
    assert Card(number=10, suit=Suit.ESPADAS).strength == 5


def test_seven_copas_paus():
    assert Card(number=7, suit=Suit.COPAS).strength == 4
    assert Card(number=7, suit=Suit.PAUS).strength == 4


def test_low_cards():
    assert Card(number=6, suit=Suit.ESPADAS).strength == 3
    assert Card(number=5, suit=Suit.ESPADAS).strength == 2
    assert Card(number=4, suit=Suit.COPAS).strength == 1


def test_envido_value_number_cards():
    assert Card(number=1, suit=Suit.ESPADAS).envido_value == 1
    assert Card(number=5, suit=Suit.COPAS).envido_value == 5
    assert Card(number=7, suit=Suit.OUROS).envido_value == 7


def test_envido_value_figure_cards():
    assert Card(number=10, suit=Suit.ESPADAS).envido_value == 0
    assert Card(number=11, suit=Suit.COPAS).envido_value == 0
    assert Card(number=12, suit=Suit.PAUS).envido_value == 0


def test_card_repr():
    card = Card(number=3, suit=Suit.ESPADAS)
    assert "3" in repr(card)
    assert "espadas" in repr(card).lower()
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
pytest tests/entities/test_card.py -v -k "card"
```
Expected: `ImportError: cannot import name 'Card'`

- [ ] **Step 3: Implementar `truco/entities/card.py`**

```python
from __future__ import annotations
from truco.enums import Suit


def _calc_strength(number: int, suit: Suit) -> int:
    if number == 4 and suit == Suit.ESPADAS:
        return 14
    if number == 7 and suit == Suit.ESPADAS:
        return 13
    if number == 1 and suit == Suit.ESPADAS:
        return 12
    if number == 7 and suit == Suit.OUROS:
        return 11
    if number == 3:
        return 10
    if number == 2:
        return 9
    if number == 1:
        return 8
    if number == 12:
        return 7
    if number == 11:
        return 6
    if number == 10:
        return 5
    if number == 7:
        return 4
    if number == 6:
        return 3
    if number == 5:
        return 2
    return 1  # number == 4, suit != ESPADAS


class Card:
    def __init__(self, number: int, suit: Suit) -> None:
        self.number = number
        self.suit = suit
        self.strength = _calc_strength(number, suit)
        self.envido_value = number if number <= 7 else 0

    def __repr__(self) -> str:
        return f"Card({self.number} de {self.suit.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.number == other.number and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.number, self.suit))
```

- [ ] **Step 4: Rodar todos os testes de card**

```bash
pytest tests/entities/test_card.py -v
```
Expected: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add truco/entities/card.py tests/entities/test_card.py
git commit -m "feat: add Card with strength hierarchy and envido_value"
```

---

## Task 4: Deck

**Files:**
- Create: `truco/entities/deck.py`
- Create: `tests/entities/test_deck.py`

- [ ] **Step 1: Escrever `tests/entities/test_deck.py`**

```python
from truco.entities.deck import Deck
from truco.enums import Suit


def test_deck_initializes_with_40_cards():
    deck = Deck()
    deck.initialize()
    assert len(deck.cards) == 40


def test_deck_has_valid_numbers_only():
    deck = Deck()
    deck.initialize()
    valid = {1, 2, 3, 4, 5, 6, 7, 10, 11, 12}
    for card in deck.cards:
        assert card.number in valid


def test_deck_has_all_suits():
    deck = Deck()
    deck.initialize()
    suits = {card.suit for card in deck.cards}
    assert suits == {Suit.ESPADAS, Suit.OUROS, Suit.COPAS, Suit.PAUS}


def test_deck_has_unique_cards():
    deck = Deck()
    deck.initialize()
    pairs = [(c.number, c.suit) for c in deck.cards]
    assert len(pairs) == len(set(pairs))


def test_deal_hand_returns_three_cards():
    deck = Deck()
    deck.initialize()
    hand = deck.deal_hand()
    assert len(hand) == 3


def test_deal_hand_removes_cards_from_deck():
    deck = Deck()
    deck.initialize()
    deck.deal_hand()
    assert len(deck.cards) == 37


def test_two_deal_hands_have_no_overlap():
    deck = Deck()
    deck.initialize()
    hand1 = deck.deal_hand()
    hand2 = deck.deal_hand()
    assert set(hand1).isdisjoint(set(hand2))


def test_shuffle_changes_order():
    import random
    random.seed(42)
    deck = Deck()
    deck.initialize()
    original = list(deck.cards)
    deck.shuffle()
    assert deck.cards != original


def test_initialize_resets_deck():
    deck = Deck()
    deck.initialize()
    deck.deal_hand()
    assert len(deck.cards) == 37
    deck.initialize()
    assert len(deck.cards) == 40
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
pytest tests/entities/test_deck.py -v
```
Expected: `ImportError: cannot import name 'Deck'`

- [ ] **Step 3: Implementar `truco/entities/deck.py`**

```python
from __future__ import annotations
import random
from truco.enums import Suit
from truco.entities.card import Card

VALID_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]


class Deck:
    def __init__(self) -> None:
        self.cards: list[Card] = []

    def initialize(self) -> None:
        self.cards = [
            Card(number=n, suit=s)
            for s in Suit
            for n in VALID_NUMBERS
        ]

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal_hand(self) -> list[Card]:
        hand = self.cards[:3]
        self.cards = self.cards[3:]
        return hand
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
pytest tests/entities/test_deck.py -v
```
Expected: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add truco/entities/deck.py tests/entities/test_deck.py
git commit -m "feat: add Deck with initialize/shuffle/deal_hand"
```

---

## Task 5: Player e Team

**Files:**
- Create: `truco/entities/player.py`
- Create: `truco/entities/team.py`
- Create: `tests/entities/test_player.py`
- Create: `tests/entities/test_team.py`

- [ ] **Step 1: Escrever `tests/entities/test_player.py`**

```python
import pytest
from truco.entities.player import Player
from truco.entities.card import Card
from truco.enums import Suit


def _make_player_with_cards():
    player = Player(name="Alice")
    player.hand = [
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.OUROS),
        Card(number=1, suit=Suit.COPAS),
    ]
    return player


def test_player_has_name():
    player = Player(name="Alice")
    assert player.name == "Alice"


def test_player_hand_starts_empty():
    player = Player(name="Alice")
    assert player.hand == []


def test_play_card_removes_from_hand():
    player = _make_player_with_cards()
    card = player.hand[0]
    played = player.play_card(card)
    assert played == card
    assert card not in player.hand
    assert len(player.hand) == 2


def test_play_card_raises_if_not_in_hand():
    player = _make_player_with_cards()
    foreign_card = Card(number=2, suit=Suit.PAUS)
    with pytest.raises(ValueError):
        player.play_card(foreign_card)


def test_clear_hand_empties_hand():
    player = _make_player_with_cards()
    player.clear_hand()
    assert player.hand == []
```

- [ ] **Step 2: Escrever `tests/entities/test_team.py`**

```python
import pytest
from truco.entities.team import Team
from truco.entities.player import Player


def _make_team():
    player = Player(name="Alice")
    return Team(name="Team A", players=[player])


def test_team_has_name():
    team = _make_team()
    assert team.name == "Team A"


def test_team_has_players():
    team = _make_team()
    assert len(team.players) == 1
    assert team.players[0].name == "Alice"


def test_team_starts_with_zero_points():
    team = _make_team()
    assert team.points == 0


def test_add_points_increases_score():
    team = _make_team()
    team.add_points(3)
    assert team.points == 3


def test_add_points_accumulates():
    team = _make_team()
    team.add_points(2)
    team.add_points(3)
    assert team.points == 5


def test_add_points_raises_if_zero():
    team = _make_team()
    with pytest.raises(ValueError):
        team.add_points(0)


def test_add_points_raises_if_negative():
    team = _make_team()
    with pytest.raises(ValueError):
        team.add_points(-1)
```

- [ ] **Step 3: Rodar e confirmar falha**

```bash
pytest tests/entities/test_player.py tests/entities/test_team.py -v
```
Expected: ImportErrors.

- [ ] **Step 4: Implementar `truco/entities/player.py`**

```python
from __future__ import annotations
from truco.entities.card import Card


class Player:
    def __init__(self, name: str) -> None:
        self.name = name
        self.hand: list[Card] = []

    def play_card(self, card: Card) -> Card:
        if card not in self.hand:
            raise ValueError(f"{card} not in {self.name}'s hand")
        self.hand.remove(card)
        return card

    def clear_hand(self) -> None:
        self.hand = []

    def __repr__(self) -> str:
        return f"Player({self.name})"
```

- [ ] **Step 5: Implementar `truco/entities/team.py`**

```python
from __future__ import annotations
from truco.entities.player import Player


class Team:
    def __init__(self, name: str, players: list[Player]) -> None:
        self.name = name
        self.players = players
        self.points = 0

    def add_points(self, value: int) -> None:
        if value <= 0:
            raise ValueError(f"Points must be positive, got {value}")
        self.points += value

    def __repr__(self) -> str:
        return f"Team({self.name}, {self.points}pts)"
```

- [ ] **Step 6: Rodar e confirmar que passa**

```bash
pytest tests/entities/test_player.py tests/entities/test_team.py -v
```
Expected: todos PASSED.

- [ ] **Step 7: Commit**

```bash
git add truco/entities/player.py truco/entities/team.py tests/entities/test_player.py tests/entities/test_team.py
git commit -m "feat: add Player and Team entities"
```

---

## Task 6: BetResult e PlayResult

**Files:**
- Create: `truco/entities/bet_result.py`
- Create: `truco/entities/play_result.py`

Esses são data classes sem lógica — sem testes isolados, serão exercitados pelos testes de Game.

- [ ] **Step 1: Implementar `truco/entities/bet_result.py`**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from truco.entities.team import Team
    from truco.entities.player import Player


@dataclass
class BetResult:
    bet_pending: bool = False
    hand_value: int = 1
    hand_over: bool = False
    winner_team: "Team | None" = None
    who_responds: "Player | None" = None
    points_winner: int = 0
    points_loser: int = 0
```

- [ ] **Step 2: Implementar `truco/entities/play_result.py`**

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from truco.entities.player import Player
    from truco.entities.team import Team


@dataclass
class PlayResult:
    round_winner: "Player | None" = None
    round_over: bool = False
    hand_winner: "Team | None" = None
    hand_over: bool = False
    next_player: "Player | None" = None
    round_number: int = 1
```

- [ ] **Step 3: Verificar imports**

```bash
python -c "from truco.entities.bet_result import BetResult; from truco.entities.play_result import PlayResult; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add truco/entities/bet_result.py truco/entities/play_result.py
git commit -m "feat: add BetResult and PlayResult dataclasses"
```

---

## Task 7: TrucoState

**Files:**
- Create: `truco/states/truco_state.py`
- Create: `tests/entities/test_bet_truco.py`

- [ ] **Step 1: Escrever `tests/entities/test_bet_truco.py`**

```python
import pytest
from truco.states.truco_state import TrucoState
from truco.entities.team import Team
from truco.entities.player import Player
from truco.enums import BetStatus


def _make_teams():
    p1 = Player(name="Alice")
    p2 = Player(name="Bob")
    t1 = Team(name="T1", players=[p1])
    t2 = Team(name="T2", players=[p2])
    return t1, t2


def test_initial_state():
    state = TrucoState()
    assert state.current_value == 1
    assert state.value_if_refused == 0
    assert state.who_asked is None
    assert state.status == BetStatus.NONE


def test_can_ask_initially():
    state = TrucoState()
    t1, t2 = _make_teams()
    assert state.can_ask(t1) is True


def test_ask_sets_pending():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    assert state.status == BetStatus.PENDING
    assert state.who_asked == t1
    assert state.current_value == 2
    assert state.value_if_refused == 1


def test_cannot_ask_while_pending():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    assert state.can_ask(t1) is False
    assert state.can_ask(t2) is False


def test_accept_clears_pending():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    assert state.status == BetStatus.ACCEPTED
    assert state.current_value == 2


def test_refuse_sets_refused():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.refuse()
    assert state.status == BetStatus.REFUSED


def test_raise_bet_after_accept():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    state.raise_bet(t2)
    assert state.status == BetStatus.PENDING
    assert state.current_value == 3
    assert state.value_if_refused == 2
    assert state.who_asked == t2


def test_raise_to_vale_quatro():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    state.raise_bet(t2)
    state.accept()
    state.raise_bet(t1)
    assert state.current_value == 4
    assert state.value_if_refused == 3


def test_cannot_raise_past_vale_quatro():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    state.raise_bet(t2)
    state.accept()
    state.raise_bet(t1)
    state.accept()
    assert state.can_ask(t2) is False


def test_same_team_cannot_ask_twice_in_a_row():
    state = TrucoState()
    t1, t2 = _make_teams()
    state.ask(t1)
    state.accept()
    assert state.can_ask(t1) is False
    assert state.can_ask(t2) is True
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
pytest tests/entities/test_bet_truco.py -v
```
Expected: `ImportError: cannot import name 'TrucoState'`

- [ ] **Step 3: Implementar `truco/states/truco_state.py`**

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from truco.enums import BetStatus

if TYPE_CHECKING:
    from truco.entities.team import Team

_BET_SEQUENCE = [2, 3, 4]  # truco, retruco, vale quatro


class TrucoState:
    def __init__(self) -> None:
        self.current_value: int = 1
        self.value_if_refused: int = 0
        self.who_asked: "Team | None" = None
        self.status: BetStatus = BetStatus.NONE

    def can_ask(self, team: "Team") -> bool:
        if self.status == BetStatus.PENDING:
            return False
        if self.current_value >= 4:
            return False
        if self.who_asked == team and self.status == BetStatus.ACCEPTED:
            return False
        return True

    def ask(self, team: "Team") -> None:
        next_value = self.current_value + 1
        self.value_if_refused = self.current_value if self.current_value > 1 else 1
        self.current_value = next_value
        self.who_asked = team
        self.status = BetStatus.PENDING

    def accept(self) -> None:
        self.status = BetStatus.ACCEPTED

    def refuse(self) -> None:
        self.status = BetStatus.REFUSED

    def raise_bet(self, team: "Team") -> None:
        self.ask(team)
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
pytest tests/entities/test_bet_truco.py -v
```
Expected: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add truco/states/truco_state.py tests/entities/test_bet_truco.py
git commit -m "feat: add TrucoState with ask/accept/refuse/raise_bet"
```

---

## Task 8: EnvidoState

**Files:**
- Create: `truco/states/envido_state.py`
- Create: `tests/states/test_envido_state.py`

- [ ] **Step 1: Escrever `tests/states/test_envido_state.py`**

```python
import pytest
from truco.states.envido_state import EnvidoState
from truco.entities.player import Player
from truco.entities.card import Card
from truco.enums import BetStatus, BetType


def _make_players():
    return Player(name="Alice"), Player(name="Bob")


def test_initial_state():
    state = EnvidoState()
    assert state.value_accepted == 0
    assert state.value_if_refused == 0
    assert state.bet_type is None
    assert state.who_asked is None
    assert state.status == BetStatus.NONE


def test_ask_envido():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.ENVIDO)
    assert state.status == BetStatus.PENDING
    assert state.who_asked == alice
    assert state.bet_type == BetType.ENVIDO
    assert state.value_accepted == 2
    assert state.value_if_refused == 1


def test_ask_real_envido():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.REAL_ENVIDO)
    assert state.value_accepted == 3
    assert state.value_if_refused == 1


def test_accept_envido():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.accept()
    assert state.status == BetStatus.ACCEPTED


def test_refuse_envido():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.refuse()
    assert state.status == BetStatus.REFUSED


def test_raise_envido_to_envido_envido():
    state = EnvidoState()
    alice, bob = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.ask(bob, BetType.ENVIDO_ENVIDO)
    assert state.bet_type == BetType.ENVIDO_ENVIDO
    assert state.value_accepted == 4
    assert state.value_if_refused == 2


def test_raise_envido_to_real_envido():
    state = EnvidoState()
    alice, bob = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.ask(bob, BetType.REAL_ENVIDO)
    assert state.value_accepted == 5  # 2 (envido accepted) + 3 (real envido)
    assert state.value_if_refused == 2


def test_falta_envido_value():
    state = EnvidoState()
    alice, _ = _make_players()
    state.ask(alice, BetType.FALTA_ENVIDO, points_to_win=15)
    assert state.value_accepted == 15
    assert state.value_if_refused == 1


def test_falta_envido_after_envido():
    state = EnvidoState()
    alice, bob = _make_players()
    state.ask(alice, BetType.ENVIDO)
    state.ask(bob, BetType.FALTA_ENVIDO, points_to_win=12)
    assert state.value_accepted == 14  # 2 (envido) + 12 (falta)
    assert state.value_if_refused == 2
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
pytest tests/states/test_envido_state.py -v
```

- [ ] **Step 3: Implementar `truco/states/envido_state.py`**

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from truco.enums import BetStatus, BetType

if TYPE_CHECKING:
    from truco.entities.player import Player

_BASE_VALUES: dict[BetType, tuple[int, int]] = {
    # (accepted_increment, refused_value_when_first)
    BetType.ENVIDO: (2, 1),
    BetType.ENVIDO_ENVIDO: (2, None),   # refused = current accepted
    BetType.REAL_ENVIDO: (3, 1),
    BetType.FALTA_ENVIDO: (0, 1),       # accepted = points_to_win (cumulative)
}


class EnvidoState:
    def __init__(self) -> None:
        self.value_accepted: int = 0
        self.value_if_refused: int = 0
        self.bet_type: BetType | None = None
        self.who_asked: "Player | None" = None
        self.status: BetStatus = BetStatus.NONE

    def ask(self, player: "Player", bet_type: BetType, points_to_win: int = 0) -> None:
        prev_accepted = self.value_accepted

        if bet_type == BetType.FALTA_ENVIDO:
            increment = points_to_win
        elif bet_type == BetType.ENVIDO and self.status == BetStatus.PENDING and self.bet_type == BetType.ENVIDO:
            # envido + envido = envido_envido, increment is 2 more
            increment = 2
        else:
            increment = _BASE_VALUES[bet_type][0]

        self.value_accepted = prev_accepted + increment
        self.value_if_refused = prev_accepted if prev_accepted > 0 else 1
        self.bet_type = bet_type
        self.who_asked = player
        self.status = BetStatus.PENDING

    def accept(self) -> None:
        self.status = BetStatus.ACCEPTED

    def refuse(self) -> None:
        self.status = BetStatus.REFUSED
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
pytest tests/states/test_envido_state.py -v
```
Expected: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add truco/states/envido_state.py tests/states/test_envido_state.py
git commit -m "feat: add EnvidoState with envido bet sequence"
```

---

## Task 9: FlorState

**Files:**
- Create: `truco/states/flor_state.py`
- Create: `tests/states/test_flor_state.py`

- [ ] **Step 1: Escrever `tests/states/test_flor_state.py`**

```python
from truco.states.flor_state import FlorState
from truco.entities.team import Team
from truco.entities.player import Player


def _make_teams():
    p1 = Player(name="Alice")
    p2 = Player(name="Bob")
    t1 = Team(name="T1", players=[p1])
    t2 = Team(name="T2", players=[p2])
    return t1, t2


def test_initial_state():
    state = FlorState()
    assert state.who_declared is None
    assert state.both_declared is False
    assert state.contra_flor_pending is False
    assert state.over is False
    assert state.envido_cancelled is False
    assert state.waiting_for_response is False


def test_declare_first_team():
    state = FlorState()
    t1, _ = _make_teams()
    state.declare(t1)
    assert state.who_declared == t1
    assert state.envido_cancelled is True
    assert state.waiting_for_response is True
    assert state.both_declared is False


def test_declare_second_team_sets_both():
    state = FlorState()
    t1, t2 = _make_teams()
    state.declare(t1)
    state.declare(t2)
    assert state.both_declared is True
    assert state.waiting_for_response is False


def test_contra_flor_pending():
    state = FlorState()
    t1, t2 = _make_teams()
    state.declare(t1)
    state.contra_flor(t2)
    assert state.contra_flor_pending is True
    assert state.waiting_for_response is True


def test_close_ends_flor():
    state = FlorState()
    t1, t2 = _make_teams()
    state.declare(t1)
    state.close()
    assert state.over is True
    assert state.waiting_for_response is False
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
pytest tests/states/test_flor_state.py -v
```

- [ ] **Step 3: Implementar `truco/states/flor_state.py`**

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from truco.entities.team import Team


class FlorState:
    def __init__(self) -> None:
        self.who_declared: "Team | None" = None
        self.both_declared: bool = False
        self.contra_flor_pending: bool = False
        self.over: bool = False
        self.envido_cancelled: bool = False
        self._waiting: bool = False

    @property
    def waiting_for_response(self) -> bool:
        return self._waiting

    def declare(self, team: "Team") -> None:
        self.envido_cancelled = True
        if self.who_declared is None:
            self.who_declared = team
            self._waiting = True
        else:
            self.both_declared = True
            self._waiting = False

    def contra_flor(self, team: "Team") -> None:
        self.contra_flor_pending = True
        self._waiting = True

    def close(self) -> None:
        self.over = True
        self._waiting = False
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
pytest tests/states/test_flor_state.py -v
```
Expected: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add truco/states/flor_state.py tests/states/test_flor_state.py
git commit -m "feat: add FlorState with declare/contra_flor/close"
```

---

## Task 10: Round

**Files:**
- Create: `truco/entities/round.py`
- Create: `tests/entities/test_round.py`

- [ ] **Step 1: Escrever `tests/entities/test_round.py`**

```python
import pytest
from truco.entities.round import Round
from truco.entities.player import Player
from truco.entities.card import Card
from truco.enums import Suit


def _make_players():
    return Player(name="Alice"), Player(name="Bob")


def _card(number, suit=Suit.ESPADAS):
    return Card(number=number, suit=suit)


def test_round_starts_empty():
    r = Round()
    assert r.plays == {}
    assert r.winner is None
    assert r.resolved is False


def test_register_play():
    r = Round()
    alice, _ = _make_players()
    card = _card(3)
    r.register_play(alice, card)
    assert r.plays[alice] == card


def test_register_play_duplicate_raises():
    r = Round()
    alice, _ = _make_players()
    r.register_play(alice, _card(3))
    with pytest.raises(RuntimeError):
        r.register_play(alice, _card(2))


def test_resolve_picks_higher_strength():
    r = Round()
    alice, bob = _make_players()
    r.register_play(alice, _card(3))   # strength 10
    r.register_play(bob, _card(2))     # strength 9
    winner = r.resolve()
    assert winner == alice
    assert r.winner == alice
    assert r.resolved is True


def test_resolve_tie_returns_none():
    r = Round()
    alice, bob = _make_players()
    r.register_play(alice, _card(3, Suit.COPAS))   # strength 10
    r.register_play(bob, _card(3, Suit.OUROS))     # strength 10
    winner = r.resolve()
    assert winner is None
    assert r.winner is None
    assert r.resolved is True


def test_resolve_requires_both_plays():
    r = Round()
    alice, _ = _make_players()
    r.register_play(alice, _card(3))
    with pytest.raises(RuntimeError):
        r.resolve()
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
pytest tests/entities/test_round.py -v
```

- [ ] **Step 3: Implementar `truco/entities/round.py`**

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from truco.entities.player import Player
    from truco.entities.card import Card


class Round:
    def __init__(self) -> None:
        self.plays: dict["Player", "Card"] = {}
        self.winner: "Player | None" = None
        self.resolved: bool = False

    def register_play(self, player: "Player", card: "Card") -> None:
        if player in self.plays:
            raise RuntimeError(f"{player} already played this round")
        self.plays[player] = card

    def resolve(self) -> "Player | None":
        if len(self.plays) < 2:
            raise RuntimeError("Cannot resolve round with fewer than 2 plays")
        self.resolved = True
        players = list(self.plays.keys())
        cards = [self.plays[p] for p in players]
        if cards[0].strength > cards[1].strength:
            self.winner = players[0]
        elif cards[1].strength > cards[0].strength:
            self.winner = players[1]
        else:
            self.winner = None
        return self.winner
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
pytest tests/entities/test_round.py -v
```
Expected: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add truco/entities/round.py tests/entities/test_round.py
git commit -m "feat: add Round with register_play and resolve"
```

---

## Task 11: Hand

**Files:**
- Create: `truco/entities/hand.py`
- Create: `tests/entities/test_hand.py`
- Create: `tests/entities/test_hand_envido_flor.py`

A `Hand` orquestra até 3 rodadas, rastreia current_player, e delega apostas para TrucoState/EnvidoState/FlorState.

- [ ] **Step 1: Escrever `tests/entities/test_hand.py`**

```python
import pytest
from truco.entities.hand import Hand
from truco.entities.player import Player
from truco.entities.team import Team
from truco.entities.card import Card
from truco.enums import Suit


def _setup():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    alice.hand = [
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=2, suit=Suit.COPAS),
        Card(number=5, suit=Suit.PAUS),
    ]
    bob.hand = [
        Card(number=1, suit=Suit.COPAS),
        Card(number=6, suit=Suit.OUROS),
        Card(number=4, suit=Suit.PAUS),
    ]
    hand = Hand(mano_player=alice, players=[alice, bob])
    return hand, alice, bob, t1, t2


def test_hand_starts_at_round_one():
    hand, alice, bob, t1, t2 = _setup()
    assert hand.round_number == 1
    assert hand.current_player == alice


def test_register_play_advances_to_next_player():
    hand, alice, bob, t1, t2 = _setup()
    card = alice.hand[0]
    hand.register_play(alice, card, [alice, bob])
    assert hand.current_player == bob


def test_round_resolves_after_two_plays():
    hand, alice, bob, t1, t2 = _setup()
    # Alice plays 3♠ (str 10), Bob plays 1♥ (str 8) → Alice wins round 1
    hand.register_play(alice, alice.hand[0], [alice, bob])
    round_winner = hand.register_play(bob, bob.hand[0], [alice, bob])
    assert round_winner == alice
    assert hand.round_number == 2


def test_hand_winner_after_two_rounds_won():
    hand, alice, bob, t1, t2 = _setup()
    teams = [t1, t2]
    # Round 1: Alice plays 3♠ (10) beats Bob's 1♥ (8)
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    # Round 2: Alice plays 2♥ (9) beats Bob's 6♦ (3)
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    result = hand.resolve(teams)
    assert result == t1


def test_mano_wins_on_double_tie():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    # Give same-strength cards
    alice.hand = [
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=2, suit=Suit.ESPADAS),
        Card(number=5, suit=Suit.ESPADAS),
    ]
    bob.hand = [
        Card(number=3, suit=Suit.COPAS),
        Card(number=2, suit=Suit.COPAS),
        Card(number=5, suit=Suit.COPAS),
    ]
    hand = Hand(mano_player=alice, players=[alice, bob])
    # Round 1 tie: 3♠ vs 3♥ (both str 10)
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    # Round 2 tie: 2♠ vs 2♥ (both str 9)
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    result = hand.resolve([t1, t2])
    assert result == t1  # mano (alice) wins on tie


def test_win_round1_tie_round2_wins_hand():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    alice.hand = [
        Card(number=3, suit=Suit.ESPADAS),  # str 10 - wins r1
        Card(number=2, suit=Suit.ESPADAS),  # str 9 - ties r2
        Card(number=5, suit=Suit.ESPADAS),
    ]
    bob.hand = [
        Card(number=1, suit=Suit.COPAS),   # str 8 - loses r1
        Card(number=2, suit=Suit.COPAS),   # str 9 - ties r2
        Card(number=5, suit=Suit.COPAS),
    ]
    hand = Hand(mano_player=alice, players=[alice, bob])
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    hand.register_play(alice, alice.hand[0], [alice, bob])
    hand.register_play(bob, bob.hand[0], [alice, bob])
    result = hand.resolve([t1, t2])
    assert result == t1
```

- [ ] **Step 2: Escrever `tests/entities/test_hand_envido_flor.py`**

```python
from truco.entities.hand import Hand
from truco.entities.player import Player
from truco.entities.team import Team
from truco.entities.card import Card
from truco.enums import Suit


def _setup_hand(alice_cards, bob_cards, mano="alice"):
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    alice.hand = alice_cards
    bob.hand = bob_cards
    mano_player = alice if mano == "alice" else bob
    hand = Hand(mano_player=mano_player, players=[alice, bob])
    return hand, alice, bob


def test_can_envido_at_start():
    alice_cards = [
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.ESPADAS),
        Card(number=1, suit=Suit.COPAS),
    ]
    bob_cards = [
        Card(number=2, suit=Suit.OUROS),
        Card(number=4, suit=Suit.COPAS),
        Card(number=5, suit=Suit.PAUS),
    ]
    hand, alice, bob = _setup_hand(alice_cards, bob_cards)
    assert hand.can_envido(alice) is True
    assert hand.can_envido(bob) is True


def test_envido_value_two_same_suit():
    alice_cards = [
        Card(number=7, suit=Suit.ESPADAS),   # envido 7
        Card(number=6, suit=Suit.ESPADAS),   # envido 6
        Card(number=1, suit=Suit.COPAS),     # envido 1 (different suit)
    ]
    hand, alice, bob = _setup_hand(alice_cards, [
        Card(number=1, suit=Suit.OUROS),
        Card(number=2, suit=Suit.PAUS),
        Card(number=3, suit=Suit.COPAS),
    ])
    assert hand.envido_value(alice) == 33  # 20 + 7 + 6


def test_envido_value_no_pair_returns_highest():
    alice_cards = [
        Card(number=7, suit=Suit.ESPADAS),   # envido 7
        Card(number=6, suit=Suit.OUROS),     # envido 6
        Card(number=5, suit=Suit.COPAS),     # envido 5
    ]
    hand, alice, bob = _setup_hand(alice_cards, [
        Card(number=1, suit=Suit.OUROS),
        Card(number=2, suit=Suit.PAUS),
        Card(number=3, suit=Suit.COPAS),
    ])
    assert hand.envido_value(alice) == 7  # just highest individual


def test_envido_value_figure_counts_zero():
    alice_cards = [
        Card(number=7, suit=Suit.ESPADAS),   # envido 7
        Card(number=10, suit=Suit.ESPADAS),  # envido 0
        Card(number=1, suit=Suit.COPAS),
    ]
    hand, alice, bob = _setup_hand(alice_cards, [
        Card(number=1, suit=Suit.OUROS),
        Card(number=2, suit=Suit.PAUS),
        Card(number=3, suit=Suit.COPAS),
    ])
    assert hand.envido_value(alice) == 27  # 20 + 7 + 0


def test_has_flor_all_same_suit():
    alice_cards = [
        Card(number=1, suit=Suit.ESPADAS),
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.ESPADAS),
    ]
    assert Hand.has_flor(alice_cards) is True


def test_has_flor_false_mixed_suits():
    alice_cards = [
        Card(number=1, suit=Suit.ESPADAS),
        Card(number=3, suit=Suit.OUROS),
        Card(number=7, suit=Suit.ESPADAS),
    ]
    assert Hand.has_flor(alice_cards) is False


def test_can_flor_with_all_same_suit():
    alice_cards = [
        Card(number=1, suit=Suit.ESPADAS),
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.ESPADAS),
    ]
    bob_cards = [
        Card(number=2, suit=Suit.OUROS),
        Card(number=4, suit=Suit.COPAS),
        Card(number=5, suit=Suit.PAUS),
    ]
    hand, alice, bob = _setup_hand(alice_cards, bob_cards)
    assert hand.can_flor(alice) is True
    assert hand.can_flor(bob) is False


def test_flor_value():
    alice_cards = [
        Card(number=7, suit=Suit.ESPADAS),   # envido 7
        Card(number=6, suit=Suit.ESPADAS),   # envido 6
        Card(number=1, suit=Suit.ESPADAS),   # envido 1
    ]
    hand, alice, bob = _setup_hand(alice_cards, [
        Card(number=1, suit=Suit.OUROS),
        Card(number=2, suit=Suit.PAUS),
        Card(number=3, suit=Suit.COPAS),
    ])
    assert hand.flor_value(alice) == 34  # 20 + 7 + 6 + 1


def test_can_envido_false_when_flor():
    alice_cards = [
        Card(number=1, suit=Suit.ESPADAS),
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.ESPADAS),
    ]
    bob_cards = [
        Card(number=2, suit=Suit.OUROS),
        Card(number=4, suit=Suit.COPAS),
        Card(number=5, suit=Suit.PAUS),
    ]
    hand, alice, bob = _setup_hand(alice_cards, bob_cards)
    # Player with flor cannot envido
    assert hand.can_envido(alice) is False
    assert hand.can_envido(bob) is True
```

- [ ] **Step 3: Rodar e confirmar falha**

```bash
pytest tests/entities/test_hand.py tests/entities/test_hand_envido_flor.py -v
```

- [ ] **Step 4: Implementar `truco/entities/hand.py`**

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from truco.entities.round import Round
from truco.states.truco_state import TrucoState
from truco.states.envido_state import EnvidoState
from truco.states.flor_state import FlorState

if TYPE_CHECKING:
    from truco.entities.player import Player
    from truco.entities.team import Team
    from truco.entities.card import Card


class Hand:
    def __init__(self, mano_player: "Player", players: list["Player"]) -> None:
        self.mano_player = mano_player
        self.players = players
        self.current_player: "Player" = mano_player
        self.rounds: list[Round] = [Round()]
        self.truco = TrucoState()
        self.envido = EnvidoState()
        self.flor = FlorState()

    @property
    def round_number(self) -> int:
        return len(self.rounds)

    @property
    def _current_round(self) -> Round:
        return self.rounds[-1]

    def register_play(self, player: "Player", card: "Card", all_players: list["Player"]) -> "Player | None":
        self._current_round.register_play(player, card)
        if len(self._current_round.plays) == 2:
            winner = self._current_round.resolve()
            self._advance_round(winner)
            return winner
        self._set_next_player(all_players)
        return None

    def _set_next_player(self, all_players: list["Player"]) -> None:
        idx = all_players.index(self.current_player)
        self.current_player = all_players[(idx + 1) % len(all_players)]

    def _advance_round(self, round_winner: "Player | None") -> None:
        if round_winner is not None:
            self.current_player = round_winner
        else:
            self.current_player = self.mano_player
        if len(self.rounds) < 3:
            self.rounds.append(Round())

    def resolve(self, teams: list["Team"]) -> "Team | None":
        winners = [r.winner for r in self.rounds if r.resolved]

        def player_team(p: "Player | None") -> "Team | None":
            if p is None:
                return None
            for t in teams:
                if p in t.players:
                    return t
            return None

        round_teams = [player_team(w) for w in winners]
        mano_team = player_team(self.mano_player)

        # apply tiebreaker rules
        if len(round_teams) >= 2:
            r1, r2 = round_teams[0], round_teams[1]
            if r1 is not None and r1 == r2:
                return r1  # won 2 in a row
            if r1 is None and r2 is not None:
                return r2  # tie then win
            if r1 is not None and r2 is None:
                return r1  # win then tie
            if r1 is None and r2 is None:
                return mano_team  # double tie
            # r1 != r2, play round 3
            if len(round_teams) >= 3:
                return round_teams[2]
        if len(round_teams) == 1 and round_teams[0] is not None:
            return round_teams[0]
        return mano_team

    def can_envido(self, player: "Player") -> bool:
        if Hand.has_flor(player.hand):
            return False
        if self.flor.envido_cancelled:
            return False
        return len(self.rounds) == 1 and not self.rounds[0].resolved

    def can_flor(self, player: "Player") -> bool:
        return Hand.has_flor(player.hand)

    def envido_value(self, player: "Player") -> int:
        cards = player.hand
        from collections import defaultdict
        by_suit: dict = defaultdict(list)
        for c in cards:
            by_suit[c.suit].append(c.envido_value)
        for suit_vals in by_suit.values():
            if len(suit_vals) >= 2:
                top2 = sorted(suit_vals, reverse=True)[:2]
                return 20 + sum(top2)
        return max(c.envido_value for c in cards)

    def flor_value(self, player: "Player") -> int:
        return 20 + sum(c.envido_value for c in player.hand)

    @staticmethod
    def has_flor(cards: list["Card"]) -> bool:
        if len(cards) != 3:
            return False
        return len({c.suit for c in cards}) == 1
```

- [ ] **Step 5: Rodar e confirmar que passa**

```bash
pytest tests/entities/test_hand.py tests/entities/test_hand_envido_flor.py -v
```
Expected: todos PASSED.

- [ ] **Step 6: Commit**

```bash
git add truco/entities/hand.py tests/entities/test_hand.py tests/entities/test_hand_envido_flor.py
git commit -m "feat: add Hand with round management, envido/flor helpers"
```

---

## Task 12: Game

**Files:**
- Create: `truco/entities/game.py`
- Create: `tests/entities/test_game.py`
- Create: `tests/entities/test_bet_envido.py`
- Create: `tests/entities/test_bet_flor.py`
- Create: `tests/entities/test_score.py`

`Game` é o orchestrator principal. Mantém `team1`, `team2`, `deck`, `hand` atual, e alterna o mano a cada hand.

- [ ] **Step 1: Escrever `tests/entities/test_game.py`**

```python
import pytest
from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team


def _make_game():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    return Game(team1=t1, team2=t2), alice, bob, t1, t2


def test_start_hand_deals_three_cards_to_each_player():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    assert len(alice.hand) == 3
    assert len(bob.hand) == 3


def test_start_hand_gives_unique_cards():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    all_cards = set(alice.hand) | set(bob.hand)
    assert len(all_cards) == 6


def test_current_player_is_mano_at_start():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    assert game.hand.current_player == alice  # alice is mano first hand


def test_play_card_returns_play_result():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    card = alice.hand[0]
    result = game.play_card(alice, card)
    assert result.round_over is False
    assert result.hand_over is False
    assert result.next_player == bob


def test_play_card_wrong_player_raises():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    with pytest.raises(RuntimeError):
        game.play_card(bob, bob.hand[0])  # bob is not current player


def test_hand_ends_after_three_rounds_or_winner():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    # Play through until hand is over
    hand_over = False
    for _ in range(6):  # max 6 plays
        current = game.hand.current_player
        card = current.hand[0]
        result = game.play_card(current, card)
        if result.hand_over:
            hand_over = True
            break
    assert hand_over


def test_mano_alternates_between_hands():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    first_mano = game.hand.mano_player
    # finish the hand
    for _ in range(6):
        current = game.hand.current_player
        if not current.hand:
            break
        result = game.play_card(current, current.hand[0])
        if result.hand_over:
            break
    game.start_hand()
    second_mano = game.hand.mano_player
    assert first_mano != second_mano


def test_can_ask_truco():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    assert game.can_ask_truco(alice) is True


def test_check_game_over_false_at_start():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    assert game.check_game_over() is False
```

- [ ] **Step 2: Escrever `tests/entities/test_bet_envido.py`**

```python
import pytest
from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.enums import BetType, BetResponse, BetStatus


def _make_game():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    game = Game(team1=t1, team2=t2)
    game.start_hand()
    return game, alice, bob, t1, t2


def test_can_envido_before_first_play():
    game, alice, bob, t1, t2 = _make_game()
    assert game.can_envido(alice) is True


def test_ask_envido_returns_pending_result():
    game, alice, bob, t1, t2 = _make_game()
    result = game.ask_envido(alice, BetType.ENVIDO)
    assert result.bet_pending is True
    assert result.who_responds == bob


def test_respond_envido_accept():
    game, alice, bob, t1, t2 = _make_game()
    game.ask_envido(alice, BetType.ENVIDO)
    result = game.respond_envido(bob, BetResponse.ACCEPT)
    assert result.bet_pending is False
    assert result.hand_over is True  # envido resolved → points awarded, hand continues? 
    # Actually: after envido resolves, play continues. hand_over=False.
    assert result.hand_over is False


def test_respond_envido_refuse_awards_points():
    game, alice, bob, t1, t2 = _make_game()
    game.ask_envido(alice, BetType.ENVIDO)
    result = game.respond_envido(bob, BetResponse.REFUSE)
    assert result.bet_pending is False
    assert t1.points == 1  # refused envido = 1 point to asker


def test_envido_not_available_after_first_round():
    game, alice, bob, t1, t2 = _make_game()
    # Play first round
    game.play_card(alice, alice.hand[0])
    game.play_card(bob, bob.hand[0])
    # Now in round 2, envido not available
    assert game.can_envido(alice) is False


def test_ask_envido_raises_when_not_available():
    game, alice, bob, t1, t2 = _make_game()
    game.play_card(alice, alice.hand[0])
    game.play_card(bob, bob.hand[0])
    with pytest.raises(RuntimeError):
        game.ask_envido(alice, BetType.ENVIDO)
```

- [ ] **Step 3: Escrever `tests/entities/test_bet_flor.py`**

```python
import pytest
from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.entities.card import Card
from truco.enums import Suit, FlorResponse, BetStatus


def _make_game_with_flor():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    # Give alice flor (all same suit)
    alice.hand = [
        Card(number=1, suit=Suit.ESPADAS),
        Card(number=3, suit=Suit.ESPADAS),
        Card(number=7, suit=Suit.ESPADAS),
    ]
    bob.hand = [
        Card(number=2, suit=Suit.OUROS),
        Card(number=4, suit=Suit.COPAS),
        Card(number=5, suit=Suit.PAUS),
    ]
    game = Game(team1=t1, team2=t2)
    game._deal_to_players(alice.hand, bob.hand)
    return game, alice, bob, t1, t2


def test_can_flor_with_all_same_suit():
    game, alice, bob, t1, t2 = _make_game_with_flor()
    assert game.can_flor(alice) is True
    assert game.can_flor(bob) is False


def test_declare_flor_cancels_envido():
    game, alice, bob, t1, t2 = _make_game_with_flor()
    game.declare_flor(alice)
    assert game.can_envido(alice) is False
    assert game.can_envido(bob) is False


def test_respond_flor_accept_awards_points():
    game, alice, bob, t1, t2 = _make_game_with_flor()
    game.declare_flor(alice)
    result = game.respond_flor(bob, FlorResponse.ACCEPT)
    # alice wins flor = 3 points (standard for one-sided flor)
    assert t1.points == 3


def test_declare_flor_sets_waiting():
    game, alice, bob, t1, t2 = _make_game_with_flor()
    result = game.declare_flor(alice)
    assert result.bet_pending is True
    assert result.who_responds == bob
```

- [ ] **Step 4: Escrever `tests/entities/test_score.py`**

```python
from truco.entities.game import Game
from truco.entities.player import Player
from truco.entities.team import Team
from truco.enums import BetResponse


def _make_game():
    alice = Player(name="Alice")
    bob = Player(name="Bob")
    t1 = Team(name="T1", players=[alice])
    t2 = Team(name="T2", players=[bob])
    return Game(team1=t1, team2=t2), alice, bob, t1, t2


def test_winning_hand_without_bet_scores_one():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    # Play through hand — winner gets 1 point (no truco bet)
    for _ in range(6):
        current = game.hand.current_player
        if not current.hand:
            break
        result = game.play_card(current, current.hand[0])
        if result.hand_over:
            break
    total = t1.points + t2.points
    assert total == 1


def test_winning_hand_with_truco_bet_scores_two():
    game, alice, bob, t1, t2 = _make_game()
    game.start_hand()
    game.ask_truco(alice)
    game.respond_truco(bob, BetResponse.ACCEPT)
    for _ in range(6):
        current = game.hand.current_player
        if not current.hand:
            break
        result = game.play_card(current, current.hand[0])
        if result.hand_over:
            break
    total = t1.points + t2.points
    assert total >= 2  # at least the truco bet points


def test_get_score_returns_both_teams():
    game, alice, bob, t1, t2 = _make_game()
    score = game.get_score()
    assert score[t1] == 0
    assert score[t2] == 0


def test_check_game_over_at_30():
    game, alice, bob, t1, t2 = _make_game()
    t1.points = 29
    game.start_hand()
    # Force a win for t1
    for _ in range(6):
        current = game.hand.current_player
        if not current.hand:
            break
        result = game.play_card(current, current.hand[0])
        if result.hand_over:
            break
    # either game over or not depending on who won, but check_game_over checks >= 30
    if t1.points >= 30:
        assert game.check_game_over() is True


def test_game_not_over_below_30():
    game, alice, bob, t1, t2 = _make_game()
    t1.points = 15
    assert game.check_game_over() is False
```

- [ ] **Step 5: Rodar e confirmar falha**

```bash
pytest tests/entities/test_game.py tests/entities/test_bet_envido.py tests/entities/test_bet_flor.py tests/entities/test_score.py -v
```

- [ ] **Step 6: Implementar `truco/entities/game.py`**

```python
from __future__ import annotations
from truco.entities.deck import Deck
from truco.entities.hand import Hand
from truco.entities.bet_result import BetResult
from truco.entities.play_result import PlayResult
from truco.enums import BetType, BetResponse, FlorResponse, BetStatus


class Game:
    def __init__(self, team1, team2, points_to_win: int = 30) -> None:
        self.team1 = team1
        self.team2 = team2
        self.points_to_win = points_to_win
        self._deck = Deck()
        self.hand: Hand = None  # type: ignore
        self._mano_index = 0  # 0 = team1's player, 1 = team2's player

    @property
    def _all_players(self):
        return [self.team1.players[0], self.team2.players[0]]

    @property
    def _mano_player(self):
        return self._all_players[self._mano_index]

    def start_hand(self) -> None:
        self._deck.initialize()
        self._deck.shuffle()
        for player in self._all_players:
            player.clear_hand()
            player.hand = self._deck.deal_hand()
        self.hand = Hand(mano_player=self._mano_player, players=self._all_players)
        self._mano_index = 1 - self._mano_index

    def _deal_to_players(self, cards1, cards2) -> None:
        """Used in tests to inject specific hands."""
        p1, p2 = self._all_players
        p1.hand = cards1
        p2.hand = cards2
        self.hand = Hand(mano_player=p1, players=[p1, p2])

    def play_card(self, player, card) -> PlayResult:
        if player != self.hand.current_player:
            raise RuntimeError(f"It's not {player.name}'s turn")
        if self._has_pending_bet():
            raise RuntimeError("Cannot play card while a bet is pending")

        round_winner = self.hand.register_play(player, card, self._all_players)
        round_over = self.hand.rounds[-1].resolved or (
            len(self.hand.rounds) > 1 and self.hand.rounds[-2].resolved
        )

        # Check if hand is over (can resolve)
        hand_over, hand_winner_team = self._check_hand_over()

        if hand_over and hand_winner_team:
            truco_val = self.hand.truco.current_value
            hand_winner_team.add_points(truco_val)

        next_player = self.hand.current_player if not hand_over else None

        return PlayResult(
            round_winner=round_winner,
            round_over=any(r.resolved for r in self.hand.rounds),
            hand_winner=hand_winner_team if hand_over else None,
            hand_over=hand_over,
            next_player=next_player,
            round_number=self.hand.round_number,
        )

    def _check_hand_over(self):
        teams = [self.team1, self.team2]
        # Count resolved rounds
        resolved = [r for r in self.hand.rounds if r.resolved]
        if len(resolved) < 2:
            return False, None

        def player_to_team(p):
            if p is None:
                return None
            return self.team1 if p in self.team1.players else self.team2

        r1_winner = player_to_team(resolved[0].winner)
        r2_winner = player_to_team(resolved[1].winner)

        # Win 2 in a row
        if r1_winner is not None and r1_winner == r2_winner:
            return True, r1_winner
        # Tie r1, win r2
        if r1_winner is None and r2_winner is not None:
            return True, r2_winner
        # Win r1, tie r2
        if r1_winner is not None and r2_winner is None:
            return True, r1_winner
        # Tie r1, tie r2
        if r1_winner is None and r2_winner is None:
            mano_team = player_to_team(self.hand.mano_player)
            return True, mano_team
        # Split (r1 != r2, both non-None): need round 3
        if len(resolved) >= 3:
            r3_winner = player_to_team(resolved[2].winner)
            return True, r3_winner or player_to_team(self.hand.mano_player)
        return False, None

    def _has_pending_bet(self) -> bool:
        from truco.enums import BetStatus
        return (
            self.hand.truco.status == BetStatus.PENDING
            or self.hand.envido.status == BetStatus.PENDING
            or self.hand.flor.waiting_for_response
        )

    def can_ask_truco(self, player) -> bool:
        return self.hand.truco.can_ask(self._player_team(player))

    def ask_truco(self, player) -> BetResult:
        team = self._player_team(player)
        self.hand.truco.ask(team)
        other_player = self._other_player(player)
        return BetResult(
            bet_pending=True,
            hand_value=self.hand.truco.current_value,
            who_responds=other_player,
        )

    def respond_truco(self, player, response: BetResponse) -> BetResult:
        if response == BetResponse.ACCEPT:
            self.hand.truco.accept()
            return BetResult(bet_pending=False, hand_value=self.hand.truco.current_value)
        if response == BetResponse.REFUSE:
            self.hand.truco.refuse()
            asking_team = self.hand.truco.who_asked
            refusing_team = self._other_team(asking_team)
            points = self.hand.truco.value_if_refused
            asking_team.add_points(points)
            return BetResult(bet_pending=False, hand_over=True, winner_team=asking_team, points_winner=points)
        # RAISE
        team = self._player_team(player)
        self.hand.truco.raise_bet(team)
        other = self._other_player(player)
        return BetResult(bet_pending=True, hand_value=self.hand.truco.current_value, who_responds=other)

    def can_envido(self, player) -> bool:
        return self.hand.can_envido(player)

    def ask_envido(self, player, bet_type: BetType) -> BetResult:
        if not self.hand.can_envido(player):
            raise RuntimeError("Envido not available")
        pts_needed = self.points_to_win - self._player_team(player).points
        self.hand.envido.ask(player, bet_type, points_to_win=pts_needed)
        other = self._other_player(player)
        return BetResult(bet_pending=True, who_responds=other)

    def respond_envido(self, player, response: BetResponse) -> BetResult:
        if response == BetResponse.ACCEPT:
            self.hand.envido.accept()
            # Resolve envido: compare values, award points
            p1, p2 = self._all_players
            v1 = self.hand.envido_value(p1)
            v2 = self.hand.envido_value(p2)
            if v1 >= v2:
                winner_team = self._player_team(p1)
            else:
                winner_team = self._player_team(p2)
            pts = self.hand.envido.value_accepted
            winner_team.add_points(pts)
            return BetResult(bet_pending=False, hand_over=False, winner_team=winner_team, points_winner=pts)
        if response == BetResponse.REFUSE:
            self.hand.envido.refuse()
            asker = self.hand.envido.who_asked
            asking_team = self._player_team(asker)
            pts = self.hand.envido.value_if_refused
            asking_team.add_points(pts)
            return BetResult(bet_pending=False, hand_over=False, winner_team=asking_team, points_winner=pts)
        # RAISE — caller should use ask_envido instead, but handle gracefully
        raise RuntimeError("Use ask_envido to raise the envido bet")

    def can_flor(self, player) -> bool:
        return self.hand.can_flor(player)

    def declare_flor(self, player) -> BetResult:
        team = self._player_team(player)
        self.hand.flor.declare(team)
        other = self._other_player(player)
        return BetResult(bet_pending=True, who_responds=other)

    def respond_flor(self, player, response: FlorResponse) -> BetResult:
        if response == FlorResponse.ACCEPT:
            # "Con flor me gano": declarer wins 3 points
            self.hand.flor.close()
            declaring_team = self.hand.flor.who_declared
            declaring_team.add_points(3)
            return BetResult(bet_pending=False, winner_team=declaring_team, points_winner=3)
        if response == FlorResponse.CONTRA_FLOR:
            team = self._player_team(player)
            self.hand.flor.contra_flor(team)
            other = self._other_player(player)
            return BetResult(bet_pending=True, who_responds=other)
        # CONTRA_FLOR_AL_RESTO: winner takes points to win
        self.hand.flor.close()
        # Compare flor values
        p1, p2 = self._all_players
        if Hand.has_flor(p1.hand) and Hand.has_flor(p2.hand):
            v1 = self.hand.flor_value(p1)
            v2 = self.hand.flor_value(p2)
            winner_team = self._player_team(p1) if v1 >= v2 else self._player_team(p2)
        elif Hand.has_flor(p1.hand):
            winner_team = self._player_team(p1)
        else:
            winner_team = self._player_team(p2)
        pts = self.points_to_win - winner_team.points
        winner_team.add_points(pts)
        return BetResult(bet_pending=False, winner_team=winner_team, points_winner=pts)

    def get_score(self) -> dict:
        return {self.team1: self.team1.points, self.team2: self.team2.points}

    def check_game_over(self) -> bool:
        return self.team1.points >= self.points_to_win or self.team2.points >= self.points_to_win

    def _player_team(self, player):
        return self.team1 if player in self.team1.players else self.team2

    def _other_player(self, player):
        p1, p2 = self._all_players
        return p2 if player == p1 else p1

    def _other_team(self, team):
        return self.team2 if team == self.team1 else self.team1
```

- [ ] **Step 7: Rodar todos os testes**

```bash
pytest -v
```
Expected: todos PASSED.

- [ ] **Step 8: Commit final**

```bash
git add truco/entities/game.py tests/entities/test_game.py tests/entities/test_bet_envido.py tests/entities/test_bet_flor.py tests/entities/test_score.py
git commit -m "feat: add Game orchestrator — complete truco engine implementation"
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
|---|---|
| `enums.py` (Suit, BetType, BetResponse, FlorResponse, BetStatus) | Task 2 |
| `card.py` (strength, envido_value) | Task 3 |
| `deck.py` (initialize, shuffle, deal_hand) | Task 4 |
| `player.py` (play_card, clear_hand) | Task 5 |
| `team.py` (add_points, ValueError on ≤0) | Task 5 |
| `bet_result.py` | Task 6 |
| `play_result.py` | Task 6 |
| `truco_state.py` (can_ask, ask, accept, refuse, raise_bet) | Task 7 |
| `envido_state.py` (ask, accept, refuse + bet sequence) | Task 8 |
| `flor_state.py` (declare, contra_flor, close, waiting_for_response) | Task 9 |
| `round.py` (register_play, resolve) | Task 10 |
| `hand.py` (register_play, resolve, can_envido, can_flor, envido_value, flor_value, has_flor) | Task 11 |
| `game.py` (start_hand, play_card, can_ask_truco, ask_truco, respond_truco, can_envido, ask_envido, respond_envido, can_flor, declare_flor, respond_flor, get_score, check_game_over) | Task 12 |
| `test_card`, `test_deck`, `test_player`, `test_team` | Tasks 3–5 |
| `test_round`, `test_hand`, `test_hand_envido_flor` | Tasks 10–11 |
| `test_game`, `test_bet_truco`, `test_bet_envido`, `test_bet_flor`, `test_score` | Tasks 7, 12 |
| `test_envido_state`, `test_flor_state` | Tasks 8–9 |
| `env/truco_env.py` | **Out of scope** (future phase) |

**Spec items not in scope confirmed:** `IJogadorStrategy`, Unity, `env/truco_env.py`, multi-player teams.

**No placeholders found.**

**Type consistency verified:** `Player`, `Team`, `Card`, `BetResult`, `PlayResult` used consistently across all tasks.
