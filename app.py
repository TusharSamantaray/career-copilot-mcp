"""Career Copilot: an MCP server for job seekers.

Cloud (HTTP):   uv run app.py          serves /mcp and /health on $PORT (8080)
Local (stdio):  uv run app.py --stdio  for Claude Desktop / Claude Code

Auth, hosted: either
- GitHub sign-in: set CAREER_COPILOT_GITHUB_CLIENT_ID and _SECRET. People
  connect with the plain URL /mcp and sign in with GitHub. Optional
  CAREER_COPILOT_ALLOWED_GITHUB_USERS limits it to an invite list.
- API keys: set CAREER_COPILOT_API_KEY (comma-separated). Callers send it as
  "Authorization: Bearer <key>", "X-API-Key: <key>", or in the URL:
  /mcp?key=<key> (for apps that can't set headers).
"""
import asyncio
import hashlib
import hmac
import os
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

STDIO = "--stdio" in sys.argv
HOME_DIR = Path(os.environ.get("CAREER_COPILOT_HOME",
                               Path.home() / "CareerCopilot"))
if STDIO:
    # Local mode can start from any folder (uvx, Claude Desktop), so keep
    # data in one fixed place. Set before copilot modules read it.
    os.environ.setdefault("COPILOT_DATA_DIR", str(HOME_DIR / "data"))

import fastmcp
from fastmcp import FastMCP
from fastmcp.exceptions import NotFoundError, ResourceError, ToolError
from pydantic import ValidationError
from fastmcp.server.dependencies import (get_access_token, get_http_headers,
                                         get_http_request)
from fastmcp.server.middleware import Middleware, MiddlewareContext
from loguru import logger
from mcp.types import LATEST_PROTOCOL_VERSION
from starlette.requests import Request
from starlette.responses import JSONResponse

from copilot import ats
from copilot import autopilot
from copilot import careers
from copilot import coach
from copilot import conduct
from copilot import dashboard as dash
from copilot import deadlines
from copilot import demand
from copilot import economy
from copilot import errors
from copilot import evidence
from copilot import facts as fact_record
from copilot import finance
from copilot import guide
from copilot import insights
from copilot import intro
from copilot import jobs
from copilot import journey
from copilot import loops
from copilot import nudges
from copilot import outreach
from copilot import persona
from copilot import places
from copilot import prep
from copilot import recruiter
from copilot import sponsorship as visa_sponsor
from copilot import store
from copilot import tailor
from copilot import timeline
from copilot import watch
from copilot.knowledge.money import (DISCLAIMER, ECONOMY_GUIDES, INVEST_GUIDES,
                             LAYOFF_PLAYBOOK)
from copilot.scoring import score_resume

VERSION = "0.3.0"
# Hosts route traffic in from outside the container, so listen on all
# interfaces; set HOST=127.0.0.1 to keep a local server private.
HOST = os.environ.get("HOST", "0.0.0.0")  # nosec B104
PORT = int(os.environ.get("PORT", "8080"))
LOG_DIR = os.environ.get("CAREER_COPILOT_LOG_DIR",
                         str(HOME_DIR / "logs") if STDIO else "logs")
LOG_LEVEL = os.environ.get("CAREER_COPILOT_LOG_LEVEL", "INFO")
API_KEYS = [key.strip() for key in
            os.environ.get("CAREER_COPILOT_API_KEY", "").split(",")
            if key.strip()]
# Optional header a marketplace gateway uses to name the subscriber.
USER_HEADER = os.environ.get("CAREER_COPILOT_USER_HEADER", "").lower()
ALLOW_OPEN = os.environ.get("CAREER_COPILOT_ALLOW_OPEN") == "1"
# Separate key for the aggregate /insights endpoint used by the improver.
ADMIN_KEY = os.environ.get("CAREER_COPILOT_ADMIN_KEY", "")
# GitHub sign-in: a plain connector URL, no key in it. Career Copilot only
# sees the GitHub user id (hashed for storage), never a password.
GITHUB_ID = os.environ.get("CAREER_COPILOT_GITHUB_CLIENT_ID", "")
GITHUB_SECRET = os.environ.get("CAREER_COPILOT_GITHUB_CLIENT_SECRET", "")
OAUTH = bool(GITHUB_ID and GITHUB_SECRET) and not STDIO
PUBLIC_URL = (os.environ.get("CAREER_COPILOT_PUBLIC_URL")
              or os.environ.get("RENDER_EXTERNAL_URL")
              or f"http://localhost:{PORT}")
ALLOWED_GITHUB = {name.strip().lower() for name in
                  os.environ.get("CAREER_COPILOT_ALLOWED_GITHUB_USERS",
                                 "").split(",") if name.strip()}
USER_SALT = os.environ.get("CAREER_COPILOT_USER_SALT", "")

LOCAL_USER = "local-user"
GRACE_DAYS_H1B = 60
STATUSES = ["saved", "applied", "assessment", "interviewing",
            "offer", "rejected", "withdrawn"]
SENSITIVE_ARGS = {"api_key", "token", "password", "authorization",
                  "work_authorization", "status_tied_to_job",
                  # money amounts are personal data
                  "balance", "value", "current", "target", "monthly_burn",
                  "monthly_core_spend", "current_fund", "monthly_saving",
                  "target_amount", "saved", "current_savings",
                  "monthly_budget", "comp_floor",
                  # outreach: recipients, drafts and their seals
                  "to", "subject", "body", "approval_id",
                  # raw emails, calendar events and moods stay out of logs
                  "emails", "events", "mood", "note", "text", "statement",
                  # people's own words: lessons, resume lines, answers
                  "add", "bullet", "answer", "posting_text", "resume_text",
                  # a recruiter's questions and intro messages, and the
                  # contact either side shares at a reveal
                  "question", "message", "share",
                  # pasted error text and app names in report_issue
                  "error_code", "client_hint",
                  # file paths can carry a person's name
                  "rendered_file"}
MAX_LOGGED_CHARS = 80


# ---------------------------------------------------------------- logging

def setup_logging():
    """stdout plus a rolling file. In stdio mode stdout carries the MCP
    protocol, so console logs go to stderr instead."""
    logger.remove()
    fmt = ("{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
           "{message}")
    logger.add(sys.stderr if STDIO else sys.stdout, format=fmt,
               level=LOG_LEVEL)
    os.makedirs(LOG_DIR, exist_ok=True)
    logger.add(os.path.join(LOG_DIR, "mcp_server.log"), format=fmt,
               level=LOG_LEVEL, rotation="10 MB", retention=10,
               enqueue=True, backtrace=True, diagnose=False)


def mask_args(args: dict | None) -> dict:
    """Redact secrets and replace long free text (resumes) with a length."""
    masked = {}
    for key, value in (args or {}).items():
        if key.lower() in SENSITIVE_ARGS:
            masked[key] = "***"
        elif isinstance(value, (list, dict)):
            # Lists/objects carry the most personal data (emails, events,
            # accounts): log only their size.
            masked[key] = f"<{type(value).__name__} of {len(value)}>"
        elif isinstance(value, str) and len(value) > MAX_LOGGED_CHARS:
            masked[key] = f"<{len(value)} chars>"
        elif isinstance(value, str) and "@" in value:
            masked[key] = "<redacted>"
        else:
            masked[key] = value
    return masked


# ------------------------------------------------------------------- auth

def _presented_key(headers: dict) -> str:
    auth = headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return headers.get("x-api-key", "").strip() or _url_key()


def _url_key() -> str:
    """claude.ai and ChatGPT connectors can't send headers, so the key may
    come in the connector URL as ?key=<key>."""
    try:
        return get_http_request().query_params.get("key", "").strip()
    except RuntimeError:
        return ""


def _github_claims() -> dict:
    token = get_access_token()
    return token.claims if token else {}


def authorize():
    """Raise PermissionError unless the caller signed in or sent a valid
    API key."""
    if STDIO or (ALLOW_OPEN and not API_KEYS and not OAUTH):
        return
    if OAUTH:
        claims = _github_claims()
        if not claims.get("sub"):
            raise PermissionError(errors.message(
                "AUTH_REQUIRED", "Unauthorized: sign in with GitHub."))
        if ALLOWED_GITHUB and \
                str(claims.get("login", "")).lower() not in ALLOWED_GITHUB:
            raise PermissionError(errors.message(
                "NOT_INVITED", "This Career Copilot is invite-only. Ask "
                "its owner to add your GitHub username."))
        return
    key = _presented_key(get_http_headers(include_all=True))
    if not key or not any(hmac.compare_digest(key, valid)
                          for valid in API_KEYS):
        raise PermissionError(errors.message(
            "AUTH_REQUIRED", "Unauthorized: send a valid API key as "
            "'Authorization: Bearer <key>'."))


def current_user() -> str:
    """Storage namespace for the caller: a hash, never the raw key."""
    if STDIO:
        return LOCAL_USER
    if OAUTH:
        sub = str(_github_claims().get("sub", ""))
        if not sub:
            return "anonymous"
        seed = f"github:{sub}:{USER_SALT}"
        return "gh_" + hashlib.sha256(seed.encode()).hexdigest()[:16]
    headers = get_http_headers(include_all=True)
    seed = _presented_key(headers)
    if USER_HEADER and headers.get(USER_HEADER):
        seed += ":" + headers[USER_HEADER]
    if not seed:
        return "anonymous"
    return "u_" + hashlib.sha256(seed.encode()).hexdigest()[:16]


