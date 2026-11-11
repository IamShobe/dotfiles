#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.12", "pydantic>=2.7"]
# ///
"""One call per step of an explainer.

  start    the rules, plus the facts of a change: a git range, PRs (with merge and deploy
           status), tickets and Slack threads. With --name it also creates a durable
           workspace (EXPLAINERS_DIR/<name>) with a starting App.tsx.
  build    build and verify a workspace; prints the path to publish
  refresh  re-check PR and deploy status, rebuild, say what changed
  url      remember the published URL
  list     every explainer, with its URL

EXPLAINERS_DIR defaults to ~/.local/share/explainers. EXPLAINER_TICKET_URL turns a
ticket id into a link: https://linear.app/acme/issue/{id}.
"""

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal, assert_never
from urllib.parse import urlparse

import typer
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, field_validator

SKILL_DIR = Path(__file__).resolve().parent.parent
EXPLAINERS_DIR = Path(os.environ.get("EXPLAINERS_DIR", Path.home() / ".local/share/explainers"))
TICKET_URL_TEMPLATE = os.environ.get("EXPLAINER_TICKET_URL", "")
DEPLOY_CHECK_TIMEOUT_S = 120
ISSUE_BODY_MAX_CHARS = 2500
ISSUE_COMMENTS_SHOWN = 10

app = typer.Typer(add_completion=False, no_args_is_help=True, help=__doc__)


class Kind(str, Enum):
    change = "change"
    incident = "incident"


PrState = Literal["draft", "open", "merged", "closed"]


class PrStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ref: str
    url: str
    title: str
    state: PrState
    merged_at: str | None
    merge_sha: str | None
    deployed: bool | None


