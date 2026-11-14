"""Sign in with GitHub, with nothing kept on the server.

The free host wipes its disk on every restart, so sign-in can't depend
on stored state. Everything it needs travels sealed inside the values
the apps already hold:

- an app's registration is sealed into its own client id;
- a sign-in in progress rides in the state sent through GitHub;
- the browser that clicked Allow holds a short-lived cookie, and the
  sign-in only finishes in that browser (so nobody can send a person a
  ready-made GitHub link that quietly signs them in for someone else);
- codes and tokens carry the person's GitHub id and username, sealed.

Sealing uses a key from the environment (CAREER_COPILOT_JWT_KEY), which
survives restarts, so one sign-in keeps working through restarts and
deploys. GitHub's own token is used once to learn who the person is,
then thrown away. Changing the key signs everyone out.
"""
import base64
import hashlib
import hmac
import html
import json
import logging
import secrets
import time
from urllib.parse import urlencode, urlparse

import httpx
from cryptography.fernet import Fernet, InvalidToken
from mcp.server.auth.provider import (AuthorizationCode, AuthorizationParams,
                                      RefreshToken, construct_redirect_uri)
from mcp.server.auth.settings import ClientRegistrationOptions
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from fastmcp.server.auth import AccessToken, OAuthProvider
from fastmcp.server.auth.middleware import RequireAuthMiddleware
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.middleware.bearer_auth import \
    RequireAuthMiddleware as SDKRequireAuth

SCOPE = "read:user"
# What a 401 says. The protocol stays as the MCP spec expects (401,
# error="invalid_token", resource_metadata so the app starts sign-in);
# only the words change, so a person sees what actually happened.
NOT_SIGNED_IN = (
    "[AUTH_REQUIRED] Not signed in yet. Your assistant should now open a "
    "Sign in with GitHub page. If it did and showed an error (for example "
    "invite-only), fix that first: ask the owner to add the GitHub "
    "username it named. Then remove Career Copilot from your assistant, "
    "add it again, and sign in.")
SIGN_IN_EXPIRED = (
    "[AUTH_REQUIRED] This sign-in is no longer valid (it expired, or the "
    "server's sign-in settings changed). Remove Career Copilot from your "
    "assistant, add it again, and sign in with GitHub.")
STATE_SECONDS = 600
CODE_SECONDS = 300
ACCESS_SECONDS = 30 * 24 * 3600
REFRESH_SECONDS = 365 * 24 * 3600
KEPT_METADATA = ("redirect_uris", "grant_types", "response_types",
                 "token_endpoint_auth_method", "scope", "client_name")
COOKIE = "cc_signin_"
# Our sign-in pages must never load inside another site's frame, and the
# links on them must not leak where the person came from.
PAGE_HEADERS = {"X-Frame-Options": "DENY",
                "Content-Security-Policy": "frame-ancestors 'none'",
                "Cache-Control": "no-store",
                "Referrer-Policy": "no-referrer"}
log = logging.getLogger("career_copilot.signin")


class GitHubUnreachable(Exception):
    """GitHub didn't answer, or answered with something unreadable."""


class _Code(AuthorizationCode):
    login: str = ""


class _Refresh(RefreshToken):
    login: str = ""


class SignInRequired(RequireAuthMiddleware):
    """FastMCP's 401 says "the provided bearer token is invalid" even when
    no token was sent, which is every app's normal first request. Tell
    the two cases apart, in words and in the log (never the token)."""

    async def __call__(self, scope, receive, send):
        if isinstance(scope.get("user"), AuthenticatedUser):
            return await super().__call__(scope, receive, send)
        sent = any(k.lower() == b"authorization" and
                   v[:7].lower() == b"bearer "
                   for k, v in scope.get("headers", []))
        log.info("sign-in needed: %s", "token rejected" if sent
                 else "no token sent")
        # The SDK's response shape, without FastMCP's rewording.
        await SDKRequireAuth._send_auth_error(
            self, send, 401, "invalid_token",
            SIGN_IN_EXPIRED if sent else NOT_SIGNED_IN)


def use_clear_messages():
    """FastMCP builds its routes with the class named in fastmcp.server.http;
    point that name at ours before the app is built."""
    import fastmcp.server.http as http
    http.RequireAuthMiddleware = SignInRequired