class AuthAndAudit(Middleware):
    """Checks the key, logs the call, times it and contains failures."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        message = context.message
        return await self._run("tool", message.name, message.arguments,
                               ToolError, context, call_next)

    async def on_read_resource(self, context: MiddlewareContext, call_next):
        return await self._run("resource", str(context.message.uri), None,
                               ResourceError, context, call_next)

    async def _run(self, kind, name, args, error_cls, context, call_next):
        try:
            authorize()
        except PermissionError as exc:
            logger.warning(f"{kind} denied: {name} (bad or missing key)")
            raise error_cls(str(exc)) from None
        user = current_user()
        logger.info(f"{kind} call: {name} user={user} "
                    f"args={mask_args(args)}")
        start = time.perf_counter()
        try:
            result = await call_next(context)
        except (ToolError, ResourceError) as exc:
            if exc.__cause__ is not None:
                # FastMCP wraps a crashing tool's exception: a real fault.
                self._crash(kind, name, user, start, error_cls, exc.__cause__)
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning(f"{kind} error: {name} after {elapsed:.1f} ms: "
                           f"{exc}")
            self._signal(kind, name, user, False, elapsed)
            raise
        except NotFoundError:
            # Usually a tool list cached from before a deploy.
            code = "UNKNOWN_TOOL" if kind == "tool" else "UNKNOWN_RESOURCE"
            logger.warning(f"{kind} not found: {name} ({code})")
            raise error_cls(errors.message(
                code, f"This server has no {kind} called '{name}'. "
                "Refresh the tool list: reconnect, or start a new chat."
            )) from None
        except ValidationError as exc:
            # Field names only: the values sent can be personal.
            fields = errors.field_errors(exc)
            logger.warning(f"{kind} bad arguments: {name}: {fields}")
            self._signal(kind, name, user, False,
                         (time.perf_counter() - start) * 1000)
            raise error_cls(errors.message(
                "BAD_ARGUMENTS", f"Check these values: {fields}.")) from None
        except Exception as exc:
            self._crash(kind, name, user, start, error_cls, exc)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"{kind} done: {name} in {elapsed:.1f} ms")
        self._signal(kind, name, user, True, elapsed)
        return result

    def _crash(self, kind, name, user, start, error_cls, exc):
        """Log a fault with a ref; the caller sees only the code and ref."""
        elapsed = (time.perf_counter() - start) * 1000
        ref = errors.new_ref()
        logger.opt(exception=exc).error(f"{kind} crashed: {name} after "
                                        f"{elapsed:.1f} ms (ref {ref})")
        self._signal(kind, name, user, False, elapsed)
        raise error_cls(errors.message(
            "INTERNAL_ERROR", f"Something went wrong on the server "
            f"(ref {ref}). It has been logged.")) from None

    @staticmethod
    def _signal(kind, name, user, ok, elapsed):
        """Usage signal for the improver; never allowed to break a call."""
        if kind != "tool":
            return
        try:
            insights.record("tool", name, user, ok, elapsed)
        except Exception:
            logger.exception("insights record failed")


def note_miss(kind, label):
    """Record a lookup that found nothing (scrubbed, k-anonymous)."""
    try:
        insights.record(kind, label, current_user(), ok=False)
    except Exception:
        logger.exception("insights record failed")


def make_auth():
    """GitHub sign-in when configured; None keeps API-key mode. Nothing
    about sign-ins is stored, so restarts on the free host don't sign
    anyone out (see copilot/signin.py)."""
    if not OAUTH:
        return None
    from copilot.signin import StatelessGitHubProvider, use_clear_messages
    use_clear_messages()
    return StatelessGitHubProvider(
        client_id=GITHUB_ID, client_secret=GITHUB_SECRET,
        base_url=PUBLIC_URL,
        key=os.environ.get("CAREER_COPILOT_JWT_KEY") or GITHUB_SECRET,
        allowed=ALLOWED_GITHUB,
        github_base=os.environ.get("CAREER_COPILOT_GITHUB_BASE",
                                   "https://github.com"),
        github_api=os.environ.get("CAREER_COPILOT_GITHUB_API",
                                  "https://api.github.com"))


mcp = FastMCP("career-copilot", version=VERSION, auth=make_auth(),
              instructions=(
    # The soul: who Career Copilot is when it talks to someone.
    "You are Career Copilot: a warm, honest guide that helps people find "
    "their next career move and take it, one small step at a time. While "
    "the person is working on their career, use Career Copilot's voice "
    "below, even over another assistant style or persona. "
    "How you reply (always): " + " ".join(conduct.REPLY_STYLE) + " "
    "People act on short direction; a long answer, however good, gets "
    "dropped. If a reply runs long, cut it to the one step that matters "
    "now. Tool results are for you: pick the one thing that matters and "
    "say it simply, never paste them back. "
    "Start of a session: call ground_rules; if accepted is false, give its "
    "three-line summary (data_handling has the details if asked) and ask "
    "if that's OK, then call "
    "ground_rules(accept=true); if they say no, keep helping but save "
    "nothing about them. Then call journey_state and follow its next: ask "
    "only its question, or offer its one step. If they have watches, call "
    "digest_get too and mention only its most urgent item. When "
    "journey_state shows fast_track, say fast-track is on and why in one "
    "line: runway first, shorter plans, freshest roles first. Save any "
    "hard date with deadline_add (best case and conservative). A new person can come in "
    "two ways: say what's on their mind (pull out the facts, read them "
    "back with confirmed or unsure labels, and save only what they "
    "confirm with profile_save), or answer starter questions one at a "
    "time (save each answer at once). Never re-ask what's known. Never "
    "more than five questions before giving something useful back. Most "
    "people arrive tired or overwhelmed: ask "
    "their energy (low, medium or high?) and call daily_step for ONE thing "
    "to do today; when they finish, call step_done and celebrate it. Rest "
    "days are fine; the rule is never skip twice. Name the hard thing, then "
    "shrink it. If a different role (career_move) or city (where_to_move) "
    "would help them grow, say so in one line and let them decide. "
    "Someone hiring (not job seeking) uses persona_search, persona_chat "
    "and persona_intro: anonymous verified work only, never identity or "
    "pay; identity_reveal shares contacts only after both sides confirm. "
    "How you talk (always): stay on career, work, money "
    "and life planning, and steer back politely when asked about other "
    "things; be respectful and neutral, never insult, mock or stereotype "
    "anyone; never comment on religion, politics, race, gender, age, "
    "health or other personal traits unless the person raises them for a "
    "practical reason; say where each fact comes from, say 'I don't know' "
    "instead of guessing, and label estimates. Before showing a resume "
    "line, message, cover letter or plan the person may send or rely on, "
    "run response_check and fix everything it flags. If someone mentions self-harm or being unsafe, "
    "stop all career talk and share the crisis_support resources from "
    "daily_step. Rules: only facts the user confirmed go on a resume; "
    "never invent numbers; money, tax, visa and relocation outputs are "
    "education, not advice, so say so; nothing leaves the chat without the "
    "person's yes to that exact text: run outreach_review, show it word "
    "for word, and only after a yes call outreach_approve, then send with "
    "their own connector and check it arrived. Career Copilot never sends "
    "anything itself and never logs in anywhere: "
    "never ask for passwords, one-time codes or bank logins. To bring in "
    "email, calendar, meetings or bank balances, read them from the user's "
    "own connectors in this chat and pass only the needed fields (see "
    "companions); otherwise ask the user to paste or type them. After "
    "onboarding, and whenever the user wants to see their progress, call "
    "dashboard and show the returned html as an artifact titled 'Career "
    "Copilot' (if the file was saved locally, also tell them the path so "
    "they can open and customise it). You may "
    "ask once whether an answer helped and call feedback, never with "
    "personal details."))
mcp.add_middleware(AuthAndAudit())


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Unauthenticated liveness check for the host. storage names the
    backend (sqlite or postgres) so the owner can confirm data will
    survive restarts; it never includes the database address.
    auth_mode tells a new client what the server expects before it
    ever calls a tool: "github-oauth", "api-key", "open", or
    "off (stdio)". invite_only says whether sign-in is limited to the
    owner's list (never who is on it). insights says where anonymous
    usage counts live: file (wiped on a free host's restart) or
    database."""
    if STDIO:
        auth_mode = "off (stdio)"
    elif OAUTH:
        auth_mode = "github-oauth"
    elif API_KEYS:
        auth_mode = "api-key"
    else:
        auth_mode = "open"
    tools = await mcp.get_tools()
    return JSONResponse({"status": "ok", "version": VERSION,
                         "storage": store.BACKEND.name,
                         "auth_mode": auth_mode,
                         "invite_only": bool(OAUTH and ALLOWED_GITHUB),
                         "insights": insights.location(),
                         "tool_count": len(tools)})


@mcp.custom_route("/data-handling", methods=["GET"])
async def data_handling_route(request: Request) -> JSONResponse:
    """Unauthenticated, machine-readable data-handling statement, so a
    cautious assistant or person can check it before connecting. Static
    text only; nothing about any person."""
    return JSONResponse(conduct.DATA_HANDLING)


@mcp.custom_route("/insights", methods=["GET"])
async def insights_route(request: Request) -> JSONResponse:
    """Aggregate, k-anonymous usage stats for the weekly improver.
    Needs CAREER_COPILOT_ADMIN_KEY; 404 when it isn't set."""
    if not ADMIN_KEY:
        return JSONResponse({"error": "not found"}, status_code=404)
    key = _presented_key({k.lower(): v for k, v in request.headers.items()})
    if not key or not hmac.compare_digest(key, ADMIN_KEY):
        logger.warning("insights denied (bad or missing admin key)")
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    days = request.query_params.get("days", "30")
    days = int(days) if days.isdigit() else 30
    return JSONResponse(insights.summary(min(days, 365)))


# ------------------------------------------------------------------ tools

@mcp.tool
def profile_get() -> dict:
    """Read the user's saved job-search profile.

    Returns target_role, level, location, hours_preference, comp_floor and
    work_authorization, or a note when no profile exists yet. Call this
    first in a session to tailor advice to the user's goals.
    """
    rows = store.list_kind(current_user(), "profile")
    return rows[-1] if rows else {"note": "No profile yet."}


@mcp.tool
def journey_state() -> dict:
    """Call first every session (after ground_rules). Where the person is
    (stage: orient, foundation, search, prepare, decide), what's known
    with confirmed or unsure labels, what's missing, and next: the one
    question to ask or the one step to offer. Follow next and say."""
    return journey.journey_state(current_user())


@mcp.tool
def profile_from_text(facts: list[dict], apply: bool = False) -> dict:
    """Save facts pulled from what the person said in their own words.

    facts: [{field, value, confirmed}], where field is a profile_save field
    (e.g. current_role, wants, dealbreakers) or "experience" (then also
    employer, title, optional start, end). confirmed: true only if they
    said it plainly; otherwise it's saved as unsure. apply=false returns a
    read_back to show them; call again with apply=true after they agree
    (write action).
    """
    return journey.profile_from_text(current_user(), facts, apply)


@mcp.tool
def direction_options(skills: list[str] | None = None,
                      current_role: str = "", years: int = 0) -> dict:
    """Two or three career directions to test, each with fit, distance,
    gaps, risk and a first test for this week. Uses the profile for
    anything not passed. Offer them in one line each and let the person
    pick."""
    return journey.direction_options(current_user(), skills, current_role,
                                     years)


