from datetime import time

import pytest

from app.demo.route_geometry import (
    demo_view,
    format_heure,
    route_path,
    sms_text,
    stops_after,
    stops_before,
)
from app.demo.scenario import DemoScenario, Incident

POSITIONS = ((30, 160), (90, 70), (160, 140), (230, 60), (290, 130))


def scenario(kind="retrait", position=2, ajout_xy=None, sms="Bonjour, votre passage est à {heure}.", icon="x-circle"):
    return DemoScenario(
        debut=time(8, 0),
        positions=POSITIONS,
        incident=Incident(kind=kind, position=position, label="Imprévu", icon=icon),
        sms=sms,
        ajout_xy=ajout_xy,
    )


def heures(stops):
    return [format_heure(stop.heure) for stop in stops]


def test_before_has_five_stops_every_45_minutes():
    assert heures(stops_before(scenario())) == ["8h00", "8h45", "9h30", "10h15", "11h00"]


def test_retrait_removes_the_stop_and_following_ones_move_earlier():
    after = stops_after(scenario(kind="retrait", position=2))
    assert [stop.key for stop in after] == ["s0", "s1", "s3", "s4"]
    assert heures(after) == ["8h00", "8h45", "9h30", "10h15"]


def test_ajout_inserts_a_stop_and_following_ones_move_later():
    after = stops_after(scenario(kind="ajout", position=2, ajout_xy=(140, 40)))
    assert [stop.key for stop in after] == ["s0", "s1", "ajout", "s2", "s3", "s4"]
    assert heures(after) == ["8h00", "8h45", "9h30", "10h15", "11h00", "11h45"]
    assert (after[2].x, after[2].y) == (140, 40)


def test_sms_announces_new_time_of_first_changed_stop():
    assert sms_text(scenario(kind="retrait", position=2)) == "Bonjour, votre passage est à 9h30."
    assert sms_text(scenario(kind="ajout", position=2, ajout_xy=(140, 40))) == "Bonjour, votre passage est à 10h15."


def test_retrait_of_first_stop_moves_next_client_to_start_time():
    assert sms_text(scenario(kind="retrait", position=0)) == "Bonjour, votre passage est à 8h00."


def test_format_heure_has_no_leading_zero():
    assert format_heure(time(7, 0)) == "7h00"
    assert format_heure(time(10, 5)) == "10h05"


def test_route_path_goes_through_first_and_last_stop():
    stops = stops_before(scenario())
    path = route_path(stops)
    assert path.startswith("M30,160 ")
    assert path.endswith(" 290,130")
    assert path.count("C") == len(stops) - 1


def test_demo_view_keeps_removed_stop_hidden_in_final_state():
    view = demo_view(scenario(kind="retrait", position=2))
    removed = next(marker for marker in view.markers if marker.key == "s2")
    assert (removed.heure_avant, removed.heure_apres) == ("9h30", None)
    moved = next(marker for marker in view.markers if marker.key == "s3")
    assert (moved.heure_avant, moved.heure_apres) == ("10h15", "9h30")
    assert view.incident_key == "s2"
    assert view.arrivee_key == "s4"
    assert view.path_apres == route_path(stops_after(scenario(kind="retrait", position=2)))


def test_demo_view_lists_added_stop_without_before_time():
    view = demo_view(scenario(kind="ajout", position=2, ajout_xy=(140, 40)))
    added = next(marker for marker in view.markers if marker.key == "ajout")
    assert (added.heure_avant, added.heure_apres) == (None, "9h30")
    assert view.incident_key == "ajout"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kind": "retrait", "position": 4},
        {"kind": "retrait", "position": -1},
        {"kind": "ajout", "position": 5, "ajout_xy": (1, 1)},
        {"kind": "ajout", "position": 1},
        {"kind": "retrait", "position": 1, "ajout_xy": (1, 1)},
        {"sms": "Bonjour, sans heure."},
        {"icon": "cloud-snow"},
    ],
)
def test_invalid_scenario_fails_fast(kwargs):
    with pytest.raises(ValueError):
        scenario(**kwargs)


def test_scenario_needs_exactly_five_positions():
    with pytest.raises(ValueError):
        DemoScenario(
            debut=time(8, 0),
            positions=POSITIONS[:4],
            incident=Incident(kind="retrait", position=1, label="Imprévu", icon="x-circle"),
            sms="{heure}",
        )
