from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

from .artifacts import (
    DECISIONS_FILE,
    FULL_STATECHART_FILE,
    HANDOFFS_FILE,
    NORMALIZATION_FILE,
    RAW_FILE,
    REFINED_FILE,
    REVIEW_FILE,
    SCENARIOS_FILE,
    STATECHART_FILE,
    alternative_artifacts,
    load_yaml,
    source_hash,
)
from .validator import validate_design


def collect_design(design_dir: Path) -> Dict[str, Any]:
    design_dir = design_dir.resolve()
    data: Dict[str, Any] = {
        "design_dir": str(design_dir),
        "raw": "",
        "raw_hash": None,
        "artifacts": {},
        "validation": {"errors": [], "warnings": []},
    }
    raw_path = design_dir / RAW_FILE
    if raw_path.exists():
        data["raw"] = raw_path.read_text(encoding="utf-8")
        data["raw_hash"] = source_hash(design_dir)
    for name in [
        REFINED_FILE,
        NORMALIZATION_FILE,
        DECISIONS_FILE,
        STATECHART_FILE,
        SCENARIOS_FILE,
        FULL_STATECHART_FILE,
        HANDOFFS_FILE,
        REVIEW_FILE,
    ]:
        path = design_dir / name
        if path.exists():
            data["artifacts"][name] = load_yaml(path)
    for path in alternative_artifacts(design_dir):
        data["artifacts"][path.name] = load_yaml(path)
    result = validate_design(design_dir)
    data["validation"] = {"errors": result.errors, "warnings": result.warnings}
    return data