@mcp.tool
def profile_save(target_role: str = "", situation: str = "",
                 current_role: str = "", level: str = "",
                 industry: str = "", years_experience: int = 0,
                 location: str = "", country: str = "",
                 goals: str = "", hours_preference: str = "",
                 comp_floor: str = "", work_authorization: str = "",
                 schedule: str = "", voice: str = "",
                 wants: list[str] | None = None,
                 dealbreakers: list[str] | None = None,
                 locations: list[str] | None = None,
                 target_companies: list[str] | None = None,
                 excluded_companies: list[str] | None = None,
                 domain_keywords: list[str] | None = None,
                 honest_gaps: list[str] | None = None,
                 unsure: list[str] | None = None,
                 skip: list[str] | None = None,
                 replace: bool = False) -> dict:
    """Save profile answers as they come, one or a few at a time (write
    action). Nothing is required. Empty fields keep what's saved; list
    fields add items. Set replace=true only to start the profile over.

    situation: starting out, between jobs, working, want a change, or
    interviewing. target_role: e.g. "Product Manager" (leave empty if
    unsure). level: entry, mid, senior or lead. goals: comma-separated from
    job, career_move, finance, future. comp_floor: e.g. "60k".
    wants rank results; dealbreakers filter them out. honest_gaps: things
    they can't truthfully claim, which tailoring respects.
    work_authorization: only if they volunteer it. voice: how drafts
    sound, plain (default), warm or formal.
    unsure: names of fields they aren't sure about (labelled unsure, never
    used on a resume as fact). skip: fields they said "not sure" or "skip"
    to, so they aren't asked again. Read the answer back before saving.
    """
    fields = {"target_role": target_role, "situation": situation,
              "current_role": current_role, "level": level,
              "industry": industry, "years_experience": years_experience,
              "location": location, "country": country, "goals": goals,
              "hours_preference": hours_preference, "comp_floor": comp_floor,
              "work_authorization": work_authorization, "schedule": schedule,
              "voice": voice,
              "wants": wants, "dealbreakers": dealbreakers,
              "locations": locations, "target_companies": target_companies,
              "excluded_companies": excluded_companies,
              "domain_keywords": domain_keywords,
              "honest_gaps": honest_gaps}
    return journey.save_profile(current_user(), fields, unsure or [],
                                skip or [], replace)


@mcp.tool
def experience_add(employer: str, title: str, start: str, end: str,
                   fact: str, confirmed: bool,
                   owned_or_contributed: str = "contributed") -> dict:
    """Store one fact about a past job (write action).

    fact: a single achievement, e.g. "Cut p95 latency from 900 to 200 ms".
    confirmed: True only when the user stated the fact themselves.
    Unconfirmed facts are kept but never appear on a resume draft.
    owned_or_contributed: "owned" if the user led the work.
    start, end: years or YYYY-MM. Returns the new record id.
    """
    body = {"employer": employer, "title": title, "start": start,
            "end": end, "fact": fact, "confirmed": confirmed,
            "role_in_work": owned_or_contributed}
    user = current_user()
    record_id = store.put(user, "experience", body)
    ownership = owned_or_contributed if owned_or_contributed in \
        fact_record.OWNERSHIP else "contributed"
    recorded = fact_record.add(
        user, fact, "said", employer, title, start, end, ownership,
        fact_record.parse_metrics(fact), confirmed,
        f"experience:{record_id}", apply=True)
    result = {"id": record_id, "fact_id": recorded["fact_id"]}
    if recorded["conflicts"]:
        result["conflicts"] = recorded["conflicts"]
        result["ask"] = recorded["ask"]
    return result


@mcp.tool
def fact_add(statement: str, source: str = "said", employer: str = "",
             title: str = "", start: str = "", end: str = "",
             ownership: str = "contributed",
             metrics: list[dict] | None = None, confirmed: bool = False,
             source_ref: str = "", apply: bool = False) -> dict:
    """Record one claim about the person's work, with where it came from.

    source: said (the person told you), imported (from a resume; set
    source_ref to its label) or inferred (you guessed; never confirmed).
    ownership: owned, led, contributed or observed. Ask "did you write it,
    lead it or fix it?" before choosing owned or led. metrics: numbers in
    the statement, e.g. [{"value": 40, "unit": "%"}], with approx=true for
    "about". apply=false previews and lists conflicts with saved facts
    (different dates for the same job, different numbers for the same
    work); apply=true saves (write action). Settle conflicts with the
    person, then fact_resolve.
    """
    return fact_record.add(current_user(), statement, source, employer,
                           title, start, end, ownership, metrics, confirmed,
                           source_ref, apply)


@mcp.tool
def ownership_check(bullet: str, fact_id: str = "") -> dict:
    """Before using a strong verb (led, owned, architected, designed,
    managed...), check it against the person's part in the fact behind
    it. Finds the closest fact when fact_id is empty. ok=false comes with
    a softer verb or the question to ask: wrote it, led it or fixed it?"""
    return fact_record.ownership_check(current_user(), bullet, fact_id)


@mcp.tool
def fact_conflicts() -> dict:
    """Every place where saved facts disagree on a date or a number. Ask
    the person about one at a time."""
    return fact_record.conflicts(current_user())


@mcp.tool
def fact_resolve(keep_id: str, drop_id: str,
                 confirm_kept: bool = True) -> dict:
    """Settle a conflict the way the person said (write action): keep one
    fact, retire the other. The kept fact becomes confirmed unless it was
    inferred."""
    return fact_record.resolve(current_user(), keep_id, drop_id,
                               confirm_kept)


@mcp.tool
def experience_list(confirmed_only: bool = False) -> list:
    """List stored experience facts, oldest first.

    Pass confirmed_only=True to see only what may go on a resume.
    """
    rows = store.list_kind(current_user(), "experience")
    return [r for r in rows if r["confirmed"]] if confirmed_only else rows


@mcp.tool
def resume_score(resume_text: str) -> dict:
    """Score pasted resume text 0-100 on the ten-check rubric.

    Returns the total, points and a note per check, and top_fix: the single
    weakest check to fix first. Read copilot://rubric for the checks.
    """
    return score_resume(resume_text)


@mcp.tool
def resume_build_draft() -> str:
    """Draft resume bullets from CONFIRMED facts only, grouped by job.

    Never invents numbers. Ends with a count of facts left off because they
    are unconfirmed (ask the user about those before adding them) and the
    result of response_check on the draft.
    """
    user = current_user()
    facts = store.list_kind(user, "experience")
    confirmed = [f for f in facts if f["confirmed"]]
    skipped = len(facts) - len(confirmed)
    # Facts confirmed in the fact record (for example a resume number the
    # person settled with fact_resolve) count too, once each.
    have = {f["fact"].lower() for f in confirmed}
    for f in fact_record.confirmed_facts(user):
        if f["statement"].lower() not in have:
            have.add(f["statement"].lower())
            confirmed.append({"title": f["title"] or "Role",
                              "employer": f["employer"] or "employer",
                              "start": f["start"], "end": f["end"],
                              "fact": f["statement"]})
    lines, current = [], None
    for fact in confirmed:
        header = f"{fact['title']}, {fact['employer']} " \
                 f"({fact['start']} - {fact['end']})"
        if header != current:
            lines.append(f"\n{header}")
            current = header
        lines.append(f"- {fact['fact']}")
    lines.append(f"\n[{skipped} unconfirmed fact(s) left off.]")
    check = conduct.check(user, "\n".join(lines), "resume")
    lines.append("[Check: ok.]" if check["ok"] else
                 "[Check: fix " + ", ".join(sorted({i["type"] for i in
                                                    check["issues"]}))
                 + " before using this.]")
    return "\n".join(lines).strip()


@mcp.tool
def application_log(company: str, role: str, status: str = "applied",
                    next_action: str = "", due_date: str = "",
                    req_id: str = "", resume_label: str = "",
                    sponsorship: str = "unknown") -> dict:
    """Add a job application to the pipeline (write action).

    status: one of saved, applied, assessment, interviewing, offer,
    rejected, withdrawn. next_action: e.g. "Finish HackerRank".
    due_date: YYYY-MM-DD for the next action. req_id: the requisition or
    job id from the posting, so a later rejection closes the right one.
    resume_label: which resume version was sent, for the outcome log.
    sponsorship: yes, no or unknown, what the posting or recruiter said
    about visa sponsorship (only matters if the person needs it).
    Returns the new id.
    """
    if status not in STATUSES:
        return {"error": f"status must be one of {STATUSES}"}
    if sponsorship not in ("yes", "no", "unknown"):
        return {"error": "sponsorship must be yes, no or unknown"}
    body = {"company": company, "role": role, "status": status,
            "next_action": next_action, "due_date": due_date,
            "req_id": req_id.strip().upper(),
            "resume_label": resume_label.strip()[:60],
            "sponsorship": sponsorship}
    user = current_user()
    app_id = store.put(user, "application", body)
    reminders = autopilot.on_application(user, app_id, body)
    return {"id": app_id, "reminders_created": len(reminders)}


@mcp.tool
def application_update(application_id: str, status: str = "",
                       next_action: str = "", due_date: str = "") -> dict:
    """Change status, next action or due date on a pipeline row (write).

    Empty arguments are left unchanged. Get ids from data_export or the
    id returned by application_log.
    """
    user = current_user()
    row = store.get(user, application_id)
    if row is None:
        return {"error": "no such application"}
    if status and status not in STATUSES:
        return {"error": f"status must be one of {STATUSES}"}
    for key, value in (("status", status), ("next_action", next_action),
                       ("due_date", due_date)):
        if value:
            row[key] = value
    store.put(user, "application", row, record_id=application_id)
    reminders = autopilot.on_application(user, application_id, row)
    return {"updated": True, "reminders_created": len(reminders)}


@mcp.tool
def job_search(companies: list[str] | None = None,
               keywords: list[str] | None = None,
               locations: list[str] | None = None, max_age_days: int = 7,
               include_seen: bool = False, today: str = "") -> dict:
    """Find fresh roles on companies' official public job boards
    (Greenhouse, Lever, Ashby). Read-only; it never applies.

    companies: "greenhouse:acme", "lever:globex", "ashby:initech", or a
    bare board name to try on all three; the profile's target_companies
    are added. keywords: words the title must contain (default: the target
    role). locations: e.g. "remote", "seattle" (default: the profile's).
    Every result has a provable posting date within max_age_days; the
    profile's excluded companies and dealbreakers filter, its wants rank.
    Only roles not shown before are returned, so "nothing new" is normal.
    For LinkedIn, give the person a link; never automate it.
    """
    now = date.fromisoformat(today) if today else None
    return jobs.job_search(current_user(), companies, keywords, locations,
                           max_age_days, include_seen, now)


@mcp.tool
def recruiter_find(company: str, role: str = "", location: str = "") -> dict:
    """Search links for finding a recruiter or hiring manager at a
    company (LinkedIn people search and web searches). Links only: the
    person opens them and decides whom to contact."""
    return jobs.recruiter_find(company, role, location)


@mcp.tool
def jd_analyze(text: str, title: str = "", company: str = "",
               remember: bool = True) -> dict:
    """Read a job posting the person pasted: what the role is, level read,
    years asked, pay read (flagged if below their floor), sponsorship
    read, why bother, fit points and gap points from their confirmed
    facts, dealbreakers it breaks, and a verdict. remember=true keeps a
    short record (title, company, skills asked; never the full text) for
    skill_gap_evidence."""
    return jobs.jd_analyze(current_user(), text, title, company, remember)


