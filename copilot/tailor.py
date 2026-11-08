"""Tailoring a resume to a posting without rewriting history.

The assistant proposes each tailored line and names the confirmed facts
it rests on. The server checks every line and blocks it, with the
reason, when it:

- cites no fact, or a fact that's unsure, replaced or missing;
- has a number no cited fact holds (unsupported_number);
- uses a verb that claims more than the person's part (ownership);
- merges facts from different jobs into one claim (merged_claim);
- names one of the person's honest gaps (honest_gap);
- adds a posting keyword the cited facts don't back (invented_keyword).

Accepted lines can be saved as a named resume version, so the outcome
log (resume_label on applications) shows which version went where.
"""
from copilot import facts, journey, jobs, store

MAX_EDITS = 30


def _numbers_backed(line, cited):
    held = {(m["value"], m["unit"]) for f in cited
            for m in f.get("metrics", [])}
    held |= {(m["value"], m["unit"]) for f in cited
             for m in facts.parse_metrics(f["statement"])}
    return [m for m in facts.parse_metrics(line)
            if (m["value"], m["unit"]) not in held]


def _check(user, edit, posting, honest, backed_terms):
    line = str(edit.get("line", "")).strip()
    ids = [str(i) for i in (edit.get("fact_ids") or [])]
    if edit.get("fact_id"):
        ids.insert(0, str(edit["fact_id"]))
    problems = []
    if not line:
        return line, ids, [{"rule": "empty", "why": "No line given."}]
    cited = {i: store.get(user, i) for i in dict.fromkeys(ids)}
    usable = [{**f, "id": i} for i, f in cited.items()
              if f and f.get("statement")
              and f.get("confidence") == "confirmed"
              and not f.get("superseded_by")]
    if not ids:
        problems.append({"rule": "no_fact", "why": "Every tailored line "
                         "must name the confirmed fact it rests on."})
    elif len(usable) < len(cited):
        problems.append({"rule": "unconfirmed_fact", "why": "A cited fact "
                         "is missing, unsure or replaced. Confirm it with "
                         "the person first."})
    if usable:
        extra = _numbers_backed(line, usable)
        if extra:
            shown = ", ".join(f"{m['value']:g} {m['unit']}" for m in extra)
            problems.append({"rule": "unsupported_number",
                             "why": f"No cited fact holds: {shown}."})
        roles = {(f.get("employer") or "").strip().lower() for f in usable}
        roles.discard("")
        if len(roles) > 1:
            problems.append({"rule": "merged_claim", "why": "This joins "
                             "work from different jobs into one claim. "
                             "Keep one job per line."})
        owner = facts.ownership_check(user, line, usable[0]["id"])
        if not owner["ok"] and owner.get("fact_ownership"):
            problems.append({"rule": "ownership", "why": owner["why"],
                             "suggest": owner["suggest"]})
    source = " ".join(f["statement"] for f in usable).lower() + \
        " " + backed_terms
    for skill in jobs.SKILLS:
        if not jobs._has_skill(skill, line.lower()):
            continue
        if skill in honest:
            problems.append({"rule": "honest_gap", "term": skill,
                             "why": f"'{skill}' is on the person's honest-"
                                    "gaps list."})
        elif usable and not jobs._has_skill(skill, source):
            problems.append({"rule": "invented_keyword", "term": skill,
                             "why": f"'{skill}' isn't in the cited facts. "
                                    "Add it only if the person confirms "
                                    "they used it there."})
    return line, list(dict.fromkeys(ids)), problems


def resume_tailor(user, posting_text, edits, save_as="", company=""):
    profile = journey.profile(user)
    honest = {g.lower() for g in profile.get("honest_gaps", [])}
    backed_terms = " ".join(profile.get("domain_keywords", [])).lower()
    posting = (posting_text or "").lower()
    wanted = [s for s in jobs.SKILLS if jobs._has_skill(s, posting)]
    accepted, blocked, invented = [], [], []
    for edit in (edits or [])[:MAX_EDITS]:
        line, ids, problems = _check(user, edit if isinstance(edit, dict)
                                     else {"line": str(edit)},
                                     posting, honest, backed_terms)
        if problems:
            blocked.append({"line": line, "fact_ids": ids,
                            "problems": problems})
            invented += [p["term"] for p in problems
                         if p["rule"] == "invented_keyword"]
        else:
            accepted.append({"line": line, "fact_ids": ids})
    text = "\n".join(f"- {a['line']}" for a in accepted)
    covered = [s for s in wanted if jobs._has_skill(s, text.lower())]
    result = {
        "accepted": accepted, "blocked": blocked,
        "honest_gaps": sorted(s for s in wanted if s in honest),
        "invented_claims_blocked": sorted(set(invented)),
        "posting_keywords_covered": f"{len(covered)}/{len(wanted)}"
        if wanted else "n/a",
        "say": "Show the accepted lines. For each blocked one, give its "
               "reason in a few words and ask one question at a time; "
               "never add an honest gap.",
    }
    if save_as and accepted:
        body = {"label": save_as[:60], "text": text,
                "bullets": len(accepted), "tailored_for": company[:80],
                "fact_ids": sorted({i for a in accepted
                                    for i in a["fact_ids"]})}
        result["saved"] = {"id": store.put(user, "resume", body),
                           "label": body["label"],
                           "next": "Log the application with this "
                                   "resume_label so outcomes are tracked."}
    return result
