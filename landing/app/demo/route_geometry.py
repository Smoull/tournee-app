from dataclasses import dataclass
from datetime import time

from app.demo.scenario import DemoScenario, DemoStop

STEP_MINUTES = 45


def _heure_at(debut: time, index: int) -> time:
    minutes = debut.hour * 60 + debut.minute + index * STEP_MINUTES
    return time(minutes // 60, minutes % 60)


def stops_before(scenario: DemoScenario) -> tuple[DemoStop, ...]:
    return tuple(
        DemoStop(f"s{index}", _heure_at(scenario.debut, index), x, y)
        for index, (x, y) in enumerate(scenario.positions)
    )


def stops_after(scenario: DemoScenario) -> tuple[DemoStop, ...]:
    keyed = [(f"s{index}", xy) for index, xy in enumerate(scenario.positions)]
    if scenario.incident.kind == "retrait":
        del keyed[scenario.incident.position]
    else:
        keyed.insert(scenario.incident.position, ("ajout", scenario.ajout_xy))
    return tuple(
        DemoStop(key, _heure_at(scenario.debut, index), x, y) for index, (key, (x, y)) in enumerate(keyed)
    )


def format_heure(heure: time) -> str:
    return f"{heure.hour}h{heure.minute:02d}"


def route_path(stops: tuple[DemoStop, ...]) -> str:
    # Catmull-Rom converti en courbes de Bézier : une route souple qui passe par chaque arrêt.
    points = [(stop.x, stop.y) for stop in stops]
    commands = [f"M{points[0][0]:g},{points[0][1]:g}"]
    for index in range(len(points) - 1):
        p0 = points[index - 1] if index > 0 else points[index]
        p1, p2 = points[index], points[index + 1]
        p3 = points[index + 2] if index + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        commands.append(f"C{c1[0]:g},{c1[1]:g} {c2[0]:g},{c2[1]:g} {p2[0]:g},{p2[1]:g}")
    return " ".join(commands)


def sms_text(scenario: DemoScenario) -> str:
    before = {stop.key: stop.heure for stop in stops_before(scenario)}
    changed = next(stop for stop in stops_after(scenario) if stop.key in before and before[stop.key] != stop.heure)
    return scenario.sms.format(heure=format_heure(changed.heure))


@dataclass(frozen=True)
class DemoMarker:
    key: str
    x: float
    y: float
    heure_avant: str | None
    heure_apres: str | None


@dataclass(frozen=True)
class DemoView:
    markers: tuple[DemoMarker, ...]
    path_avant: str
    path_apres: str
    incident_key: str
    incident_label: str
    incident_icon: str
    arrivee_key: str
    sms: str


def demo_view(scenario: DemoScenario) -> DemoView:
    before = {stop.key: stop for stop in stops_before(scenario)}
    after_stops = stops_after(scenario)
    after = {stop.key: stop for stop in after_stops}
    keys = list(before) + [key for key in after if key not in before]
    markers = tuple(
        DemoMarker(
            key=key,
            x=(after.get(key) or before[key]).x,
            y=(after.get(key) or before[key]).y,
            heure_avant=format_heure(before[key].heure) if key in before else None,
            heure_apres=format_heure(after[key].heure) if key in after else None,
        )
        for key in keys
    )
    incident = scenario.incident
    return DemoView(
        markers=markers,
        path_avant=route_path(tuple(before.values())),
        path_apres=route_path(after_stops),
        incident_key=f"s{incident.position}" if incident.kind == "retrait" else "ajout",
        incident_label=incident.label,
        incident_icon=incident.icon,
        arrivee_key=after_stops[-1].key,
        sms=sms_text(scenario),
    )
