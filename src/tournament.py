"""Which teams are still alive in the 2026 World Cup.

Names must match the ``Team`` column in ``data/team_statistics.csv`` exactly.
Edit this set between rounds — group-stage exits first, then knockout losers.
"""

from __future__ import annotations

# Snapshot: 2026-07-01 (Round of 32 in progress).
# 16 group-stage eliminated + 7 Round of 32 losers (Jun 28 – 30).
ELIMINATED: frozenset[str] = frozenset({
    # Group stage
    "Korea Republic", "Czechia", "Qatar", "Scotland", "Haiti", "Türkiye",
    "Curaçao", "Tunisia", "IR Iran", "New Zealand", "Uruguay",
    "Saudi Arabia", "Iraq", "Jordan", "Uzbekistan", "Panama",
    # Round of 32
    "South Africa", "Japan", "Germany", "Netherlands",
    "Côte d'Ivoire", "Sweden", "Ecuador",
})


def is_alive(team: str) -> bool:
    return team not in ELIMINATED