class Status(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checked_at: str
    prs: list[PrStatus]


class Workspace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    kind: Kind
    repo_dir: str | None
    base: str | None
    head: str | None
    paths: list[str]
    prs: list[str]
    tickets: list[str]
    threads: list[str]
    deploy_check: str | None
    url: str | None = None


class GhCommit(BaseModel):
    oid: str


class GhPr(BaseModel):
    number: int
    title: str
    state: Literal["OPEN", "MERGED", "CLOSED"]
    isDraft: bool
    mergedAt: str | None
    mergeCommit: GhCommit | None
    url: str
    baseRefName: str
    headRefName: str

    @field_validator("mergedAt", mode="before")
    @classmethod
    def empty_is_none(cls, value: object) -> object:
        return value or None


class GhPrNumber(BaseModel):
    number: int


SPECS = TypeAdapter(list[dict[str, object]])


class GhComment(BaseModel):
    author: dict[str, str | None]
    body: str


class GhIssue(BaseModel):
    title: str
    state: str
    body: str
    comments: list[GhComment] = Field(default_factory=list)


class Deps(BaseModel):
    wab: Path
    diagram_design: Path


class PrRef(BaseModel):
    repo: str
    number: int

    @property
    def label(self) -> str:
        return f"{self.repo.split('/')[-1]}#{self.number}"


GH_PR_FIELDS = "number,title,state,isDraft,mergedAt,mergeCommit,url,baseRefName,headRefName"


# ---------------------------------------------------------------- commands


@app.command()
def start(
    base: Annotated[str | None, typer.Argument(help="git base (default: merge-base with the default branch, or the PR's)")] = None,
    head: Annotated[str | None, typer.Argument(help="git head (default: HEAD, or the PR's)")] = None,
    name: Annotated[str | None, typer.Option(help="create or update the durable workspace EXPLAINERS_DIR/<name>")] = None,
    kind: Annotated[Kind, typer.Option(help="change: a PR or feature; incident: something broke")] = Kind.change,
    pr: Annotated[list[str] | None, typer.Option(help="PR: 123, owner/repo#123 or its URL; repeatable")] = None,
    ticket: Annotated[list[str] | None, typer.Option(help="ticket id or URL; repeatable")] = None,
    thread: Annotated[list[str] | None, typer.Option(help="Slack thread URL; repeatable")] = None,
    path: Annotated[list[str] | None, typer.Option(help="limit git facts to this path; repeatable")] = None,
    deploy_check: Annotated[str | None, typer.Option(help="shell command, {sha} = merge commit; exit 0 deployed, 1 not")] = None,
) -> None:
    """Print paths, rules and facts; with --name, also set up the workspace."""
    deps = resolve_deps()
    repo_dir = git_toplevel()
    pr_refs = [parse_pr_ref(raw=raw, repo_dir=repo_dir) for raw in pr or []] or current_branch_pr(repo_dir=repo_dir)
    status = check_status(pr_refs=pr_refs, deploy_check=deploy_check, repo_dir=repo_dir)
    git_range = choose_git_range(base=base, head=head, status=status, pr_refs=pr_refs, repo_dir=repo_dir)
    workspace = Workspace(
        name=name or "", kind=kind, repo_dir=str(repo_dir) if repo_dir else None,
        base=git_range[0], head=git_range[1], paths=path or [],
        prs=[f"{ref.repo}#{ref.number}" for ref in pr_refs], tickets=ticket or [], threads=thread or [],
        deploy_check=deploy_check,
    )
    print_paths(deps=deps, name=name)
    print_rules(deps=deps)
    print_status(status=status, deploy_check=deploy_check)
    print_inputs(tickets=workspace.tickets, threads=workspace.threads)
    print_git_facts(workspace=workspace)
    if name:
        create_workspace(workspace=workspace, status=status)


@app.command()
def build(name: str, no_verify: Annotated[bool, typer.Option(help="skip verify.sh")] = False) -> None:
    """Build and verify the workspace; print the path to publish."""
    workspace = load_workspace(name)
    deps = resolve_deps()
    code = build_workspace(workspace=workspace, deps=deps, verify=not no_verify)
    print_publish_hint(workspace=workspace)
    raise typer.Exit(code)


@app.command()
def refresh(name: str) -> None:
    """Re-check PR and deploy status, rebuild, and say what changed."""
    workspace = load_workspace(name)
    previous = load_status(name)
    repo_dir = Path(workspace.repo_dir) if workspace.repo_dir else None
    pr_refs = [parse_pr_ref(raw=raw, repo_dir=repo_dir) for raw in workspace.prs]
    current = check_status(pr_refs=pr_refs, deploy_check=workspace.deploy_check, repo_dir=repo_dir)
    write_status(name=name, status=current)
    print_status_changes(previous=previous, current=current)
    code = build_workspace(workspace=workspace, deps=resolve_deps(), verify=True)
    print_publish_hint(workspace=workspace)
    raise typer.Exit(code)


@app.command()
def url(name: str, artifact_url: str) -> None:
    """Remember the published URL, so later sessions update the same artifact."""
    workspace = load_workspace(name)
    save_workspace(workspace.model_copy(update={"url": artifact_url}))
    print(f"✓ {name} → {artifact_url}")


@app.command(name="list")
def list_explainers() -> None:
    """Every explainer: name, title, URL, last change."""
    for directory in sorted(EXPLAINERS_DIR.glob("*/explainer.json")):
        workspace = load_workspace(directory.parent.name)
        app_file = directory.parent / "App.tsx"
        title = read_title(app_file) if app_file.exists() else "?"
        changed = dt.datetime.fromtimestamp(directory.parent.stat().st_mtime).strftime("%Y-%m-%d")
        print(f"{workspace.name} · {title} · {workspace.url or 'not published'} · {changed}")


# ---------------------------------------------------------------- start


def resolve_deps() -> Deps:
    script = f'eval "$(bash {SKILL_DIR}/scripts/ensure-deps.sh 2>/dev/null)"; printf "%s\\n%s" "$WAB" "$DIAGRAM_DESIGN"'
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True)
    wab, diagram_design = result.stdout.splitlines()
    return Deps(wab=Path(wab), diagram_design=Path(diagram_design))


def git_toplevel() -> Path | None:
    result = run(["git", "rev-parse", "--show-toplevel"], cwd=None)
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def parse_pr_ref(*, raw: str, repo_dir: Path | None) -> PrRef:
    url_match = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)\S*", raw)
    slug_match = re.fullmatch(r"([^/\s]+/[^#\s]+)#(\d+)", raw)
    if url_match:
        return PrRef(repo=url_match.group(1), number=int(url_match.group(2)))
    if slug_match:
        return PrRef(repo=slug_match.group(1), number=int(slug_match.group(2)))
    if raw.isdigit() and repo_dir:
        return PrRef(repo=current_repo_slug(repo_dir=repo_dir), number=int(raw))
    raise typer.BadParameter(f"PR '{raw}': use 123 (inside a repo), owner/repo#123 or the PR URL")


