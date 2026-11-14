"""Proficiency tiers come from verified evidence, never from a typed
claim. Made-up person; the tiers must follow the evidence exactly."""
from copilot import proficiency

ID = "proficiency"
TITLE = "Proficiency tiers: computed from verified evidence"
BACKLOG = "B-070"
BEFORE = ("No proficiency model: a persona showed skills with no sense "
          "of how deep anyone was in them, and nothing stopped a person "
          "typing their own rating.")


def run(user, measure):
    fresh = proficiency.compute(user)
    measure("new person starts at Foundational in every dimension",
            [row["tier"] for row in fresh["tiers"]],
            ["Foundational"] * 3)

    added = proficiency.add_evidence(
        user, "Notification system, 6 countries", "shipped_system",
        ["domain", "scope"], topics=["Distributed Systems"])
    measure("submitted evidence moves no tier",
            [row["tier"] for row in proficiency.compute(user)["tiers"]],
            ["Foundational"] * 3)
    measure("submitted evidence is listed as pending",
            proficiency.compute(user)["pending_total"], 1)

    # The same work, once verified, moves the tiers it demonstrates.
    proficiency.remove_evidence(user, added["id"])
    first = proficiency.add_evidence(
        user, "Notification system, 6 countries", "shipped_system",
        ["domain", "scope"], topics=["Distributed Systems"],
        verification="verified")
    view = proficiency.compute(user)
    by_dim = {row["dimension"]: row for row in view["tiers"]}
    measure("1 verified item: Developing where it applies",
            (by_dim["domain"]["tier"], by_dim["scope"]["tier"],
             by_dim["stack_depth"]["tier"]),
            ("Developing", "Developing", "Foundational"))
    measure("the tier lists the evidence behind it",
            [e["id"] for e in by_dim["domain"]["evidence"]],
            [first["id"]])
    measure("no tier is stored on the evidence record",
            "tier" in first["recorded"], False)

    for n in range(2, 4):
        proficiency.add_evidence(
            user, f"Design doc {n}: event pipeline", "design_doc",
            ["domain"], verification="verified")
    view = proficiency.compute(user)
    by_dim = {row["dimension"]: row for row in view["tiers"]}
    measure("3 verified items: Proficient",
            by_dim["domain"]["tier"], "Proficient")
    measure("other dimensions stay where their evidence puts them",
            by_dim["scope"]["tier"], "Developing")
    measure("verified-from counts by kind",
            view["verified_from"],
            {"shipped_system": 1, "design_doc": 2})

    measure("a made-up kind is refused",
            "error" in proficiency.add_evidence(
                user, "x", "trophy", ["domain"]), True)
    measure("a made-up dimension is refused",
            "error" in proficiency.add_evidence(
                user, "x", "design_doc", ["charisma"]), True)
