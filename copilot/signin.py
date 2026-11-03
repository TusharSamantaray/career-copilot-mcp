"""Sign in with GitHub, with nothing kept on the server.

The free host wipes its disk on every restart, so sign-in can't depend
on stored state. Everything it needs travels sealed inside the values
the apps already hold:

- an app's registration is sealed into its own client id;
- a sign-in in progress rides in the state sent through GitHub;
- codes and tokens carry the person's GitHub id and username, sealed.

Sealing uses a key from the environment (CAREER_COPILOT_JWT_KEY), which
survives restarts, so one sign-in keeps working through restarts and
deploys. GitHub's own token is used once to learn who the person is,
then thrown away. Changing the key signs everyone out.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import urlencode

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

SCOPE = "read:user"
STATE_SECONDS = 600
CODE_SECONDS = 300
ACCESS_SECONDS = 30 * 24 * 3600
REFRESH_SECONDS = 365 * 24 * 3600
KEPT_METADATA = ("redirect_uris", "grant_types", "response_types",
                 "token_endpoint_auth_method", "scope", "client_name")


class _Code(AuthorizationCode):
    login: str = ""


class _Refresh(RefreshToken):
    login: str = ""


def _page(title, text, status):
    return HTMLResponse(
        f"<!doctype html><meta charset=utf-8><title>{title}</title>"
        f"<body style='font-family:system-ui;max-width:32rem;margin:4rem "
        f"auto;padding:0 1rem'><h1>{title}</h1><p>{text}</p></body>",
        status_code=status)


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
    async def authorize(self, client, params: AuthorizationParams) -> str:
        state = self._seal("state", {
            "cid": client.client_id, "uri": str(params.redirect_uri),
            "exp_uri": params.redirect_uri_provided_explicitly,
            "pkce": params.code_challenge, "st": params.state,
            "sc": params.scopes or [SCOPE], "res": params.resource,
        }, STATE_SECONDS)
        query = urlencode({"client_id": self.gh_id,
                           "redirect_uri": f"{str(self.base_url).rstrip('/')}"
                                           "/auth/callback",
                           "scope": SCOPE, "state": state,
                           "allow_signup": "true"})
        return f"{self.gh_base}/login/oauth/authorize?{query}"

    async def _github_user(self, code):
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

    async def callback(self, request: Request):
        state = self._open("state", request.query_params.get("state", ""))
        if state is None:
            return _page("Sign-in expired", "Please go back to your "
                         "assistant and click Connect again.", 400)
        code = request.query_params.get("code")
        user = await self._github_user(code) if code else None
        if not user or "id" not in user:
            return _page("Sign-in didn't finish", "GitHub didn't confirm "
                         "the sign-in. Please try Connect again.", 400)
        login = str(user.get("login", ""))
        if self.allowed and login.lower() not in self.allowed:
            return _page("Invite only", "This Career Copilot is invite-only. "
                         "Ask its owner to add your GitHub username.", 403)
        our_code = self._seal("code", {
            "sub": str(user["id"]), "login": login, "cid": state["cid"],
            "uri": state["uri"], "exp_uri": state["exp_uri"],
            "pkce": state["pkce"], "sc": state["sc"], "res": state["res"],
        }, CODE_SECONDS)
        return RedirectResponse(construct_redirect_uri(
            state["uri"], code=our_code, state=state["st"]), status_code=302)

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
            Route("/auth/callback", self.callback, methods=["GET"])]