@mcp.tool
def sponsorship_verify(company: str, role: str = "", posting_text: str = "",
                       application_id: str = "", save: bool = False) -> dict:
    """What's known about visa sponsorship for one role: yes, no or
    unstated, with confidence and the evidence quoted (posting sentences,
    and what the person logged on their applications), plus links to
    public H-1B filing data as education. Never assumes yes. save=true
    with application_id records an explicit yes or no from the posting on
    that application (write action). Ask about sponsorship only when
    matters_for_you is true or the person raises it."""
    return visa_sponsor.verify(current_user(), company, role, posting_text,
                               application_id, save)


@mcp.tool
def skill_gap_evidence(role_keyword: str = "", window_days: int = 90,
                       min_postings: int = 5) -> dict:
    """Skill gaps from evidence, not keyword guesses: across the postings
    this person analyzed (optionally only titles containing
    role_keyword), how often each skill is asked for (required or
    preferred), how well their confirmed facts prove it (proven, claimed,
    none), and the gap cost. Also the reply rate per resume version from
    their own applications, once there's enough data. Refuses to conclude
    from fewer than min_postings postings."""
    return evidence.skill_gap_evidence(current_user(), role_keyword,
                                       window_days, min_postings)


@mcp.tool
def ats_keyword_check(posting_text: str, resume_text: str = "",
                      resume_label: str = "") -> dict:
    """The posting's skill keywords against the resume (the latest
    imported one unless given): covered, missing but true (backed by a
    confirmed fact or the profile, so safe to add), and missing and a gap
    (never add these)."""
    return ats.ats_keyword_check(current_user(), posting_text, resume_text,
                                 resume_label)


@mcp.tool
def resume_tailor(posting_text: str, edits: list[dict], save_as: str = "",
                  company: str = "") -> dict:
    """Check tailored resume lines for one posting before the person uses
    them. You write each line; the server only lets through what the
    person's confirmed facts support. edits: [{"line": "...",
    "fact_ids": ["..."]}], each line naming the confirmed facts it rests
    on (from fact_add or profile_get). Blocks lines with numbers no cited
    fact holds, verbs bigger than the person's part, work from two jobs
    merged into one claim, honest gaps, or posting keywords the facts
    don't back. save_as: a label to save accepted lines as a resume
    version (write action); log applications with it as resume_label.
    Comes with check, the response_check result."""
    user = current_user()
    result = tailor.resume_tailor(user, posting_text, edits, save_as,
                                  company)
    if result["accepted"]:
        result["check"] = conduct.check(
            user, "\n".join(a["line"] for a in result["accepted"]),
            "resume")
    return result


@mcp.tool
def ats_profile_check(posting_text: str = "", posting_url: str = "",
                      resume_text: str = "", resume_label: str = "") -> dict:
    """Before applying: which tracking system the posting uses (from its
    link), what in the resume its parser may lose (tables, columns, icons,
    mixed dates, missing headings or email), the knock-out questions in
    the posting (authorization, location, years, degree, clearance) and
    whether an answer is on file, platform quirks, and a verdict: ready,
    fix_first or knockout_risk. Uses the latest imported resume unless
    resume_text or resume_label is given."""
    return ats.ats_profile_check(current_user(), posting_text, posting_url,
                                 resume_text, resume_label)


@mcp.tool
def watch_create(kind: str, companies: list[str] | None = None,
                 keywords: list[str] | None = None,
                 locations: list[str] | None = None, max_age_days: int = 7,
                 cadence: str = "daily") -> dict:
    """Keep an eye on something between chats (write action). kind:
    new_postings (uses companies, keywords, locations like job_search),
    assessment_expiry, follow_up_due or deadline. cadence: daily or
    weekly. Findings wait in the outbox for digest_get. Watches never
    apply, post or message anyone."""
    query = {"companies": companies, "keywords": keywords,
             "locations": locations, "max_age_days": max_age_days}
    return watch.watch_create(current_user(), kind,
                              {k: v for k, v in query.items() if v}, cadence)


@mcp.tool
def watches(remove_id: str = "") -> dict:
    """List the person's watches. remove_id removes one first (write
    action)."""
    return watch.watches(current_user(), remove_id)


@mcp.tool
def digest_get(today: str = "") -> dict:
    """What the watches found since the last chat: runs any watch that's
    due, then returns unread outbox items once. Silent when nothing is
    new. Call at the start of a session, after journey_state."""
    now = date.fromisoformat(today) if today else None
    return watch.digest_get(current_user(), now)


@mcp.tool
def pipeline_digest(today: str = "") -> dict:
    """Today's to-do list for the job search.

    Returns counts by status, overdue actions and actions due within three
    days. today: YYYY-MM-DD, defaults to the server's date.
    """
    now = date.fromisoformat(today) if today else date.today()
    rows = store.list_kind(current_user(), "application")
    counts = {name: 0 for name in STATUSES}
    overdue, soon = [], []
    for row in rows:
        counts[row["status"]] += 1
        if not row["due_date"] or row["status"] in ("rejected",
                                                    "withdrawn"):
            continue
        due = date.fromisoformat(row["due_date"])
        item = {"company": row["company"], "next": row["next_action"],
                "due": row["due_date"]}
        if due < now:
            overdue.append(item)
        elif due <= now + timedelta(days=3):
            soon.append(item)
    result = {"counts": counts, "overdue": overdue,
              "due_within_3_days": soon}
    dealbreakers = " ".join(journey.profile(current_user())
                            .get("dealbreakers", [])).lower()
    if "sponsor" in dealbreakers:
        live = [r for r in rows if r["status"] not in ("rejected",
                                                       "withdrawn")]
        result["sponsorship"] = {
            "unknown": [r["company"] for r in live
                        if r.get("sponsorship", "unknown") == "unknown"],
            "says_no": [r["company"] for r in live
                        if r.get("sponsorship") == "no"],
            "do": "Ask about sponsorship once, early, as a plain fact. "
                  "This is education, not immigration advice."}
    return result


@mcp.tool
def runway_calc(last_working_day: str, payroll_end: str,
                grace_days: int = 0, today: str = "") -> dict:
    """Key dates after a job loss: pay left, grace period, hard deadline.

    Dates are YYYY-MM-DD. If the user's visa or work permit gives a grace
    period after employment ends, pass its length as grace_days (e.g. 60
    for a US H-1B); otherwise leave it at 0. Not legal advice: tell the
    user to confirm visa timelines with an immigration professional.
    """
    now = date.fromisoformat(today) if today else date.today()
    last_day = date.fromisoformat(last_working_day)
    pay_end = date.fromisoformat(payroll_end)
    result = {
        "last_working_day": str(last_day),
        "payroll_end": str(pay_end),
        "days_of_pay_left": max((pay_end - now).days, 0),
    }
    anchor = pay_end
    if grace_days:
        grace_end = anchor + timedelta(days=grace_days)
        result["grace_period_end"] = str(grace_end)
        result["days_until_grace_ends"] = (grace_end - now).days
        anchor = grace_end
    result["hard_deadline"] = str(anchor)
    result["days_to_hard_deadline"] = (anchor - now).days
    holiday_start = date(anchor.year if anchor.month > 1 else anchor.year - 1,
                         12, 20)
    result["note"] = ("Hiring slows after about "
                      f"{holiday_start:%b %d}; front-load applications.")
    result["disclaimer"] = "Confirm immigration timelines with an attorney."
    return result


@mcp.tool
def deadline_add(title: str, best_case: str, conservative: str,
                 why: str = "") -> dict:
    """Save a deadline with two dates (write action): best_case and
    conservative (YYYY-MM-DD, the conservative one no later). Plans use
    the conservative date. Within 60 days, journey_state turns fast-track
    on. For visa dates, say it's education and to confirm with an
    immigration attorney."""
    return deadlines.deadline_add(current_user(), title, best_case,
                                  conservative, why)


@mcp.tool
def ground_rules(accept: bool = False) -> dict:
    """Privacy, terms and how Career Copilot talks, in plain words. Call
    first with a new person. accept=True records that they agreed to the
    current version (write action); only pass it after they say yes.
    """
    return conduct.ground_rules(current_user(), accept)


@mcp.tool
def response_check(text: str, kind: str = "chat") -> dict:
    """Check text before the person reads, sends or relies on it.

    kind: chat, plan, resume, message, cover_letter or linkedin. Flags
    insults, profanity, promised outcomes, biased wording, personal traits
    in things they send, missing education-not-advice notes, and numbers
    not backed by a confirmed fact. ok is false while anything must be
    fixed; rewrite and check again.
    """
    return conduct.check(current_user(), text, kind)


@mcp.tool
def data_export() -> dict:
    """Export every record stored for this user, grouped by kind."""
    return store.export_all(current_user())


@mcp.tool
def data_mirror(save_local: bool = True) -> dict:
    """Everything stored about the person as one readable Markdown page,
    with confirmed and unsure labels. On their own computer it's also
    saved as ~/CareerCopilot/my-data.md (saved_to). Show it as a document
    or summarise it; don't paste it all."""
    text = store.markdown(current_user())
    result = {"markdown": text}
    if save_local and STDIO:
        path = HOME_DIR / "my-data.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        result["saved_to"] = str(path)
    return result


@mcp.tool
def data_delete(confirm: bool = False) -> dict:
    """Permanently delete all of this user's records (write action).

    Requires confirm=True. Ask the user to confirm in plain words first.
    """
    if not confirm:
        return {"deleted": False, "note": "Pass confirm=true to proceed."}
    user = current_user()
    insights.forget(user)
    return {"deleted": store.delete_all(user)}


@mcp.tool
def feedback(tool: str, helpful: bool, reason: str = "",
             missing_role: str = "") -> dict:
    """Tell Career Copilot whether a tool's answer helped, so it improves.

    Offer this after a substantial answer: "Was that useful?". reason: one
    of helpful, wrong, missing_info, confusing, too_generic,
    not_my_country, missing_role. missing_role: a role the user wanted that
    wasn't in the catalogue (job title only, never a name or employer).
    Only anonymous counts are kept, never free text.
    """
    if reason and reason not in insights.FEEDBACK_REASONS:
        return {"error": f"reason must be one of {insights.FEEDBACK_REASONS}"}
    user = current_user()
    insights.record(f"feedback:{reason or 'unspecified'}", tool, user,
                    ok=helpful)
    if missing_role:
        insights.record("unmet_role", missing_role, user, ok=False)
    return {"thanks": True,
            "privacy": "Stored as an anonymous count; no text is kept."}


