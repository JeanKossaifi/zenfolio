"""Shared team selection for pages, homepage sections, and metadata."""

from typing import Any, Dict, List

from .models.content_models import PersonConfig
from .serialization import as_dict


_TEAM_GROUPS = (
    ("members", "Members"),
    ("interns", "Interns"),
    ("past_interns", "Past interns"),
)


def team_groups(config: Any, current_only: bool = False) -> List[Dict[str, Any]]:
    """Return nonempty groups with person configurations in configured order."""
    team = config.team
    if team is None:
        return []

    groups = []
    for membership, title in _TEAM_GROUPS:
        if current_only and membership == "past_interns":
            continue
        people = list(getattr(team, membership))
        for person in people:
            person.validate_profile()
        if people:
            groups.append({"key": membership, "title": title, "people": people})
    return groups


def team_people(config: Any, current_only: bool = False) -> List[PersonConfig]:
    """Flatten selected groups without modifying profiles or their history."""
    return [
        person
        for group in team_groups(config, current_only=current_only)
        for person in group["people"]
    ]


def team_records(config: Any, current_only: bool = False) -> List[Dict[str, Any]]:
    """Add rendering membership without storing it on the person's profile."""
    return [
        dict(as_dict(person), membership=group["key"])
        for group in team_groups(config, current_only=current_only)
        for person in group["people"]
    ]