def _page(title, text, status):
    return HTMLResponse(
        f"<!doctype html><meta charset=utf-8>"
        f"<meta name=viewport content='width=device-width'><title>{title}"
        f"</title><body style='font-family:system-ui;max-width:32rem;"
        f"margin:4rem auto;padding:0 1rem'><h1>{title}</h1><p>{text}</p>"
        f"</body>", status_code=status, headers=PAGE_HEADERS)


class StatelessGitHubProvider(OAuthProvider):
    def __init__(self, *, client_id, client_secret, base_url, key,
                 allowed=None, github_base="https://github.com",
                 github_api="https://api.github.com"):
        super().__init__(
            base_url=base_url,
            client_registration_options=ClientRegistrationOptions(
                enabled=True, default_scopes=[SCOPE]))
        self.gh_id, self.gh_secret = client_id, client_secret
        self.gh_base, self.gh_api = github_base.rstrip("/"), \
            github_api.rstrip("/")
        self.allowed = {a.lower() for a in (allowed or [])}
        digest = hashlib.sha256(f"career-copilot-signin:{key}".encode())
        self._sign_key = digest.digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(
            hashlib.sha256(digest.digest()).digest()))

    # --------------------------------------------------------- sealing
    def _seal(self, kind, body, seconds):
        body = {**body, "k": kind, "x": int(time.time()) + seconds}
        return self._fernet.encrypt(json.dumps(body).encode()).decode()

    def _open(self, kind, token):
        try:
            body = json.loads(self._fernet.decrypt(token.encode()))
        except (InvalidToken, ValueError, TypeError):
            return None
        if body.get("k") != kind or body.get("x", 0) < time.time():
            return None
        return body

    def _sign(self, text):
        mac = hmac.new(self._sign_key, text.encode(), hashlib.sha256)
        return base64.urlsafe_b64encode(mac.digest()[:24]).decode().rstrip("=")

    # ---------------------------------------------------------- clients
    async def register_client(self, client_info: OAuthClientInformationFull):
        meta = {k: v for k, v in client_info.model_dump(mode="json").items()
                if k in KEPT_METADATA and v is not None}
        packed = base64.urlsafe_b64encode(
            json.dumps(meta, separators=(",", ":")).encode()).decode() \
            .rstrip("=")
        client_info.client_id = f"cc1.{packed}.{self._sign(packed)}"
        if client_info.token_endpoint_auth_method != "none":
            client_info.client_secret = self._sign("secret:" +
                                                   client_info.client_id)
        client_info.client_secret_expires_at = None

    async def get_client(self, client_id: str):
        parts = client_id.split(".")
        if len(parts) != 3 or parts[0] != "cc1" or not hmac.compare_digest(
                parts[2], self._sign(parts[1])):
            return None
        try:
            meta = json.loads(base64.urlsafe_b64decode(
                parts[1] + "=" * (-len(parts[1]) % 4)))
        except (ValueError, TypeError):
            return None
        secret = None if meta.get("token_endpoint_auth_method") == "none" \
            else self._sign("secret:" + client_id)
        return OAuthClientInformationFull(client_id=client_id,
                                          client_secret=secret, **meta)

    # ---------------------------------------------------------- sign-in
    # 1. authorize: the app sends the person to our Allow page.
    # 2. Allow page (GET): names the app and where it will send the
    #    sign-in, and gives this browser a one-time cookie.
    # 3. Allow (POST, same cookie): on to GitHub, the cookie's value
    #    sealed in the state.
    # 4. callback: finishes only if this browser has that same cookie.
    # GitHub skips its own consent screen for people who said yes once,
    # so without 2 to 4 anyone could send a person a GitHub link that
    # signs them in to the sender's app (a "confused deputy").
    def _base(self):
        return str(self.base_url).rstrip("/")

    async def authorize(self, client, params: AuthorizationParams) -> str:
        ask = self._seal("ask", {
            "cid": client.client_id, "uri": str(params.redirect_uri),
            "exp_uri": params.redirect_uri_provided_explicitly,
            "pkce": params.code_challenge, "st": params.state,
            "sc": params.scopes or [SCOPE], "res": params.resource,
        }, STATE_SECONDS)
        return f"{self._base()}/auth/consent?{urlencode({'t': ask})}"

    def _cookie_kwargs(self):
        return {"httponly": True, "samesite": "lax", "path": "/auth",
                "secure": self._base().startswith("https://")}

    async def consent(self, request: Request):
        form = await request.form() if request.method == "POST" else {}
        ask = self._open("ask", str(form.get("t") or
                                    request.query_params.get("t", "")))
        if ask is None:
            return _page("Sign-in expired", "Please go back to your "
                         "assistant and click Connect again.", 400)
        client = await self.get_client(ask["cid"])
        if client is None:
            return _page("Sign-in didn't finish", "Your assistant's "
                         "registration wasn't recognized. Remove Career "
                         "Copilot from it, add it again, and sign in.", 400)
        if request.method == "GET":
            return self._ask_page(client, ask)
        nonce = str(form.get("n", ""))
        held = request.cookies.get(COOKIE + nonce[:8], "")
        if not nonce or not hmac.compare_digest(held, nonce):
            log.info("sign-in refused: Allow came from another page")
            return _page("Sign-in didn't finish", "That Allow click didn't "
                         "come from this browser's Career Copilot page. Go "
                         "back to your assistant and click Connect again.",
                         400)
        if form.get("go") != "allow":
            return RedirectResponse(construct_redirect_uri(
                ask["uri"], error="access_denied", state=ask["st"]),
                status_code=302, headers=PAGE_HEADERS)
        body = {k: v for k, v in ask.items() if k not in ("k", "x")}
        state = self._seal("state", {**body, "n": nonce}, STATE_SECONDS)
        query = urlencode({"client_id": self.gh_id,
                           "redirect_uri": f"{self._base()}/auth/callback",
                           "scope": SCOPE, "state": state,
                           "allow_signup": "true"})
        return RedirectResponse(
            f"{self.gh_base}/login/oauth/authorize?{query}", status_code=302,
            headers=PAGE_HEADERS)

    def _ask_page(self, client, ask):
        nonce = secrets.token_urlsafe(24)
        app = html.escape(client.client_name or "An app")
        where = html.escape(urlparse(ask["uri"]).netloc or ask["uri"])
        body = {k: v for k, v in ask.items() if k not in ("k", "x")}
        sealed = html.escape(self._seal("ask", body, STATE_SECONDS))
        button = "style='padding:.6rem 1.2rem;font:inherit'"
        page = _page(
            "Connect Career Copilot?",
            f"<b>{app}</b> wants to use your Career Copilot. After you sign "
            f"in with GitHub, it will be sent to <b>{where}</b>.</p><p>Only "
            "allow this if you just clicked Connect in your own assistant. "
            "If someone sent you this link, close this page."
            f"<form method=post action='{self._base()}/auth/consent' "
            "style='display:flex;flex-wrap:wrap;gap:.75rem;"
            "margin-top:1.5rem'>"
            f"<input type=hidden name=t value='{sealed}'>"
            f"<input type=hidden name=n value='{nonce}'>"
            f"<button name=go value=allow {button}>Allow and sign in with "
            f"GitHub</button><button name=go value=deny {button}>Don't "
            "allow</button></form>", 200)
        page.set_cookie(COOKIE + nonce[:8], nonce, max_age=STATE_SECONDS,
                        **self._cookie_kwargs())
        return page

    async def _github_user(self, code):
        try:
            async with httpx.AsyncClient(timeout=10) as http:
                token = await http.post(
                    f"{self.gh_base}/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={"client_id": self.gh_id,
                          "client_secret": self.gh_secret, "code": code})
                gh_token = token.json().get("access_token") \
                    if token.status_code == 200 else None
                if not gh_token:
                    return None
                user = await http.get(f"{self.gh_api}/user", headers={
                    "Authorization": f"Bearer {gh_token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "CareerCopilot"})
                # The GitHub token is dropped here: only the identity is kept.
                return user.json() if user.status_code == 200 else None
        except (httpx.HTTPError, ValueError, AttributeError) as error:
            # Only the error's kind is logged: never codes, tokens or bodies.
            log.warning("GitHub sign-in step failed: %s",
                        type(error).__name__)
            raise GitHubUnreachable from None

    async def callback(self, request: Request):
        state = self._open("state", request.query_params.get("state", ""))
        if state is None:
            return _page("Sign-in expired", "Please go back to your "
                         "assistant and click Connect again.", 400)
        nonce = state.get("n", "")
        held = request.cookies.get(COOKIE + nonce[:8], "")
        if not nonce or not hmac.compare_digest(held, nonce):
            log.info("sign-in refused: finished in a different browser")
            return _page("Sign-in didn't finish", "This sign-in was started "
                         "in a different browser, or from a link someone "
                         "sent you. If you were connecting your own "
                         "assistant, click Connect again there. Otherwise "
                         "close this page: nothing was shared.", 400)
        code = request.query_params.get("code")
        try:
            user = await self._github_user(code) if code else None
        except GitHubUnreachable:
            return _page("Couldn't reach GitHub", "GitHub didn't answer "
                         "properly just now. Wait a minute, then click "
                         "Connect again.", 502)
        if not user or "id" not in user:
            return _page("Sign-in didn't finish", "GitHub didn't confirm "
                         "the sign-in. Please try Connect again.", 400)
        login = str(user.get("login", ""))
        if self.allowed and login.lower() not in self.allowed:
            log.info("sign-in refused: not on the invite list")
            safe = html.escape(login)
            return _page("Invite only", "This Career Copilot is invite-only, "
                         f"and you signed in to GitHub as <b>{safe}</b>. Send "
                         "that username to the owner and ask them to add it. "
                         "Then remove Career Copilot from your assistant, add "
                         "it again, and sign in.", 403)
        our_code = self._seal("code", {
            "sub": str(user["id"]), "login": login, "cid": state["cid"],
            "uri": state["uri"], "exp_uri": state["exp_uri"],
            "pkce": state["pkce"], "sc": state["sc"], "res": state["res"],
        }, CODE_SECONDS)
        done = RedirectResponse(construct_redirect_uri(
            state["uri"], code=our_code, state=state["st"]), status_code=302,
            headers=PAGE_HEADERS)
        done.delete_cookie(COOKIE + nonce[:8], **self._cookie_kwargs())
        return done

    async def load_authorization_code(self, client, authorization_code):
        body = self._open("code", authorization_code)
        if not body or body["cid"] != client.client_id:
            return None
        return _Code(code=authorization_code, scopes=body["sc"],
                     expires_at=body["x"], client_id=body["cid"],
                     code_challenge=body["pkce"], redirect_uri=body["uri"],
                     redirect_uri_provided_explicitly=body["exp_uri"],
                     resource=body["res"], subject=body["sub"],
                     login=body["login"])

    # ----------------------------------------------------------- tokens
    def _tokens(self, client_id, sub, login, scopes):
        who = {"sub": sub, "login": login, "cid": client_id, "sc": scopes,
               "n": secrets.token_hex(4)}
        return OAuthToken(
            access_token=self._seal("access", who, ACCESS_SECONDS),
            token_type="Bearer", expires_in=ACCESS_SECONDS,
            refresh_token=self._seal("refresh", who, REFRESH_SECONDS),
            scope=" ".join(scopes))

    async def exchange_authorization_code(self, client, authorization_code):
        return self._tokens(client.client_id, authorization_code.subject,
                            authorization_code.login,
                            authorization_code.scopes)

    async def load_refresh_token(self, client, refresh_token):
        body = self._open("refresh", refresh_token)
        if not body or body["cid"] != client.client_id:
            return None
        return _Refresh(token=refresh_token, client_id=body["cid"],
                        scopes=body["sc"], expires_at=body["x"],
                        subject=body["sub"], login=body["login"])

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        return self._tokens(client.client_id, refresh_token.subject,
                            refresh_token.login,
                            scopes or refresh_token.scopes)

    async def load_access_token(self, token):
        body = self._open("access", token)
        if not body:
            return None
        return AccessToken(token=token, client_id=body["cid"],
                           scopes=body["sc"], expires_at=body["x"],
                           subject=body["sub"],
                           claims={"sub": body["sub"],
                                   "login": body["login"]})

    async def revoke_token(self, token):
        # Nothing is stored, so there's nothing to delete. Removing someone
        # from the invite list blocks them on their next request.
        return None

    def get_routes(self, mcp_path=None):
        return super().get_routes(mcp_path) + [
            Route("/auth/consent", self.consent, methods=["GET", "POST"]),
            Route("/auth/callback", self.callback, methods=["GET"])]