@mcp.tool
def report_issue(error_code: str, tool_name: str = "", ref: str = "",
                 client_hint: str = "") -> dict:
    """Look up an error from Career Copilot and say what to do next.

    Call this when a Career Copilot tool returns an error. error_code: the
    code in brackets at the start of the error (e.g. INTERNAL_ERROR), or
    the error text itself. tool_name: the tool that failed. ref: the
    reference in an INTERNAL_ERROR, so the owner can find it in the log.
    client_hint: the assistant app, e.g. "Claude desktop". Never pass
    resume text, messages or personal details. Only anonymous counts of
    the code, tool and app family are kept.
    """
    code = errors.lookup(error_code)
    tool = tool_name if re.fullmatch(r"[a-z_]{1,40}", tool_name or "") \
        else "other"
    user = current_user()
    insights.record(f"issue:{code or 'unknown'}", tool, user, ok=False)
    insights.record("issue_client", errors.client_family(client_hint), user,
                    ok=False)
    safe_ref = ref if re.fullmatch(r"[0-9a-f]{6}", ref or "") else ""
    if safe_ref:
        logger.warning(f"issue reported: {code or 'unknown'} {tool} "
                       f"(ref {safe_ref})")
    if not code:
        return {"known": False, "codes": sorted(errors.CODES),
                "say": "I don't recognise that error. Tell the owner what "
                       "you asked and what you saw; try another step for "
                       "now."}
    meaning, retry, fix = errors.CODES[code]
    return {"known": True, "code": code, "meaning": meaning,
            "retry": retry, "what_to_do": fix,
            "ref": safe_ref or None,
            "say": fix if not retry else "That was a server hiccup. " + fix}


# ----------------------------------------------------------------- coach

@mcp.tool
def daily_step(energy: str = "medium", mood: str = "",
               today: str = "") -> dict:
    """The ONE thing for the user to do today: call at the start of every
    session.

    energy: low, medium or high (ask the user). mood: optional, in their
    words. Picks what's due first, otherwise a tiny step toward their
    goals sized to their energy, and returns their momentum (streak with
    one rest day allowed). If the mood signals crisis, returns support
    resources instead of a task.
    """
    now = date.fromisoformat(today) if today else None
    return coach.daily_step(current_user(), energy, mood, now)


@mcp.tool
def step_done(note: str = "", today: str = "") -> dict:
    """Mark today's step done (write action) and celebrate it. note: what
    they did, in a few words."""
    now = date.fromisoformat(today) if today else None
    return coach.step_done(current_user(), note, now)


@mcp.tool
def life_compass(question: int = 0, answer: str = "",
                 save_as: str = "") -> dict:
    """Reflection questions for people who don't know what they want yet,
    asked one at a time. Call with no arguments for the next question.
    After they answer, call again with question (its number) and answer
    to save it (write action). save_as: "want" or "dealbreaker" when the
    answer is a clear want or hard no, so it goes on the profile too."""
    return journey.life_compass(current_user(), question, answer, save_as)


@mcp.tool
def where_to_move(target_role: str, country: str = "",
                  priorities: list[str] | None = None,
                  open_to_abroad: bool = False) -> dict:
    """Recommend cities to move to for a role, if moving would help growth.

    country: where they live now (e.g. "US", "India"). priorities: any of
    low_cost, big_market, stay_in_country, english. open_to_abroad: include
    other countries. Returns ranked hubs with reasons, a remote-first
    option and cautions (visa, cost of living). Education, not advice.
    """
    result = places.where_to_move(target_role, country, priorities,
                                  open_to_abroad)
    if "error" in result:
        note_miss("unmet_role", target_role)
    return result


@mcp.tool
def dashboard(save_local: bool = True, today: str = "") -> dict:
    """Build the user's visual dashboard: Today (one step, momentum ring,
    what's due), Pipeline, Prep, Money and Direction, as one HTML file.

    Show the returned html to the user as an artifact titled "Career
    Copilot". When Career Copilot runs on the user's own computer, the file
    is also saved there (saved_to) so they can open and customise it.
    Re-run it to refresh.
    """
    now = date.fromisoformat(today) if today else None
    html = dash.render(dash.build_data(current_user(), now))
    result = {"html": html,
              "show_as": "an HTML artifact titled 'Career Copilot'",
              "customize": "Colours are CSS variables at the top of the "
                           "file; SHOW_TABS near the bottom picks the tabs."}
    if save_local and STDIO:
        result["saved_to"] = dash.save_local(html)
    return result


@mcp.resource("ui://career-copilot/dashboard", mime_type="text/html")
def dashboard_view() -> str:
    """The user's dashboard as HTML, for hosts that render HTML
    resources."""
    return dash.render(dash.build_data(current_user()))


@mcp.tool
def companions(need: str = "") -> dict:
    """Which of the user's other connectors feed Career Copilot, what to
    read from them, and which tool to hand it to. Career Copilot never
    logs in anywhere itself.

    need: email, calendar, meetings, finance, resume, notes or design
    (empty for all).
    """
    from copilot.knowledge.companions import COMPANIONS, RULES
    if need and need not in COMPANIONS:
        return {"error": "Unknown need.", "needs": sorted(COMPANIONS)}
    picked = {need: COMPANIONS[need]} if need else COMPANIONS
    return {"companions": picked, "rules": RULES}


@mcp.tool
def outreach_review(channel: str, to: str = "", subject: str = "",
                    body: str = "", thread_id: str = "", when: str = "",
                    event_id: str = "") -> dict:
    """Step 1 before anything leaves the chat: an email, a calendar event
    or cancellation, or a LinkedIn post or profile change. channel:
    email, calendar_event, calendar_cancel, linkedin_post or
    linkedin_profile. Checks the exact text (response_check, plus never
    mentioning a performance plan, urgency or a visa deadline). If it
    passes, returns an approval_id for this exact text and show_user:
    show it word for word and ask "Send it?". Stores nothing."""
    return outreach.review(current_user(), channel, to, subject, body,
                           thread_id, when, event_id)


@mcp.tool
def outreach_approve(approval_id: str, channel: str, consent: bool,
                     to: str = "", subject: str = "", body: str = "",
                     thread_id: str = "", when: str = "",
                     event_id: str = "") -> dict:
    """Step 2, only after the person said yes to that exact message:
    consent=True with the same fields as outreach_review. Refused if
    anything changed since review or the approval expired (30 minutes).
    When approved, send it once with the person's own connector as
    send_with says, then check as verify says before saying it's done.
    Career Copilot never sends anything itself and keeps no copy."""
    return outreach.approve(current_user(), approval_id, channel, to,
                            subject, body, thread_id, when, event_id,
                            consent)


# -------------------------------------------------------------- persona

@mcp.tool
def persona_publish(accept: bool = False, preview_id: str = "",
                    hide: list[str] | None = None) -> dict:
    """The person's anonymous persona: verified skills and confirmed work
    facts only (employer names, emails, links and phone numbers removed;
    never a name, photo, age, gender, salary or work authorization).
    accept=false (default) returns the exact preview and a preview_id;
    hide: ids of evidence lines to leave out. Show the preview word for
    word. Only after their yes, call with accept=true and that preview_id
    to publish it, so signed-in people searching for candidates can find
    it (write action). Private until then."""
    return persona.publish(current_user(), accept, preview_id, hide)


@mcp.tool
def persona_unpublish(delete: bool = False) -> dict:
    """Take the person's persona out of search at once (write action).
    delete=true removes it completely."""
    return persona.unpublish(current_user(), delete)


@mcp.tool
def persona_search(posting_text: str, title: str = "",
                   must_have: list[str] | None = None,
                   nice_to_have: list[str] | None = None,
                   location: str = "") -> dict:
    """For someone hiring: the top 5 published anonymous personas for a
    job. posting_text: the posting the recruiter pasted (from a job link
    they opened). must_have filters out personas that don't prove it;
    nice_to_have and the posting's skills rank them; location keeps
    personas there or remote. Ranked by verified evidence. Results carry
    skills and proof lines only: no names, contacts or salary. Never
    contacts anyone."""
    return recruiter.search(current_user(), posting_text, title, must_have,
                            nice_to_have, location)


@mcp.tool
def persona_chat(persona_id: str, question: str) -> dict:
    """Ask a published persona about its work, like a short screen.
    Answers come only from the persona's verified evidence; identity and
    salary questions are refused. Answer from answer_from only."""
    return recruiter.chat(current_user(), persona_id, question)


@mcp.tool
def persona_intro(persona_id: str, company: str, role: str,
                  message: str) -> dict:
    """For someone hiring: ask to meet a persona (write action). company
    and role say what it's for; message is checked first. Neither side's
    identity is shared; that happens only if both confirm with
    identity_reveal. Never contacts the person any other way."""
    return intro.request(current_user(), persona_id, company, role, message)


@mcp.tool
def persona_intros() -> dict:
    """Introduction requests the person's persona received (company,
    role, message, how many screening questions came first) and ones
    they sent, with who has confirmed."""
    return intro.inbox(current_user())


@mcp.tool
def identity_reveal(intro_id: str, confirm: bool, share: str = "") -> dict:
    """Either side of an introduction confirms (write action). confirm=true
    with share: the contact they choose to give (e.g. a name and email),
    only after they said yes. confirm=false declines. Nothing is shared
    until both sides confirm; then each sees what the other shared, and
    the persona notes that the reveal came after the merit screen."""
    return intro.reveal(current_user(), intro_id, confirm, share)


@mcp.tool
def recruiter_survey(answers: dict[str, str] | None = None,
                     company: str = "", role: str = "") -> dict:
    """For someone hiring: a short, versioned survey on what they see in
    hiring. No answers: returns the current questions; ask one at a time.
    answers: {question id: their words}. company is optional and, if
    given, is shown with their answers in the demand digest (write
    action)."""
    return demand.survey(current_user(), answers, company, role)


@mcp.tool
def demand_digest(direction: str = "") -> dict:
    """What people hiring on Career Copilot asked for in the last 90 days,
    from survey answers and persona searches: each skill per direction
    with how many people said it (each counted once), who (company if
    they gave one) and the sources. Report counts, never 'the market wants'."""
    return demand.digest(direction)


@mcp.tool
def pathway_build(direction: str = "", mode: str = "guided") -> dict:
    """A short path for the direction the person picked, from their
    verified skills and the demand digest; every step cites its reason
    (write action). mode: guided (steps toward the direction) or
    immediate (roles asking for what they already prove, no new
    learning; no direction needed). Never pick the direction for them."""
    return demand.build(current_user(), direction, mode)


@mcp.tool
def pathway_next(done: bool = False) -> dict:
    """The one next step on the person's pathway, with its reason.
    done=true marks the current step done first (write action)."""
    return demand.next_step(current_user(), done)


# ------------------------------------------------------------- guidance

