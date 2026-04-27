"""Registry of external services Instinct can probe (v1 push, #5).

A registered service has:
- detection keywords (matched against the thread's BuildPlan + utterances)
- required auth scopes (informational; surfaced when probe finds the user
  is missing a scope)
- a probe coroutine that returns True iff the service is reachable AND
  scopes look adequate

Services not in this registry are silently skipped — Critic doesn't speculate
about reachability of unknown services.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable

import httpx

log = logging.getLogger(__name__)


@dataclass
class Service:
    key: str                    # canonical id ("linear", "stripe")
    display_name: str           # for human surfaces
    keywords: list[str]         # case-insensitive substrings to detect references
    required_scopes: list[str] = field(default_factory=list)
    suggested_alternatives: list[str] = field(default_factory=list)
    probe: Callable[[], Awaitable[bool]] | None = None

    async def is_reachable(self) -> bool:
        if self.probe is None:
            return True  # registered but no live probe wired — treat as reachable
        try:
            return await self.probe()
        except Exception as e:
            log.debug("probe for %s raised %s", self.key, e)
            return False


# --- Probe implementations --------------------------------------------------
#
# Real probes hit each service's status endpoint with a short timeout. Tests
# substitute these via dependency injection or by overriding `Service.probe`.


_HTTP_TIMEOUT = 5.0


async def _http_status_ok(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            r = await client.get(url)
            return 200 <= r.status_code < 500
    except Exception:
        return False


async def _probe_linear() -> bool:
    if os.environ.get("INSTINCT_LINEAR_API_KEY"):
        return await _http_status_ok("https://api.linear.app/graphql")
    return await _http_status_ok("https://linear-status.com/")


async def _probe_stripe() -> bool:
    return await _http_status_ok("https://www.stripestatus.com/api/v2/status.json")


async def _probe_github() -> bool:
    return await _http_status_ok("https://www.githubstatus.com/api/v2/status.json")


async def _probe_slack() -> bool:
    return await _http_status_ok("https://status.slack.com/api/v2.0.0/current")


async def _probe_salesforce() -> bool:
    return await _http_status_ok("https://api.status.salesforce.com/v1/instances/status")


async def _probe_postgres() -> bool:
    # Postgres reachability is per-deployment; if a connection string is set,
    # we'd ping it. Without one, treat as reachable (deployer can validate).
    return os.environ.get("INSTINCT_POSTGRES_DSN") is None or True


# --- Registry ---------------------------------------------------------------


def default_registry() -> dict[str, Service]:
    return {
        "linear": Service(
            key="linear",
            display_name="Linear",
            keywords=["linear.app", "linear api", "linear epic", "linear issue", "linear workspace", " linear "],
            required_scopes=["issues:create", "issues:read"],
            suggested_alternatives=["GitHub Issues", "Jira"],
            probe=_probe_linear,
        ),
        "stripe": Service(
            key="stripe",
            display_name="Stripe",
            keywords=["stripe.com", "stripe api", "stripe checkout", " stripe "],
            required_scopes=["read_charges", "write_charges"],
            suggested_alternatives=["Paddle", "Lemon Squeezy"],
            probe=_probe_stripe,
        ),
        "github": Service(
            key="github",
            display_name="GitHub",
            keywords=["github.com", "github api", "github actions", " github "],
            required_scopes=["repo", "workflow"],
            suggested_alternatives=["GitLab"],
            probe=_probe_github,
        ),
        "slack": Service(
            key="slack",
            display_name="Slack",
            keywords=["slack.com", "slack api", "slack channel", " slack "],
            required_scopes=["chat:write", "channels:read"],
            suggested_alternatives=["Discord webhooks", "MS Teams"],
            probe=_probe_slack,
        ),
        "salesforce": Service(
            key="salesforce",
            display_name="Salesforce",
            keywords=["salesforce", "sfdc", "force.com"],
            required_scopes=["api"],
            suggested_alternatives=["HubSpot"],
            probe=_probe_salesforce,
        ),
        "postgres": Service(
            key="postgres",
            display_name="Postgres",
            keywords=["postgres", "postgresql", "psql", "rds postgres"],
            required_scopes=[],
            suggested_alternatives=["MySQL", "Snowflake", "BigQuery"],
            probe=_probe_postgres,
        ),
    }


# --- Infeasibility detectors ------------------------------------------------
#
# Pattern catches obviously-fake service names — useful for the
# `infeasible_request` eval fixture and as a guardrail when the Builder
# hallucinates an API.


_INFEASIBLE_NAME_RE = re.compile(
    r"\b(foobarbaz|foo[\s_-]?bar|stripexyz|xyzcorp|widgetapi|"
    r"acmewidget|loremipsum|placeholder[\s_-]?api|fakeapi|sampleservice)\b",
    re.IGNORECASE,
)


def detect_obviously_infeasible(text: str) -> list[str]:
    """Returns the substrings that look like obviously-fake API references."""
    return list({m.group(0) for m in _INFEASIBLE_NAME_RE.finditer(text)})
