"""Company research and a one-pager where every claim has a source."""
from copilot import company, facts

ID = "one_pager"
TITLE = "Company research and a one-page brief, every line sourced"
BACKLOG = "B-078"
BEFORE = ("Company research was manual web search, and the one-pager was "
          "hand-built HTML with nothing checking its claims (GitHub #34, "
          "#35).")

HOME = ("<html><head><title>Northwind Talent</title><meta name=\"description"
        "\" content=\"Northwind Talent places data and AI engineers with "
        "fast-growing companies across Europe.\"></head></html>")


def run(user, measure):
    pages = {"https://northwind.example/": HOME}
    company.fetch_page = pages.get
    facts.add(user, "Built a candidate-matching service in Python that cut "
              "screening time 40%", confirmed=True, apply=True)
    facts.add(user, "Led a team of 4 data engineers on Airflow pipelines",
              confirmed=True, apply=True)
    record = company.research(
        "Northwind Talent", "northwind.example", fetch=True, found=[
            {"kind": "service_line", "statement": "Places data engineers "
             "and ML engineers on contract and permanent roles",
             "source": "https://northwind.example/services"},
            {"kind": "size", "statement": "A network of 32,000 engineers"},
        ])
    kinds = {f["kind"] for f in record["facts"]}
    measure("their own words read from the home page",
            "what_they_do" in kinds, True)
    measure("every fact kept has an https source",
            all(f["source"].startswith("https://") for f in record["facts"]),
            True)
    measure("a fact without a link is held back as unverified",
            len(record["unverified"]), 1)
    measure("gaps come with searches to run",
            len(record["search_next"]) == len(record["gaps"]) > 0, True)
    measure("private or non-web addresses refused",
            [company._public(h) for h in ("localhost", "127.0.0.1",
                                          "169.254.169.254")],
            [False, False, False])

    draft = company.one_pager(user, record, "Data Engineer")
    measure("draft mode offers sourced material, writes nothing",
            (draft.get("mode"), "html" in draft), ("draft", False))
    ids = {v["whose"]: k for k, v in draft["sources"].items()}
    line = next(f["id"] for f in record["facts"]
                if f["kind"] == "service_line")
    mine = next(k for k, v in draft["sources"].items() if "40%" in
                v["statement"])
    good = [{"section": "fit", "text": "I built matching software that cut "
             "screening time 40%.", "sources": [mine]},
            {"section": "plugs_in", "text": "You place data engineers; I've "
             "led them and built their pipelines.",
             "sources": [line, ids["you"]]}]
    invented = good + [{"section": "why_now", "text": "Your 32,000-engineer "
                        "network is growing 50% a year.", "sources": [line]}]
    bad = company.one_pager(user, record, "Data Engineer", invented,
                            offer="A 20-minute call next week")
    measure("a number no cited source has is refused",
            any("isn't in any source" in p for p in bad.get("problems", [])),
            True)
    unsourced = company.one_pager(
        user, record, "", [{"section": "fit", "text": "I'm the best.",
                            "sources": []}], offer="A call")
    measure("a line with no source is refused", unsourced["ok"], False)
    built = company.one_pager(user, record, "Data Engineer", good,
                              offer="A 20-minute call next week",
                              me="Sam Example")
    measure("clean lines build a page", built.get("ok"), True)
    measure("company sources listed on the page",
            "https://northwind.example/services" in built.get("html", ""),
            True)
    measure("sized for one page (words)", built.get("words", 999) <= 380,
            True)