@mcp.tool
def next_steps(goals: list[str] | None = None) -> dict:
    """The user's personalised next actions, based on what they've set up.

    goals: any of job, career_move, finance, future (default: the goals in
    their profile, or all four). Returns the next 3 actions with the tool
    or starter prompt to use, plus what's already done. Use it to keep the
    conversation moving: offer the first action as a question.
    """
    return guide.next_steps(current_user(), goals)


# ------------------------------------------------------- resume & linkedin

@mcp.tool
def resume_import(text: str, label: str) -> dict:
    """Store a previous resume version as pasted text (write action).

    Ask the user for every past resume they have (old jobs, different
    targets) and import each with a label like "2024 backend". Then call
    resume_merge to pull the best bullets from all of them.
    """
    return careers.resume_import(current_user(), text, label)


@mcp.tool
def resume_versions() -> list:
    """List stored resume versions with label, bullet count and date."""
    return careers.resume_versions(current_user())


@mcp.tool
def resume_merge() -> dict:
    """Merge bullets across every stored resume version.

    Deduplicates, scores each bullet (ownership, artifact, scale, result)
    and lists the questions to ask where a part is missing. Confirm facts
    with the user before saving them with experience_add.
    """
    return careers.resume_merge(current_user())


@mcp.tool
def resume_snapshot(text: str = "", label: str = "", note: str = "",
                    from_version: str = "", rendered_file: str = "",
                    parent: str = "",
                    avoid_terms: list[str] | None = None) -> dict:
    """Save a dated snapshot of the resume as it is now (write action).
    Append-only: never replaces an earlier snapshot, so a step back stays
    visible. Give the text, or from_version (an id from resume_versions).
    note: what the person says changed. rendered_file: a path or link to
    the PDF or image of this version, if they have one. parent: the
    snapshot this was built from, when not the latest (a branch).
    avoid_terms: internal team or org nicknames the person says recruiters
    won't know (kept for later snapshots until changed). Returns the
    computed checks (level tags, internal names, numbers no confirmed
    fact holds, a summary that doesn't lead with a number) and any
    regressions: problems an earlier version had fixed that came back."""
    return timeline.snapshot(current_user(), text, label, note,
                             from_version, rendered_file, parent,
                             avoid_terms)


@mcp.tool
def resume_timeline() -> dict:
    """Every resume snapshot in order: date, words, what changed against
    the version it was built from, branches, and problems that came
    back."""
    return timeline.timeline(current_user())


@mcp.tool
def resume_diff(a: str = "", b: str = "") -> dict:
    """Compare two resume snapshots by id or label (default: the first
    and the latest): bullets added, removed and reworded, the word-count
    change, and each check before and after. Computed from saved text."""
    return timeline.diff(current_user(), a, b)


@mcp.tool
def resume_proof(a: str = "", b: str = "") -> dict:
    """A Markdown proof of how the resume improved: dated timeline, a
    before and after table, and the final version appended. Show the
    markdown as a document. Comes with check, the response_check result
    for the final resume; fix what it flags before the person shares it."""
    user = current_user()
    result = timeline.proof(user, a, b)
    if "markdown" in result:
        final = result["markdown"].split("## Final resume", 1)[1]
        result["check"] = conduct.check(user, final, "resume")
    return result


@mcp.tool
def resume_sections(level: str = "", target_role: str = "",
                    years: int = 0) -> dict:
    """Which resume sections to include, in what order, and where to focus.

    level: junior, mid, senior or staff (or pass years of experience).
    target_role: e.g. "backend", "ML engineer"; adds the keywords to cover.
    """
    return careers.resume_sections(level, target_role, years)


@mcp.tool
def contribution_check(bullet: str) -> dict:
    """Check one work-contribution bullet against the strong-bullet formula.

    Returns which parts it has (ownership verb, artifact, scale, measurable
    result), what's missing, and the exact questions to ask the user to
    fill the gaps. Never fill a gap with an invented number.
    """
    return careers.contribution_check(bullet)


@mcp.tool
def contribution_framework() -> dict:
    """The formula for strong work-contribution bullets, with weak vs
    strong examples. Use it to coach the user while drafting."""
    from copilot.knowledge.careers import CONTRIBUTION_FRAMEWORK
    return CONTRIBUTION_FRAMEWORK


@mcp.tool
def linkedin_review(profile_text: str, target_role: str) -> dict:
    """Review a LinkedIn profile the user pasted against a target role.

    profile_text: headline, About and Experience text, or the text of
    LinkedIn's "Save to PDF" export. This tool never logs in to or scrapes
    LinkedIn. Returns missing keywords and concrete fixes.
    """
    result = careers.linkedin_review(profile_text, target_role)
    if "error" in result:
        note_miss("unmet_role", target_role)
    return result


# --------------------------------------------------------- roles & skills

@mcp.tool
def role_match(skills: list[str], years: int = 0) -> dict:
    """Rank the roles a user is best suited for from their skills.

    skills: e.g. ["python", "aws", "kafka", "sql"]. Returns the top fits
    with matched skills and the core skills each role still needs.
    """
    return careers.role_match(skills, years)


@mcp.tool
def skills_gap(target_role: str, level: str = "",
               skills: list[str] | None = None, years: int = 0) -> dict:
    """What a user needs for a target role and level: missing skills, what
    the interview loop tests, level expectations and the levers that move
    pay. Roles span engineering, product, data, design, project
    management, marketing, sales, customer success, operations, finance
    and HR (see the copilot://roles resource)."""
    result = careers.skills_gap(target_role, level, skills, years)
    if "error" in result:
        note_miss("unmet_role", target_role)
    return result


@mcp.tool
def career_move(current_role: str, target_role: str,
                skills: list[str] | None = None, years: int = 0) -> dict:
    """Plan a move into a different role or field.

    Returns how far the move is (adjacent, same family or full career
    change), skills that transfer, skills to build, stepping-stone roles,
    a rough timeline and concrete steps. Pair with study_plan or nudge_add
    to schedule the learning.
    """
    result = careers.career_move(current_role, target_role, skills, years)
    if "error" in result:
        note_miss("unmet_role", target_role)
    elif not careers.resolve_role(current_role):
        note_miss("unmet_role", current_role)
    return result


# ----------------------------------------------------------- interview prep

@mcp.tool
def coding_pattern(query: str) -> dict:
    """Identify the coding pattern for a problem, or show one pattern.

    query: a pattern name ("sliding window", "dp") or a problem
    description ("longest substring without repeating characters").
    Returns the mental model, recognition signals, template, common
    mistakes and how to explain the approach out loud.
    """
    result = prep.coding_pattern(query)
    if result["match"] == "none":
        note_miss("unmet_pattern", query)
    return result


@mcp.tool
def system_design(topic: str = "framework") -> dict:
    """System design mental models.

    topic="framework" returns the 7-step interview framework with timings.
    A component name (cache, queue, cdn, load_balancer, nosql, kafka, ...)
    returns when to use it, when not to, the trade-off, a likely interview
    question and common mistakes.
    """
    result = prep.system_design(topic)
    if "error" in result:
        note_miss("unmet_design_topic", topic)
    return result


@mcp.tool
def study_plan(start: str, interview_date: str, hours_per_day: float = 2.0,
               save_as_nudges: bool = False, loop_format: str = "") -> dict:
    """Build a day-by-day prep schedule up to an interview (YYYY-MM-DD).

    loop_format shapes the days: big_tech_algorithmic (default: coding
    heavy), values_heavy (stories every other day), practical (applied
    coding and design), enterprise, startup, or non_technical (work
    sample, stories, case). Ends with mocks and rest. save_as_nudges=True
    stores each day as a reminder (write action).
    """
    result = prep.study_plan(start, interview_date, hours_per_day,
                             loop_format)
    if save_as_nudges and "plan" in result:
        result.update(nudges.plan_to_nudges(current_user(), result["plan"]))
    return result


@mcp.tool
def interview_questions(round: str = "", likely_only: bool = False) -> dict:
    """Interview question bank with why they ask and how to answer.

    round: recruiter, hiring_manager, technical, resume_defense, closing
    (empty for all, plus loop formats by company type).
    """
    return prep.interview_questions(round, likely_only)


@mcp.tool
def story_add(title: str, situation: str, task: str, action: str,
              result: str, themes: list[str] | None = None) -> dict:
    """Save a behavioural story (situation, task, action, result) to the
    story bank (write action). Themes are detected automatically."""
    return prep.story_add(current_user(), title, situation, task, action,
                          result, themes)


@mcp.tool
def story_match(question: str) -> dict:
    """Pick the best stories from the bank for an interview question, and
    list themes the bank doesn't cover yet."""
    return prep.story_match(current_user(), question)


@mcp.tool
def prep_checklist() -> dict:
    """The interview prep checklist: story bank, resume defense, skills
    practice, company prep, mock loops."""
    return prep.prep_checklist()


@mcp.tool
def story_coverage() -> dict:
    """The story bank as a grid: for each interview competency (ownership,
    conflict, failure, ambiguity, influence, leadership, impact, customer,
    speed), the stories that cover it and how strong each is (a number,
    clear ownership, a result, enough detail). Returns the gaps and the
    one story to write or strengthen next. Flags story numbers that aren't
    in any confirmed fact."""
    return prep.story_coverage(current_user())


@mcp.tool
def loop_round_log(company: str, round_n: int, round_format: str,
                   req_id: str = "", role: str = "", round_date: str = "",
                   panel: list[dict] | None = None,
                   questions: list[dict] | None = None,
                   feedback: list[dict] | None = None,
                   apply: bool = False) -> dict:
    """Log one interview round, so the next round builds on it.

    round_format: recruiter, hiring_manager, coding, system_design,
    behavioral, bar_raiser, take_home, panel or team_match. req_id: the
    requisition number (ask for it). panel: [{role, focus_area}], never
    names. questions: [{text, competency, story_id, self_rating 1-5,
    follow_ups}]. feedback: [{text, source: recruiter_said,
    interviewer_said or self_read}]. apply=false previews; apply=true
    saves (write action).
    """
    return loops.round_log(current_user(), company, round_n, round_format,
                           req_id, role, round_date, panel, questions,
                           feedback, apply)


@mcp.tool
def loop_next_round_prep(loop_id: str, next_format: str = "",
                         known_panel: list[dict] | None = None,
                         calendar_events: list[dict] | None = None) -> dict:
    """Prepare the next round of a loop: competencies already covered and
    still open, which story to bring for each (and whether this panel may
    have heard it), weak spots from low self-ratings or real feedback, and
    one thing to do today. loop_id comes from loop_round_log.
    calendar_events: [{subject, start, organizer}] from the person's own
    calendar connector, to confirm the round is really booked."""
    return loops.next_round_prep(current_user(), loop_id, next_format,
                                 known_panel, calendar_events)