def current_repo_slug(*, repo_dir: Path) -> str:
    result = run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"], cwd=repo_dir)
    return result.stdout.strip()


def current_branch_pr(*, repo_dir: Path | None) -> list[PrRef]:
    if not repo_dir:
        return []
    result = run(["gh", "pr", "view", "--json", "number"], cwd=repo_dir)
    if result.returncode != 0:
        return []
    branch_pr = GhPrNumber.model_validate_json(result.stdout)
    return [PrRef(repo=current_repo_slug(repo_dir=repo_dir), number=branch_pr.number)]


def check_status(*, pr_refs: list[PrRef], deploy_check: str | None, repo_dir: Path | None) -> Status:
    prs = [pr_status(ref=ref, deploy_check=deploy_check, repo_dir=repo_dir) for ref in pr_refs]
    return Status(checked_at=dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC"), prs=[p for p in prs if p])


def pr_status(*, ref: PrRef, deploy_check: str | None, repo_dir: Path | None) -> PrStatus | None:
    gh_pr = fetch_pr(ref=ref)
    if not gh_pr:
        return None
    state = pr_state(gh_pr)
    merge_sha = gh_pr.mergeCommit.oid if gh_pr.mergeCommit and state == "merged" else None
    deployed = run_deploy_check(command=deploy_check, sha=merge_sha, repo_dir=repo_dir) if merge_sha else None
    return PrStatus(
        ref=ref.label, url=gh_pr.url, title=gh_pr.title, state=state,
        merged_at=gh_pr.mergedAt, merge_sha=merge_sha, deployed=deployed,
    )


def fetch_pr(*, ref: PrRef) -> GhPr | None:
    result = run(["gh", "pr", "view", str(ref.number), "--repo", ref.repo, "--json", GH_PR_FIELDS], cwd=None)
    if result.returncode != 0:
        print(f"⚠ {ref.label}: gh pr view failed: {result.stderr.strip()[:200]}", file=sys.stderr)
        return None
    try:
        return GhPr.model_validate_json(result.stdout)
    except ValidationError as error:
        print(f"⚠ {ref.label}: unexpected gh output: {error}", file=sys.stderr)
        return None


def pr_state(gh_pr: GhPr) -> PrState:
    match gh_pr.state:
        case "MERGED":
            return "merged"
        case "CLOSED":
            return "closed"
        case "OPEN":
            return "draft" if gh_pr.isDraft else "open"
        case unreachable:
            assert_never(unreachable)


def run_deploy_check(*, command: str | None, sha: str, repo_dir: Path | None) -> bool | None:
    if not command:
        return None
    try:
        result = subprocess.run(
            command.replace("{sha}", sha), shell=True, cwd=repo_dir,
            capture_output=True, timeout=DEPLOY_CHECK_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return None
    match result.returncode:
        case 0:
            return True
        case 1:
            return False
        case _:
            return None


def choose_git_range(
    *, base: str | None, head: str | None, status: Status, pr_refs: list[PrRef], repo_dir: Path | None,
) -> tuple[str | None, str | None]:
    """Explicit arguments win; otherwise one PR of this repo defines the range."""
    if base or not repo_dir or len(pr_refs) != 1 or pr_refs[0].repo != current_repo_slug(repo_dir=repo_dir):
        return base, head
    gh_pr = fetch_pr(ref=pr_refs[0])
    merged = next((p for p in status.prs if p.merge_sha), None)
    if merged and merged.merge_sha and ensure_commit(sha=merged.merge_sha, repo_dir=repo_dir):
        return f"{merged.merge_sha}^1", merged.merge_sha
    if gh_pr and gh_pr.state == "OPEN":
        run(["git", "fetch", "-q", "origin", gh_pr.baseRefName, gh_pr.headRefName], cwd=repo_dir)
        return f"origin/{gh_pr.baseRefName}", f"origin/{gh_pr.headRefName}"
    return base, head


def ensure_commit(*, sha: str, repo_dir: Path) -> bool:
    if run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=repo_dir).returncode == 0:
        return True
    return run(["git", "fetch", "-q", "origin", sha], cwd=repo_dir).returncode == 0


def print_paths(*, deps: Deps, name: str | None) -> None:
    cli = f"{SKILL_DIR}/scripts/explainer.py"
    workspace = EXPLAINERS_DIR / name if name else None
    print("# Paths\n")
    print(f"S={SKILL_DIR}\nWAB={deps.wab}\nDIAGRAM_DESIGN={deps.diagram_design}")
    if workspace:
        print(f"workspace: {workspace}  (App.tsx, specs.json, status.ts live here; edit them in place)")
        print(f"build:     {cli} build {name}")
        print(f"refresh:   {cli} refresh {name}   # status changed → rebuild")
        print(f"record:    {cli} url {name} <artifact url>")
    print(f"example:   python3 {deps.wab}/scripts/diagrams/render.py --example <type>\n")


def print_rules(*, deps: Deps) -> None:
    for rule_file in (
        SKILL_DIR / "references/readability.md",
        SKILL_DIR / "references/formatting.md",
        deps.wab / "references/kit.md",
        deps.wab / "references/diagram-types.md",
    ):
        print(f"\n<!-- {rule_file} -->")
        print(rule_file.read_text())


def print_status(*, status: Status, deploy_check: str | None) -> None:
    if not status.prs:
        return
    print("\n# Status\n")
    for pr in status.prs:
        print(f"- {pr.ref} · {pr.state}{merged_detail(pr)} · {deploy_detail(pr=pr, deploy_check=deploy_check)} · {pr.url}")
        print(f"  {pr.title}")
    print(f"\nChecked {status.checked_at}. Merged is not deployed: say which on the page.")


def merged_detail(pr: PrStatus) -> str:
    return f" {pr.merged_at[:10]} as {pr.merge_sha[:9]}" if pr.merged_at and pr.merge_sha else ""


def deploy_detail(*, pr: PrStatus, deploy_check: str | None) -> str:
    if pr.state != "merged":
        return "not deployed"
    if not deploy_check:
        return "deployed: unknown (no --deploy-check)"
    return {True: "deployed", False: "NOT deployed yet", None: "deployed: check failed"}[pr.deployed]


def print_inputs(*, tickets: list[str], threads: list[str]) -> None:
    if not tickets and not threads:
        return
    print("\n# Inputs\n")
    for ticket in tickets:
        print_ticket(ticket)
    for thread_url in threads:
        print_thread(thread_url)


def print_ticket(ticket: str) -> None:
    parsed = urlparse(ticket)
    parts = parsed.path.strip("/").split("/")
    if parsed.netloc == "github.com" and len(parts) == 4 and parts[2] == "issues":
        print_github_issue(ticket)
        return
    link = ticket if parsed.scheme else TICKET_URL_TEMPLATE.replace("{id}", ticket)
    print(f"## Ticket {ticket}")
    print(f"Link: {link or '(set EXPLAINER_TICKET_URL to link ids)'}")
    print("Fetch it in turn 2, with the source reads: your tracker's tool (Linear: get_issue + list_comments).\n")


def print_github_issue(issue_url: str) -> None:
    result = run(["gh", "issue", "view", issue_url, "--json", "title,state,body,comments"], cwd=None)
    if result.returncode != 0:
        print(f"## {issue_url}\n⚠ gh issue view failed; read it in turn 2.\n")
        return
    issue = GhIssue.model_validate_json(result.stdout)
    print(f"## {issue.title} ({issue.state.lower()}) · {issue_url}\n")
    print(issue.body[:ISSUE_BODY_MAX_CHARS])
    for comment in issue.comments[-ISSUE_COMMENTS_SHOWN:]:
        print(f"\n> {comment.author.get('login')}: {comment.body[:600]}")
    print()


def print_thread(thread_url: str) -> None:
    match = re.search(r"/archives/([A-Z0-9]+)/p(\d{10})(\d{6})", thread_url)
    print(f"## Thread {thread_url}")
    if match:
        channel, seconds, micros = match.groups()
        print(f"Fetch it in turn 2: slack_read_thread(channel_id={channel}, message_ts={seconds}.{micros})\n")
    else:
        print("Fetch it in turn 2 with the tool for that source.\n")


def print_git_facts(*, workspace: Workspace) -> None:
    if not workspace.repo_dir:
        print("\n# Facts\n\nNot in a git repo: no diff facts. Build the story from the inputs above.")
        return
    args = [a for a in (workspace.base, workspace.head) if a]
    args += ["--", *workspace.paths] if workspace.paths else []
    print()
    sys.stdout.flush()
    subprocess.run(["bash", str(SKILL_DIR / "scripts/gather-facts.sh"), *args], cwd=workspace.repo_dir)


def create_workspace(*, workspace: Workspace, status: Status) -> None:
    directory = EXPLAINERS_DIR / workspace.name
    directory.mkdir(parents=True, exist_ok=True)
    existing = load_workspace(workspace.name) if (directory / "explainer.json").exists() else None
    save_workspace(workspace.model_copy(update={"url": existing.url}) if existing else workspace)
    write_status(name=workspace.name, status=status)
    if not (directory / "specs.json").exists():
        (directory / "specs.json").write_text("[]\n")
    app_file = directory / "App.tsx"
    if not app_file.exists():
        app_file.write_text(scaffold_app(workspace=workspace))
    print(f"\n# Workspace\n\n{directory}: App.tsx ({'kept' if existing else 'scaffolded'}), specs.json, status.ts")


# ---------------------------------------------------------------- scaffold


def scaffold_app(*, workspace: Workspace) -> str:
    """A starting point with every slot marked ⟨…⟩; verify.sh fails until each is replaced or cut."""
    meta = page_meta(workspace)
    tickets = " · ".join(ticket_ref(t) for t in workspace.tickets)
    eyebrow_tickets = f"{tickets} · " if tickets else ""
    return (
        SCAFFOLD_HEAD.replace("__META__", meta).replace("__TICKETS__", eyebrow_tickets)
        + sections_for(workspace.kind)
        + SCAFFOLD_TAIL
    )


def page_meta(workspace: Workspace) -> str:
    if not workspace.repo_dir:
        return "{}"
    repo_dir = Path(workspace.repo_dir)
    sha = run(["git", "rev-parse", workspace.head or "HEAD"], cwd=repo_dir).stdout.strip()
    return f"{{ repo: '{current_repo_slug(repo_dir=repo_dir)}', sha: '{sha}' }}"


def ticket_ref(ticket: str) -> str:
    link = ticket if urlparse(ticket).scheme else TICKET_URL_TEMPLATE.replace("{id}", ticket) or "⟨ticket URL⟩"
    label = ticket.rstrip("/").split("/")[-1] if urlparse(ticket).scheme else ticket
    return f'<Ref href="{link}">{label}</Ref>'


def sections_for(kind: Kind) -> str:
    match kind:
        case Kind.change:
            return CHANGE_SECTIONS
        case Kind.incident:
            return INCIDENT_SECTIONS
        case unreachable:
            assert_never(unreachable)


SCAFFOLD_HEAD = """// @title: ⟨Human title⟩
// A starting point, not a form. Rename, reorder, merge or cut any section; swap any block;
// add a diagram, a TimeChart or a Playground where it tells the story better. Pick blocks
// by content (formatting.md). verify.sh fails while any placeholder is left.
import { Fragment } from 'react'
import { BeforeAfter, Callout, Code, P, Page, Ref, Section, Steps, Table, Tldr } from '@/kit'
import { status, type Pr, type PrState } from './status'

const meta = __META__

const stateLabel = { draft: 'Draft', open: 'In review', merged: '✓ Merged', closed: 'Closed' } satisfies Record<PrState, string>

function progress(pr: Pr) {
  if (pr.deployed) return '✓ Deployed'
  return pr.state === 'merged' && pr.deployed === false ? '✓ Merged, not deployed yet' : stateLabel[pr.state]
}

function PrLinks() {
  return <>{status.prs.map((pr, i) => <Fragment key={pr.ref}>{i > 0 && ' + '}<Ref href={pr.url}>{pr.ref}</Ref></Fragment>)}</>
}

const rollout = status.prs.map((pr) => ({ title: <>{progress(pr)}: <Ref href={pr.url}>{pr.ref}</Ref></>, body: pr.title }))

export default function App() {
  return (
    <Page
      meta={meta}
      eyebrow={<>__TICKETS__<PrLinks /></>}
      title="⟨What changed, in plain words⟩"
      thesis="⟨One sentence a teammate who didn't write it understands⟩"
    >
"""

CHANGE_SECTIONS = """      <Section id="tldr" title="TL;DR">
        <Tldr
          items={[
            { label: 'What changed', tone: 'change', statement: '⟨≤ 8 plain words, outcome first⟩', facts: ['⟨a number⟩'] },
            { label: 'Why', tone: 'neutral', statement: '⟨≤ 8 words⟩' },
            { label: 'Status', tone: 'result', statement: <PrLinks />, facts: status.prs.map(progress) },
            { label: 'What you do', tone: 'action', statement: '⟨One action, or "Nothing"⟩' },
          ]}
        />
        <BeforeAfter
          example="⟨The running example: one person, request or row⟩"
          rows={[{ aspect: '⟨…⟩', before: '⟨…⟩', after: '⟨…⟩' }]}
          result={{ before: '⟨…⟩', after: '⟨…⟩' }}
        />
      </Section>

      <Section id="how" group="The change" title="How it works" takeaway="⟨Outcome first, ≤ 25 words⟩">
        <P>⟨A diagram in a Figure usually beats prose here.⟩</P>
      </Section>

      <Section id="rollout" group="Shipping" title="Rollout status" takeaway="⟨Where it is now, honestly: merged is not deployed⟩">
        <Steps items={[...rollout, { title: '⟨Then: what happens after deploy⟩' }]} />
      </Section>

      <Section id="check" group="Shipping" title="How to check it" takeaway="⟨The one thing that proves it works⟩">
        <Code lang="bash" code="⟨command, query or URL⟩" />
      </Section>

      <Section id="risk" group="Shipping" title="Risk and rollback" takeaway="⟨What could break and how you'd know⟩">
        <Table columns={['If', 'You see', 'Undo']} rows={[['⟨…⟩', '⟨alert or dashboard⟩', '⟨…⟩']]} />
      </Section>

      <Section id="decisions" group="What's next" title="Decisions needed" takeaway="⟨What's open, who decides, by when⟩">
        <Table columns={['Question', 'Who', 'By']} rows={[['⟨…⟩', '⟨…⟩', '⟨…⟩']]} />
      </Section>
"""

INCIDENT_SECTIONS = """      <Section id="tldr" title="TL;DR">
        <Tldr
          items={[
            { label: 'What broke', tone: 'problem', statement: '⟨≤ 8 plain words, outcome first⟩', facts: ['⟨who, how many⟩', '⟨since when⟩'] },
            { label: 'Why', tone: 'neutral', statement: '⟨≤ 8 words⟩' },
            { label: 'The fix', tone: 'change', statement: '⟨≤ 8 words⟩' },
            { label: 'Status', tone: 'result', statement: <PrLinks />, facts: status.prs.map(progress) },
            { label: 'What you do', tone: 'action', statement: '⟨One action, or "Nothing"⟩' },
          ]}
        />
        <BeforeAfter
          example="⟨The running example: one affected person or record⟩"
          rows={[{ aspect: '⟨…⟩', before: '⟨…⟩', after: '⟨…⟩' }]}
          result={{ before: '⟨…⟩', after: '⟨…⟩' }}
        />
      </Section>

      <Section id="timeline" group="What went wrong" title="What happened" takeaway="⟨The impact, with numbers⟩">
        <Table columns={['When', 'What happened']} rows={[['⟨15:43 UTC⟩', '⟨…⟩']]} />
      </Section>

      <Section id="cause" group="What went wrong" title="Why it broke" takeaway="⟨The cause in one sentence⟩">
        <P>⟨A diagram of the running example often says this best.⟩</P>
      </Section>

      <Section id="fix" group="The fix" title="The fix" takeaway="⟨What changed, outcome first⟩">
        <P>⟨…⟩</P>
      </Section>

      <Section id="rollout" group="Shipping" title="Rollout status" takeaway="⟨Where it is now, honestly: merged is not deployed⟩">
        <Steps items={[...rollout, { title: '⟨Then: when access or data comes back⟩' }]} />
      </Section>

      <Section id="check" group="Shipping" title="How to check it" takeaway="⟨The one thing that proves it's fixed⟩">
        <Code lang="bash" code="⟨command, query or URL⟩" />
      </Section>

      <Section id="risk" group="Shipping" title="Risk and rollback" takeaway="⟨What could break and how you'd know⟩">
        <Table columns={['If', 'You see', 'Undo']} rows={[['⟨…⟩', '⟨alert or dashboard⟩', '⟨…⟩']]} />
      </Section>

      <Section id="next" group="What's next" title="Follow-ups" takeaway="⟨What stops this happening again⟩">
        <Callout title="Decisions needed">⟨Question · who decides · by when⟩</Callout>
      </Section>
"""

SCAFFOLD_TAIL = """    </Page>
  )
}
"""


# ---------------------------------------------------------------- build


def build_workspace(*, workspace: Workspace, deps: Deps, verify: bool) -> int:
    directory = EXPLAINERS_DIR / workspace.name
    artifact_src = directory / workspace.name / "src"
    if not artifact_src.exists():
        run(["bash", str(deps.wab / "scripts/new-artifact.sh"), workspace.name], cwd=directory)
    shutil.copy(directory / "status.ts", artifact_src / "status.ts")
    command = ["bash", str(deps.wab / "scripts/build.sh"), workspace.name, "App.tsx"]
    command += ["--specs", "specs.json"] if has_specs(directory / "specs.json") else []
    command += ["--repo", workspace.repo_dir] if workspace.repo_dir else []
    command += [] if verify else ["--no-verify"]
    sys.stdout.flush()
    return subprocess.run(command, cwd=directory).returncode


def has_specs(specs_file: Path) -> bool:
    return specs_file.exists() and bool(SPECS.validate_json(specs_file.read_text()))


def print_publish_hint(*, workspace: Workspace) -> None:
    html = EXPLAINERS_DIR / workspace.name / f"{workspace.name}.html"
    if workspace.url:
        print(f"\nPublish: Artifact file_path={html} url={workspace.url}")
    else:
        print(f"\nPublish: Artifact file_path={html}, then: {SKILL_DIR}/scripts/explainer.py url {workspace.name} <url>")


# ---------------------------------------------------------------- refresh


def print_status_changes(*, previous: Status | None, current: Status) -> None:
    before = {pr.ref: pr for pr in previous.prs} if previous else {}
    changes = [
        f"- {pr.ref}: {describe(before.get(pr.ref))} → {describe(pr)}"
        for pr in current.prs
        if describe(before.get(pr.ref)) != describe(pr)
    ]
    print("# Status changes\n")
    print("\n".join(changes) if changes else "- none: the page's status is current")
    if changes:
        print("\nThe eyebrow, TL;DR status row and rollout steps update by themselves.")
        print("Update any prose that states the old status (takeaways, 'Next:' steps, 'What you do').")
    print()


def describe(pr: PrStatus | None) -> str:
    if not pr:
        return "not tracked"
    return "deployed" if pr.deployed else pr.state


# ---------------------------------------------------------------- storage


def load_workspace(name: str) -> Workspace:
    config = EXPLAINERS_DIR / name / "explainer.json"
    if not config.exists():
        raise typer.BadParameter(f"no explainer '{name}' in {EXPLAINERS_DIR} (create it: start --name {name})")
    return Workspace.model_validate_json(config.read_text())


def save_workspace(workspace: Workspace) -> None:
    (EXPLAINERS_DIR / workspace.name / "explainer.json").write_text(workspace.model_dump_json(indent=2) + "\n")


def load_status(name: str) -> Status | None:
    status_file = EXPLAINERS_DIR / name / "status.json"
    return Status.model_validate_json(status_file.read_text()) if status_file.exists() else None


def write_status(*, name: str, status: Status) -> None:
    directory = EXPLAINERS_DIR / name
    (directory / "status.json").write_text(status.model_dump_json(indent=2) + "\n")
    prs = json.dumps([pr.model_dump() for pr in status.prs], indent=2)
    (directory / "status.ts").write_text(STATUS_TS.replace("__CHECKED__", status.checked_at).replace("__PRS__", prs))


STATUS_TS = """// Written by explainer.py (start / refresh). Edit the PR list with `start --name`, not here.
export type PrState = 'draft' | 'open' | 'merged' | 'closed'
export type Pr = {
  ref: string; url: string; title: string; state: PrState
  merged_at: string | null; merge_sha: string | null; deployed: boolean | null
}
export const status: { checkedAt: string; prs: Pr[] } = {
  checkedAt: '__CHECKED__',
  prs: __PRS__,
}
"""


def read_title(app_file: Path) -> str:
    first = app_file.read_text().split("\n", 1)[0]
    return first.removeprefix("// @title:").strip() if first.startswith("// @title:") else "?"


def run(command: list[str], *, cwd: Path | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


if __name__ == "__main__":
    app()
