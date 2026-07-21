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