@mcp.tool
def cover_letter_draft(company: str, role: str, posting_text: str = "",
                       me: str = "", voice: str = "") -> dict:
    """A short cover letter from the person's confirmed facts only: the
    two that best match the posting, in their own words. voice: plain,
    warm or formal (default: the profile's). Comes with check, the
    response_check result; fix anything flagged before showing it."""
    user = current_user()
    voice = voice or journey.profile(user).get("voice", "plain")
    draft = prep.cover_letter_draft(user, company, role, posting_text, me,
                                    voice)
    if "body" in draft:
        draft["check"] = conduct.check(user, draft["body"], "cover_letter")
    return draft


@mcp.tool
def lessons(add: str = "", loop_id: str = "") -> dict:
    """The person's lessons from interviews and searches, newest first.
    add: a lesson in their own words, e.g. "Lead with the number" (write
    action); loop_id links it to a loop. Next-round prep shows the latest
    three."""
    return loops.lessons(current_user(), add, loop_id)


@mcp.tool
def message_draft(kind: str, company: str = "", role: str = "",
                  name: str = "", detail: str = "", me: str = "",
                  voice: str = "") -> dict:
    """Draft a job-search message for the user to send themselves.

    kind: thank_you, follow_up, assessment_extension, recruiter_reply,
    level_question, referral_request, offer_negotiation, withdraw.
    voice: plain (default), warm or formal; empty uses the profile's
    voice (save it with profile_save(voice=...)). The draft comes with
    check, the response_check result: fix anything it flags before
    showing it.
    """
    voice = voice or journey.profile(current_user()).get("voice", "plain")
    draft = prep.message_draft(kind, company, role, name, detail, me, voice)
    if "body" in draft:
        draft["check"] = conduct.check(
            current_user(), f"{draft['subject']}\n{draft['body']}",
            "message")
    return draft


# ---------------------------------------------------------- inbox & calendar

@mcp.tool
def inbox_triage(emails: list[dict], apply: bool = False,
                 today: str = "") -> dict:
    """Turn job-search emails into pipeline updates and reminders.

    emails: [{from, subject, date, snippet}], taken from the user's own
    Gmail/Outlook connector or pasted. Detects applications, rejections,
    interview invites, assessments (with expiry), offers and recruiter
    outreach. apply=false proposes changes; after the user agrees, call
    with apply=true. A rejection closes an application only when its role
    or req id matches; otherwise it comes back as a "confirm" proposal for
    the person to settle (apply skips it). Email text is never stored.
    today: the user's local date (YYYY-MM-DD), so reminders land on their
    days.
    """
    now = date.fromisoformat(today) if today else None
    return autopilot.triage_emails(current_user(), emails, apply, now)


@mcp.tool
def calendar_interviews(events: list[dict], apply: bool = False,
                        today: str = "") -> dict:
    """Find interviews in calendar events (Outlook, Google, Zoom) and set up
    prep, thank-you and follow-up reminders.

    events: [{subject, start, organizer, join_url}]. apply=true updates the
    matching applications and creates the reminders. today: the user's
    local date (YYYY-MM-DD), so reminders land on their days.
    """
    now = date.fromisoformat(today) if today else None
    return autopilot.interviews_from_calendar(current_user(), events, apply,
                                              now)


# --------------------------------------------------------- nudges & calendar

@mcp.tool
def nudge_add(title: str, due: str, repeat_days: int = 0,
              note: str = "") -> dict:
    """Add a reminder (write action). due: YYYY-MM-DD. repeat_days: 1 for
    daily, 7 for weekly, 0 for once."""
    return nudges.nudge_add(current_user(), title, due, repeat_days, note)


@mcp.tool
def nudges_due(today: str = "", within_days: int = 2) -> dict:
    """What's overdue, due today and coming up: reminders plus application
    deadlines. Call this at the start of every session."""
    now = date.fromisoformat(today) if today else None
    return nudges.nudges_due(current_user(), now, within_days)


@mcp.tool
def nudge_done(nudge_id: str, today: str = "") -> dict:
    """Mark a reminder done (write action). Repeating ones roll forward."""
    now = date.fromisoformat(today) if today else None
    return nudges.nudge_done(current_user(), nudge_id, now)


@mcp.tool
def calendar_export() -> str:
    """An .ics calendar of open reminders and application deadlines, with
    alerts. Give it to the user to import into Google, Outlook or Apple
    Calendar so they get real notifications."""
    return nudges.calendar_ics(current_user())


# ---------------------------------------------------------------- finance

@mcp.tool
def finance_account_set(name: str, kind: str, balance: float,
                        as_of: str = "") -> dict:
    """Add or update an account balance (write action).

    kind: cash, brokerage, foreign, retirement, hsa, property, debt, other.
    Debt balances are the amount owed, as a positive number. as_of:
    YYYY-MM-DD of the balance, so stale numbers get flagged.
    """
    return finance.account_set(current_user(), name, kind, balance, as_of)


@mcp.tool
def finance_import(accounts: list[dict],
                   holdings: list[dict] | None = None) -> dict:
    """Load many accounts and holdings at once (write action), e.g. from
    the user's own bank-data connector in this chat.

    accounts: [{name, institution, type, subtype, balance}] where balance
    is a number or {current, available}; Plaid-style types are mapped
    automatically (depository → cash, credit/loan → debt, 401k/IRA →
    retirement, HSA, brokerage). holdings: [{symbol, market_value, type}].
    Account numbers and ids are dropped; never pass logins.
    """
    return finance.finance_import(current_user(), accounts, holdings)


@mcp.tool
def finance_account_remove(name: str) -> dict:
    """Remove an account by name (write action)."""
    return finance.account_remove(current_user(), name)


@mcp.tool
def finance_holding_set(symbol: str, value: float, kind: str = "stock",
                        employer: bool = False) -> dict:
    """Add or update an investment holding's current value (write action).

    kind: "stock" for a single company, "fund" for an ETF or mutual fund.
    employer=True flags stock in the company the user works for.
    """
    return finance.holding_set(current_user(), symbol, value, kind, employer)


@mcp.tool
def finance_budget_set(category: str, current: float, target: float) -> dict:
    """Set a monthly budget line: current spend and target (write action)."""
    return finance.budget_set(current_user(), category, current, target)


@mcp.tool
def finance_dashboard(monthly_burn: float = 0.0, today: str = "") -> dict:
    """The personal finance dashboard.

    Net worth; accessible vs locked vs illiquid money; runway in months on
    cash only and on all accessible money; stale balances; concentration
    flags. monthly_burn defaults to the budget's current total.
    """
    now = date.fromisoformat(today) if today else None
    return finance.dashboard(current_user(), monthly_burn, now)


@mcp.tool
def finance_budget_review() -> dict:
    """Budget now vs target: monthly savings, biggest cuts first, and how
    much runway the cuts buy."""
    return finance.budget_review(current_user())


@mcp.tool
def portfolio_check() -> dict:
    """Check holdings for single-stock and employer-stock concentration and
    the share held in diversified funds. Educational, not advice."""
    return finance.portfolio_check(current_user())


@mcp.tool
def layoff_fund_plan(monthly_core_spend: float, current_fund: float,
                     monthly_saving: float, target_months: int = 6,
                     status_tied_to_job: bool = False) -> dict:
    """How much to save for a layoff, the gap, and months to get there.

    status_tied_to_job=True (e.g. a work visa) raises the target to at
    least 9 months. Pair with layoff_playbook for what to do and when.
    """
    return finance.layoff_fund_plan(monthly_core_spend, current_fund,
                                    monthly_saving, target_months,
                                    status_tied_to_job)


@mcp.tool
def goal_set(name: str, target_amount: float, target_date: str,
             saved: float = 0.0) -> dict:
    """Add or update a savings goal (write action): e.g. emergency fund,
    home deposit, education, a career-change cushion, retirement.
    target_date: YYYY-MM-DD. saved: amount already put aside."""
    return finance.goal_set(current_user(), name, target_amount,
                            target_date, saved)


@mcp.tool
def goals_review(monthly_budget: float = 0.0, today: str = "") -> dict:
    """Every goal's progress and the monthly saving it needs. With
    monthly_budget, says whether the user is on track overall."""
    now = date.fromisoformat(today) if today else None
    return finance.goals_review(current_user(), monthly_budget, now)


@mcp.tool
def future_projection(current_savings: float, monthly_saving: float,
                      years: int, target_amount: float = 0.0) -> dict:
    """Where savings could be after N years at cautious (3%), balanced (5%)
    and growth (7%) returns, also in today's money, and when a target
    would be reached. Illustrative, not a forecast."""
    return finance.future_projection(current_savings, monthly_saving,
                                     years, target_amount)


@mcp.tool
def layoff_playbook() -> dict:
    """What to do before, during and after a layoff, in order: paperwork,
    coverage, spending, applications and tax timing."""
    return {"steps": LAYOFF_PLAYBOOK, "disclaimer": DISCLAIMER}


@mcp.tool
def invest_guide(topic: str = "what_works") -> dict:
    """Evidence-based investing education.

    topic: what_works, order_of_operations, allocation, concentration,
    tax_timing, rebalancing. Educational, not personalised advice.
    """
    guide = INVEST_GUIDES.get(topic)
    if guide is None:
        note_miss("unmet_guide", topic)
        return {"error": "Unknown topic.", "topics": sorted(INVEST_GUIDES)}
    return {**guide, "disclaimer": DISCLAIMER}


# ---------------------------------------------------------------- economy

@mcp.tool
def economy_guide(topic: str = "how_to_use") -> dict:
    """The World Economy OS: how the economy works and reaches prices,
    markets and jobs. topic: supply_demand, money_rates_inflation,
    business_cycle, commodities, markets_link, how_to_use."""
    guide = ECONOMY_GUIDES.get(topic)
    if guide is None:
        note_miss("unmet_guide", topic)
        return {"error": "Unknown topic.", "topics": sorted(ECONOMY_GUIDES)}
    return guide


@mcp.tool
async def economy_indicators(country: str = "USA",
                             indicators: list[str] | None = None) -> dict:
    """Live macro data from the World Bank (last 5 years).

    country: ISO code such as USA, IND, GBR, DEU, or WLD for the world.
    indicators: any of gdp_growth, inflation, unemployment,
    real_interest_rate, current_account, gov_debt (default: all).
    """
    return await economy.indicators(country, indicators)


# -------------------------------------------------------------- resources

@mcp.resource("copilot://rubric")
def rubric() -> str:
    """The ten-check resume rubric used by resume_score."""
    return ("six_second_scan, role_clarity, quantified_impact, ownership, "
            "seniority, thesis, bullet_order, credibility, ats_parse, "
            "density. 10 points each.")