def render_dashboard_html(design_dir: Path) -> str:
    design = collect_design(design_dir)
    artifacts = design["artifacts"]
    refined = artifacts.get(REFINED_FILE, {})
    statechart = artifacts.get(STATECHART_FILE)
    full_statechart = artifacts.get(FULL_STATECHART_FILE)
    scenarios = artifacts.get(SCENARIOS_FILE, {})
    handoffs = artifacts.get(HANDOFFS_FILE, {})
    alternatives = {name: value for name, value in artifacts.items() if name.startswith("artifact.")}
    decisions = artifacts.get(DECISIONS_FILE, {}).get("decisions", [])
    requirements = refined.get("requirements", [])
    errors = design["validation"]["errors"]

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Journeyman Review</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1c2430;
      --muted: #64748b;
      --line: #d7dee8;
      --panel: #f8fafc;
      --accent: #0f766e;
      --warn: #b45309;
      --bad: #b91c1c;
    }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #ffffff;
    }}
    header {{
      padding: 24px 32px;
      border-bottom: 1px solid var(--line);
      background: #f7f9fb;
    }}
    main {{
      display: grid;
      grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
      min-height: calc(100vh - 89px);
    }}
    aside {{
      border-right: 1px solid var(--line);
      padding: 24px;
      background: var(--panel);
    }}
    section {{
      padding: 24px 32px;
      border-bottom: 1px solid var(--line);
    }}
    .filter-input {{
      margin-top: 14px;
      width: min(420px, 100%);
      box-sizing: border-box;
      padding: 9px 11px;
      border: 1px solid var(--line);
      border-radius: 6px;
      font: inherit;
      background: #fff;
    }}
    .hidden {{ display: none; }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    h1 {{ font-size: 22px; }}
    h2 {{ font-size: 18px; }}
    h3 {{ font-size: 15px; }}
    p, li {{ line-height: 1.5; }}
    code, pre {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
    }}
    pre {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: #eef3f8;
      padding: 12px;
      border-radius: 6px;
      border: 1px solid var(--line);
    }}
    .muted {{ color: var(--muted); }}
    .pill {{
      display: inline-block;
      padding: 2px 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      font-size: 12px;
      color: var(--muted);
    }}
    .error {{ color: var(--bad); }}
    .ok {{ color: var(--accent); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .item {{ border: 1px solid var(--line); border-radius: 6px; padding: 12px; background: #fff; }}
    .transition {{ border-left: 3px solid var(--accent); padding-left: 10px; margin: 10px 0; }}
    @media (max-width: 820px) {{
      main {{ grid-template-columns: 1fr; }}
      aside {{ border-right: 0; border-bottom: 1px solid var(--line); }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Journeyman Review</h1>
    <div class="muted">{html.escape(str(design["design_dir"]))}</div>
    <input id="review-filter" class="filter-input" type="search" placeholder="Filter by actor, scenario, dependency, state, or decision">
  </header>
  <main>
    <aside>
      <h2>Validation</h2>
      {_render_validation(errors)}
      <h2>Routing</h2>
      {_render_routing(refined)}
      <h2>Raw Source</h2>
      <p class="muted">sha256:{html.escape(str(design["raw_hash"] or ""))}</p>
      <pre>{html.escape(design["raw"])}</pre>
    </aside>
    <div>
      <section>
        <h2>Requirements</h2>
        {_render_requirements(requirements)}
      </section>
      <section>
        <h2>Selected Artifact</h2>
        {_render_statechart(statechart) if statechart else _render_alternatives(alternatives)}
      </section>
      <section>
        <h2>Full Chart Review</h2>
        {_render_full_review(statechart, full_statechart)}
      </section>
      <section>
        <h2>Scenario Coverage</h2>
        {_render_scenarios(scenarios)}
      </section>
      <section>
        <h2>Handoffs And Dependencies</h2>
        {_render_handoffs(handoffs)}
      </section>
      <section>
        <h2>Actor Lanes And Events</h2>
        {_render_actor_lanes(full_statechart or statechart or {})}
      </section>
      <section>
        <h2>Decisions</h2>
        {_render_decisions(decisions)}
      </section>
    </div>
  </main>
  <script>
    const filterInput = document.getElementById('review-filter');
    const filterTargets = Array.from(document.querySelectorAll('.item, .transition'));
    filterInput.addEventListener('input', () => {{
      const query = filterInput.value.trim().toLowerCase();
      for (const target of filterTargets) {{
        target.classList.toggle('hidden', query.length > 0 && !target.textContent.toLowerCase().includes(query));
      }}
    }});
  </script>
</body>
</html>"""


def run_dashboard(design_dir: Path, host: str, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/api/design":
                body = json.dumps(collect_design(design_dir), indent=2).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            body = render_dashboard_html(design_dir).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Journeyman dashboard: http://{host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")


def _render_validation(errors: Any) -> str:
    if not errors:
        return '<p class="ok">No validation errors.</p>'
    items = "".join(f'<li class="error">{html.escape(str(error))}</li>' for error in errors)
    return f"<ul>{items}</ul>"


def _render_routing(refined: Dict[str, Any]) -> str:
    return (
        f"<p><span class=\"pill\">{html.escape(str(refined.get('request_type', 'unknown')))}</span></p>"
        f"<p>Recommended: <strong>{html.escape(str(refined.get('recommended_artifact', 'unknown')))}</strong></p>"
        f"<p class=\"muted\">Confidence: {html.escape(str(refined.get('recommendation_confidence', 'unknown')))}</p>"
    )


def _render_requirements(requirements: Any) -> str:
    if not requirements:
        return '<p class="muted">No requirements found.</p>'
    chunks = []
    for req in requirements:
        if not isinstance(req, dict):
            continue
        chunks.append(
            '<div class="item">'
            f"<h3>{html.escape(str(req.get('id', 'requirement')))}</h3>"
            f"<p>{html.escape(str(req.get('text', '')))}</p>"
            f"<p><span class=\"pill\">{html.escape(str(req.get('evidence', 'unknown')))}</span> "
            f"<span class=\"muted\">{html.escape(str(req.get('source_ref', '')))}</span></p>"
            "</div>"
        )
    return f'<div class="grid">{"".join(chunks)}</div>'


def _render_statechart(statechart: Dict[str, Any]) -> str:
    states = statechart.get("states", [])
    transitions = statechart.get("transitions", [])
    state_items = "".join(
        f"<li><strong>{html.escape(str(state.get('id', state)))}</strong>: "
        f"{html.escape(str(state.get('entry_condition', '')) if isinstance(state, dict) else '')}</li>"
        for state in states
    )
    transition_items = "".join(
        '<div class="transition">'
        f"<strong>{html.escape(str(t.get('from')))} -> {html.escape(str(t.get('to')))}</strong>"
        f"<p>{html.escape(str(t.get('trigger', '')))}: {html.escape(str(t.get('expected_result', '')))}</p>"
        "</div>"
        for t in transitions
        if isinstance(t, dict)
    )
    return f"<h3>{html.escape(str(statechart.get('title', 'Happy Path Statechart')))}</h3><ul>{state_items}</ul>{transition_items}"


def _render_full_review(happy: Any, full: Any) -> str:
    if not isinstance(full, dict):
        return '<p class="muted">No full chart artifact found.</p>'
    happy_states = _state_ids(happy.get("states", []) if isinstance(happy, dict) else [])
    full_states = _state_ids(full.get("states", []))
    happy_transitions = _transition_ids(happy.get("transitions", []) if isinstance(happy, dict) else [])
    full_transitions = _transition_ids(full.get("transitions", []))
    added_states = sorted(full_states - happy_states)
    added_transitions = sorted(full_transitions - happy_transitions)
    return (
        f"<h3>{html.escape(str(full.get('title', 'Full Chart')))}</h3>"
        f"<p><span class=\"pill\">Added states: {len(added_states)}</span> "
        f"<span class=\"pill\">Added transitions: {len(added_transitions)}</span></p>"
        f"<p class=\"muted\">States: {html.escape(', '.join(added_states) or 'none')}</p>"
        f"<p class=\"muted\">Transitions: {html.escape(', '.join(added_transitions) or 'none')}</p>"
        f"{_render_statechart(full)}"
    )


def _render_scenarios(scenarios: Dict[str, Any]) -> str:
    if not scenarios:
        return '<p class="muted">No scenarios found.</p>'
    chunks = []
    for scenario in scenarios.get("high_priority", []):
        if not isinstance(scenario, dict):
            continue
        chunks.append(
            '<div class="item">'
            f"<h3>{html.escape(str(scenario.get('id', 'scenario')))}: {html.escape(str(scenario.get('title', '')))}</h3>"
            f"<p>{html.escape(str(scenario.get('reason', '')))}</p>"
            f"<p><span class=\"pill\">{html.escape(str(scenario.get('priority', '')))}</span> "
            f"<span class=\"muted\">states: {html.escape(', '.join(map(str, scenario.get('affected_states', []))))}</span></p>"
            f"<p class=\"muted\">transitions: {html.escape(', '.join(map(str, scenario.get('affected_transitions', []))))}</p>"
            "</div>"
        )
    deferred = scenarios.get("deferred", [])
    if deferred:
        chunks.append(
            '<div class="item">'
            "<h3>Deferred</h3>"
            + "".join(
                f"<p><strong>{html.escape(str(item.get('id', 'deferred')))}</strong>: {html.escape(str(item.get('rationale', '')))}</p>"
                for item in deferred
                if isinstance(item, dict)
            )
            + "</div>"
        )
    return f'<div class="grid">{"".join(chunks)}</div>' if chunks else '<p class="muted">No scenarios found.</p>'


def _render_handoffs(handoffs: Dict[str, Any]) -> str:
    if not handoffs:
        return '<p class="muted">No handoffs found.</p>'
    chunks = []
    for handoff in handoffs.get("handoffs", []):
        if not isinstance(handoff, dict):
            continue
        chunks.append(
            '<div class="item">'
            f"<h3>{html.escape(str(handoff.get('id', 'handoff')))}</h3>"
            f"<p>Owner: <strong>{html.escape(str(handoff.get('owner', '')))}</strong></p>"
            f"<p>{html.escape(str(handoff.get('input_artifact', '')))} -> {html.escape(str(handoff.get('output_artifact', '')))}</p>"
            f"<p class=\"muted\">Failure: {html.escape(str(handoff.get('failure_transition') or handoff.get('accepted_risk') or ''))}</p>"
            "</div>"
        )
    for dependency in handoffs.get("dependencies", []):
        if not isinstance(dependency, dict):
            continue
        chunks.append(
            '<div class="item">'
            f"<h3>{html.escape(str(dependency.get('id', 'dependency')))}: {html.escape(str(dependency.get('name', '')))}</h3>"
            f"<p>Owner: <strong>{html.escape(str(dependency.get('owner', '')))}</strong></p>"
            f"<p class=\"muted\">Failure path: {html.escape(str(dependency.get('failure_path', '')))}</p>"
            "</div>"
        )
    return f'<div class="grid">{"".join(chunks)}</div>' if chunks else '<p class="muted">No handoffs found.</p>'


def _render_actor_lanes(chart: Dict[str, Any]) -> str:
    if not chart:
        return '<p class="muted">No actor lane data found.</p>'
    lanes: Dict[str, list] = {}
    for state in chart.get("states", []):
        if not isinstance(state, dict):
            continue
        lane = str(state.get("lane") or "unassigned")
        lanes.setdefault(lane, []).append(str(state.get("id", "")))
    lane_chunks = "".join(
        '<div class="item">'
        f"<h3>{html.escape(lane)}</h3>"
        f"<p>{html.escape(', '.join(states))}</p>"
        "</div>"
        for lane, states in lanes.items()
    )
    events = chart.get("metadata", {}).get("event_passes", []) if isinstance(chart.get("metadata"), dict) else []
    event_chunks = "".join(
        '<div class="transition">'
        f"<strong>{html.escape(str(event.get('id', 'event')))}: {html.escape(str(event.get('from', '')))} -> {html.escape(str(event.get('to', '')))}</strong>"
        f"<p>{html.escape(str(event.get('event', '')))} ({html.escape(str(event.get('transition_ref', '')))}).</p>"
        "</div>"
        for event in events
        if isinstance(event, dict)
    )
    return f'<div class="grid">{lane_chunks}</div>{event_chunks}' if lane_chunks or event_chunks else '<p class="muted">No actor lane data found.</p>'


def _render_alternatives(alternatives: Dict[str, Any]) -> str:
    if not alternatives:
        return '<p class="muted">No selected artifact found.</p>'
    chunks = []
    for name, artifact in alternatives.items():
        chunks.append(
            '<div class="item">'
            f"<h3>{html.escape(name)}</h3>"
            f"<p><strong>{html.escape(str(artifact.get('artifact_type', 'artifact')))}</strong></p>"
            f"<p>{html.escape(str(artifact.get('rationale', '')))}</p>"
            "</div>"
        )
    return "".join(chunks)


def _render_decisions(decisions: Any) -> str:
    if not decisions:
        return '<p class="muted">No decisions logged.</p>'
    chunks = []
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        chunks.append(
            '<div class="item">'
            f"<h3>{html.escape(str(decision.get('id', 'decision')))}</h3>"
            f"<p><span class=\"pill\">{html.escape(str(decision.get('stage', '')))}</span> "
            f"<span class=\"pill\">{html.escape(str(decision.get('mode', '')))}</span></p>"
            f"<p>{html.escape(str(decision.get('proposal', '')))}</p>"
            f"<p class=\"muted\">Outcome: {html.escape(str(decision.get('outcome', '')))}</p>"
            "</div>"
        )
    return f'<div class="grid">{"".join(chunks)}</div>'


def _state_ids(states: Any) -> set:
    if not isinstance(states, list):
        return set()
    values = set()
    for state in states:
        if isinstance(state, dict) and state.get("id"):
            values.add(str(state["id"]))
        elif isinstance(state, str):
            values.add(state)
    return values


def _transition_ids(transitions: Any) -> set:
    if not isinstance(transitions, list):
        return set()
    values = set()
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        if transition.get("id"):
            values.add(str(transition["id"]))
        elif transition.get("from") and transition.get("to"):
            values.add(f"{transition['from']}->{transition['to']}")
    return values