@mcp.resource("copilot://ground-rules")
def ground_rules_text() -> dict:
    """Privacy summary, terms of use and conduct rules, with links to the
    full documents."""
    return {key: value for key, value in
            conduct.ground_rules(current_user()).items()
            if key not in {"accepted", "accepted_on"}}


@mcp.resource("copilot://data-handling")
def data_handling_text() -> dict:
    """What is stored, where, for how long and who can read it, as data.
    The same statement ground_rules shows before anything is saved."""
    return conduct.DATA_HANDLING


@mcp.resource("copilot://pipeline")
def pipeline() -> dict:
    """The user's live application pipeline: every application row with
    status, next action and due date."""
    return {"applications": store.list_kind(current_user(), "application")}


@mcp.resource("copilot://calendar.ics", mime_type="text/calendar")
def calendar() -> str:
    """The user's reminders and application deadlines as an iCalendar
    feed."""
    return nudges.calendar_ics(current_user())


@mcp.resource("copilot://connect")
def connect() -> dict:
    """How to connect Career Copilot to each AI client. Replace URL with
    the server's /mcp endpoint and KEY with the user's API key."""
    from copilot.knowledge.connect import CLIENTS
    return CLIENTS


@mcp.resource("copilot://patterns")
def patterns_index() -> list:
    """Every coding pattern with its one-line recognition signal."""
    from copilot.knowledge.patterns import PATTERNS
    return [{"id": p["id"], "name": p["name"], "signal": p["signal"]}
            for p in PATTERNS]


@mcp.resource("copilot://roles")
def roles_index() -> list:
    """Every role in the catalogue, with its family and core skills."""
    from copilot.knowledge.careers import ROLES
    return [{"id": key, "title": r["title"], "family": r["family"],
             "core_skills": r["core"]} for key, r in ROLES.items()]


# ---------------------------------------------------------------- prompts

@mcp.prompt
def get_started() -> str:
    """Starter chip: guided onboarding for a new user."""
    return ("Welcome me to Career Copilot in one sentence. Call "
            "ground_rules, then journey_state, and follow its next: let me "
            "either tell you what's on my mind or answer a few quick "
            "questions, one at a time. Save each answer as I give it.")


@mcp.prompt
def i_dont_know_what_i_want() -> str:
    """Starter chip: no direction yet."""
    return ("I don't know what I want. Use life_compass: one question at a "
            "time, save each answer, and after a few, offer 2 or 3 "
            "directions I could test.")


@mcp.prompt
def i_know_my_target() -> str:
    """Starter chip: I know the role I want."""
    return ("I know the role I want. Ask for the role, where I want to work, "
            "my pay floor and any hard no's, one at a time. Save them with "
            "profile_save, then give me one step toward applying.")


@mcp.prompt
def find_candidates() -> str:
    """Starter chip, for someone hiring: find candidates for a job."""
    return ("I'm hiring. I'll paste a job posting and say what the role must "
            "have. Use persona_search to find the top 5 anonymous personas, "
            "one line each with its proof, then let me ask one of them a "
            "question with persona_chat.")


@mcp.prompt
def interview_coming_up() -> str:
    """Starter chip: I have an interview coming up."""
    return ("I have an interview coming up. Ask the company, role, date and "
            "format, one at a time. Log it with application_log, then give "
            "me the one prep step that matters most today.")


@mcp.prompt
def daily_checkin() -> str:
    """Starter chip: today's one small step."""
    return ("Check in with me like a friend who believes in me. Ask how my "
            "energy is today (low, medium or high) and, optionally, how I "
            "feel. Call daily_step, offer the one step in a sentence or "
            "two, and if it feels too big, make it smaller. When I say I "
            "did it, call step_done and celebrate.")


@mcp.prompt
def should_i_move() -> str:
    """Starter chip: would moving cities help my career?"""
    return ("Ask where I live, the role I want, and what matters most "
            "(cost, market size, staying in my country, English). Call "
            "where_to_move, explain the top options honestly, including "
            "remote, and the cautions. It's my decision.")


@mcp.prompt
def tour() -> str:
    """Starter chip: a 2-minute guided tour of Career Copilot."""
    return ("Give me a short guided tour of Career Copilot in six stops, "
            "one at a time, waiting for me after each: 1) starting without "
            "a form (journey_state), 2) finding a direction "
            "(direction_options, life_compass), 3) a truthful resume "
            "(fact_conflicts, ownership_check, ats_keyword_check), 4) "
            "search (job_search, jd_analyze, watch_create), 5) interviews "
            "round by round (loop_round_log, loop_next_round_prep, "
            "story_coverage), 6) steadying the ground (deadline_add, "
            "runway_calc, finance_dashboard). Keep each stop under 4 "
            "sentences and end each with a tiny try-it.")


@mcp.prompt
def change_careers() -> str:
    """Starter chip: plan a move into a new role or field."""
    return ("Ask what I do now, what I want to do, and my main skills. Call "
            "career_move, explain what carries over and what to learn, then "
            "offer to schedule the learning with study_plan or nudge_add.")


@mcp.prompt
def plan_my_future() -> str:
    """Starter chip: savings goals and a long-term projection."""
    return ("Ask about my savings goals (emergency fund, home, education, "
            "retirement) with amounts and dates. Save each with goal_set, "
            "call goals_review with my monthly budget, then "
            "future_projection for 10 and 30 years. Explain it simply and "
            "note it's illustrative, not advice.")


@mcp.prompt
def build_my_resume() -> str:
    """Starter chip: build a resume from confirmed facts."""
    return ("Interview me one question at a time about my last two jobs. "
            "Save each fact with experience_add, marking confirmed only "
            "when I state it. Then call resume_build_draft and "
            "resume_score. Never invent a number.")


@mcp.prompt
def i_just_got_laid_off() -> str:
    """Starter chip: layoff fast-track."""
    return ("Ask for my last working day, payroll end date and any visa "
            "grace period. Call runway_calc, then set up a 72-hour plan.")


@mcp.prompt
def import_my_resumes() -> str:
    """Starter chip: collect old resumes and merge the best bullets."""
    return ("Ask me to paste every previous resume I have, one at a time. "
            "Import each with resume_import and a short label. Then call "
            "resume_merge, walk me through the weakest bullets using the "
            "questions it returns, and save confirmed facts with "
            "experience_add.")


@mcp.prompt
def review_my_linkedin() -> str:
    """Starter chip: LinkedIn review for a target role."""
    return ("Ask for my target role, then ask me to paste my LinkedIn "
            "headline, About and Experience (or the 'Save to PDF' text). "
            "Call linkedin_review and rewrite my headline and About with "
            "only facts I confirm.")


@mcp.prompt
def find_my_role() -> str:
    """Starter chip: which roles fit and what to learn for top pay."""
    return ("Ask for my skills and years of experience. Call role_match, "
            "then skills_gap for my best fit at my level, and turn the gaps "
            "into a 4-week learning plan with nudges.")


@mcp.prompt
def plan_my_prep() -> str:
    """Starter chip: interview prep schedule with reminders."""
    return ("Ask for today's date, my interview date and hours per day. "
            "Call study_plan with save_as_nudges=true, then calendar_export "
            "so I can import the reminders into my calendar.")


@mcp.prompt
def money_checkup() -> str:
    """Starter chip: finance dashboard and layoff readiness."""
    return ("Help me enter my accounts with finance_account_set and my "
            "monthly budget with finance_budget_set. Then show "
            "finance_dashboard, layoff_fund_plan and portfolio_check, and "
            "remind me this is education, not advice.")


# ------------------------------------------------------------------- main

def check_auth_config():
    if OAUTH:
        if API_KEYS:
            logger.warning("GitHub sign-in is on, so API keys are ignored.")
        if not os.environ.get("CAREER_COPILOT_PUBLIC_URL") and \
                not os.environ.get("RENDER_EXTERNAL_URL"):
            logger.warning(f"Public URL not set; sign-in redirects go to "
                           f"{PUBLIC_URL}. Set CAREER_COPILOT_PUBLIC_URL.")
        return
    if STDIO or API_KEYS:
        return
    if ALLOW_OPEN:
        logger.warning("CAREER_COPILOT_ALLOW_OPEN=1: no API key required. "
                       "Do not use this in production.")
        return
    logger.error("CAREER_COPILOT_API_KEY is not set. Refusing to start an "
                 "open HTTP server. Set a key, or CAREER_COPILOT_ALLOW_OPEN=1 "
                 "for local testing.")
    sys.exit(1)


def log_startup():
    tools = asyncio.run(mcp.get_tools())
    transport = "stdio" if STDIO else "streamable-http"
    logger.info(f"Career Copilot {VERSION} starting")
    logger.info(f"fastmcp {fastmcp.__version__}, MCP protocol "
                f"{LATEST_PROTOCOL_VERSION}, transport {transport}")
    if not STDIO:
        logger.info(f"MCP endpoint http://{HOST}:{PORT}/mcp, "
                    f"health http://{HOST}:{PORT}/health")
    if insights.ENABLED and not STDIO and not insights.SALT:
        logger.warning("CAREER_COPILOT_INSIGHTS_SALT is not set: set a "
                       "random secret so insight hashes can't be recomputed.")
    logger.info(f"insights {'on' if insights.ENABLED else 'off'} "
                f"(k={insights.K_ANON}), admin endpoint "
                f"{'on' if ADMIN_KEY else 'off'}")
    if STDIO:
        auth = "off (stdio)"
    elif OAUTH:
        invite = f"{len(ALLOWED_GITHUB)} invited" if ALLOWED_GITHUB \
            else "anyone"
        auth = f"GitHub sign-in ({invite})"
    else:
        auth = f"{len(API_KEYS)} key(s)"
    logger.info(f"{len(tools)} tools, auth {auth}, "
                f"storage {_storage_label()}, logs {LOG_DIR}/mcp_server.log")


def _storage_label():
    # Never print DATABASE_URL: it contains the database password.
    return "postgres (DATABASE_URL)" if store.BACKEND.name == "postgres" \
        else f"sqlite files in {store.DATA_DIR}"


def main():
    setup_logging()
    check_auth_config()
    log_startup()
    minutes = os.environ.get("CAREER_COPILOT_WATCH_MINUTES", "")
    if minutes.isdigit() and int(minutes) > 0 and not STDIO:
        watch.start_scheduler(int(minutes))
        logger.info(f"watches run every {minutes} minutes while awake")
    try:
        if STDIO:
            mcp.run(show_banner=False)
        else:
            # No access log: request lines can carry ?key= in the URL.
            mcp.run(transport="http", host=HOST, port=PORT,
                    show_banner=False, uvicorn_config={"access_log": False})
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Career Copilot stopped")


if __name__ == "__main__":
    main()
