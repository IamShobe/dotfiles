#!/usr/bin/env python3
"""Re-apply this machine's tweaks on top of a Shepherdr install (run after `shepherdr install`).

  - The stock agents list under the spaces list in the sidebar.
  - The skillshare panel: a toggle beside the tab bar and a block beside the work area.
  - Shepherdr's single-child wrappers (e.g. the `panel` column its buttons show and hide) put back
    when something collapsed them, checked against the pristine layout in the Shepherdr checkout.
  - A spinner on a space's row (and on the collapsed rail) while one of its agents works.
  - The sections-api mod in a 0px block, so `herdr-sections` can change sidebar sections.
  - Shepherdr as the active layout.

Idempotent: what's already there is left alone. When a Shepherdr update moved the code a patch
anchors on, it says so and skips that patch instead of guessing.

Shepherdr's installer keeps a file the person changed and puts its own version beside it as
<file>.new. Every change to these files lives in this script, so the .new is taken (the update
lands) and the tweaks are applied to it again.
"""

import json
import os
import pathlib
import subprocess
import sys
from typing import Any

# Herdr's layout tree and shared state, edited in place so keys this script doesn't know survive.
JsonObject = dict[str, Any]  # no-smell: stdlib-only bootstrap script (no pydantic on a fresh machine); app-owned JSON round-tripped as-is
APP_HOME = pathlib.Path.home() / ".config/herdr-app"
LAYOUT_FILE = APP_HOME / "layouts/shepherdr.json"
SPACES_MOD_FILE = APP_HOME / "mods/spaces-chat/main.js"
SHARED_STATE_FILE = APP_HOME / "shared.json"
LAYOUT_NAME = "shepherdr"

AGENTS_BLOCK = {"id": "agents", "type": "block", "size": {"weight": 1}, "min": 90, "content": {"mod": "agents"}}
SKILLSHARE_TOGGLE = {"id": "skillshare-toggle", "type": "block", "content": {"mod": "skillshare", "props": {"role": "toggle"}}, "size": {"px": 118}}
# One block, not a column holding one: a single-child wrapper is what gets collapsed, and the
# toggle shows and hides this id.
SKILLSHARE_PANEL = {
    "id": "skillshare-panel", "type": "block", "hidden": True, "size": {"px": 400}, "min": 320, "max": 720,
    "content": {"mod": "skillshare"},
}
PRISTINE_LAYOUT_FILE = pathlib.Path.home() / ".local/share/shepherdr/layouts/shepherdr.json"
SECTIONS_API_HOLDER = {"id": "sections-api", "type": "block", "size": {"px": 0}, "content": {"mod": "sections-api"}}
TAB_BAR_HEIGHT = {"px": 42}

SPINNER = 'svg("mods/workspace-chrome/spinner.svg").size(12).flex_none().text_color(t.working).spin(900)'
ROW_ANCHOR = '          .when(quiet, (el) => el.child(svg("mods/spaces-chat/bell-off.svg").size(13).flex_none().text_color(t.dim)))\n'
ROW_SPINNER = (
    "          // An agent here is working: the agents list's spinner, so progress shows on the space too.\n"
    f'          .when(w.status === "working", (el) => el.child({SPINNER}))\n'
)
RAIL_ANCHOR = "      .child(div().text_color(tone(t, w.status)).child(glyph(w.status)));\n"
RAIL_SPINNER = f'      .child(w.status === "working" ? {SPINNER} : div().text_color(tone(t, w.status)).child(glyph(w.status)));\n'


def main() -> int:
    if not LAYOUT_FILE.exists():
        print(f"no {LAYOUT_FILE}: Shepherdr isn't installed; nothing to customize")
        return 0
    for patched_file in (LAYOUT_FILE, SPACES_MOD_FILE):
        take_shepherdr_update(path=patched_file)
    customize_layout(layout_file=LAYOUT_FILE)
    add_working_spinner(mod_file=SPACES_MOD_FILE)
    make_layout_active(layout_name=LAYOUT_NAME)
    return 0


def take_shepherdr_update(*, path: pathlib.Path) -> None:
    shepherdr_version = path.with_name(path.name + ".new")
    if shepherdr_version.exists():
        os.replace(shepherdr_version, path)


def customize_layout(*, layout_file: pathlib.Path) -> None:
    layout = json.loads(layout_file.read_text())  # no-smell: Herdr's layout file, round-tripped untouched apart from our nodes
    restore_collapsed_wrappers(layout=layout)
    add_agents_list(layout=layout)
    add_skillshare_toggle(layout=layout)
    add_skillshare_panel(layout=layout)
    add_sections_api_holder(layout=layout)
    write_json_atomically(path=layout_file, data=layout)


def add_agents_list(*, layout: JsonObject) -> None:
    if find_node(node=layout, node_id="agents"):
        return
    sidebar_lists = find_node(node=layout, node_id="sidebar-lists")
    if sidebar_lists is None:
        warn("layout has no sidebar-lists node; agents list not added")
        return
    sidebar_lists["children"].append(AGENTS_BLOCK)


def add_skillshare_toggle(*, layout: JsonObject) -> None:
    if find_node(node=layout, node_id="skillshare-toggle"):
        return
    work = find_node(node=layout, node_id="work")
    tabs = find_node(node=layout, node_id="tabs")
    if work is None or tabs is None or tabs not in work["children"]:
        warn("layout's tab bar isn't directly in the work column; skillshare toggle not added")
        return
    tabs_row = {
        "id": "tabs-row", "type": "row", "size": tabs.get("size", TAB_BAR_HEIGHT), "resizable": False,
        "children": [{**tabs, "size": {"weight": 1}}, SKILLSHARE_TOGGLE],
    }
    work["children"][work["children"].index(tabs)] = tabs_row


def add_skillshare_panel(*, layout: JsonObject) -> None:
    work_body = find_node(node=layout, node_id="work-body")
    if work_body is None:
        warn("layout has no work-body node; skillshare panel not added")
        return
    # Older shapes: a "skillshare-panel" column around a "skillshare" block, or that block alone
    # after the column was collapsed. Both become the single block.
    old_shapes = {"skillshare-panel", "skillshare"}
    kept = [child for child in work_body["children"] if child.get("id") not in old_shapes]
    work_body["children"] = [*kept, SKILLSHARE_PANEL]


def restore_collapsed_wrappers(*, layout: JsonObject) -> None:
    if not PRISTINE_LAYOUT_FILE.exists():
        return
    pristine = json.loads(PRISTINE_LAYOUT_FILE.read_text())  # no-smell: Shepherdr's own layout file, read only
    for wrapper in single_child_containers(node=pristine):
        wrap_child_again(layout=layout, wrapper=wrapper)


def single_child_containers(*, node: JsonObject) -> list[JsonObject]:
    children = node.get("children", [])
    here = [node] if len(children) == 1 and node.get("id") else []
    return here + [found for child in children for found in single_child_containers(node=child)]


def wrap_child_again(*, layout: JsonObject, wrapper: JsonObject) -> None:
    child_id = wrapper["children"][0].get("id")
    if find_node(node=layout, node_id=wrapper["id"]) or not child_id:
        return
    parent = find_parent(node=layout, child_id=child_id)
    if parent is None:
        return
    index = next(i for i, child in enumerate(parent["children"]) if child.get("id") == child_id)
    parent["children"][index] = {**wrapper, "children": [parent["children"][index]]}


def find_parent(*, node: JsonObject, child_id: str) -> JsonObject | None:
    for child in node.get("children", []):
        if child.get("id") == child_id:
            return node
        found = find_parent(node=child, child_id=child_id)
        if found is not None:
            return found
    return None


def add_sections_api_holder(*, layout: JsonObject) -> None:
    if find_node(node=layout, node_id="sections-api"):
        return
    sidebar = find_node(node=layout, node_id="sidebar")
    if sidebar is None:
        warn("layout has no sidebar node; sections-api not added (herdr-sections won't work)")
        return
    sidebar["children"].append(SECTIONS_API_HOLDER)


def add_working_spinner(*, mod_file: pathlib.Path) -> None:
    source = mod_file.read_text()
    patched = insert_after_anchor(source=source, anchor=ROW_ANCHOR, addition=ROW_SPINNER, what="row spinner")
    patched = replace_anchor(source=patched, anchor=RAIL_ANCHOR, replacement=RAIL_SPINNER, what="rail spinner")
    if patched != source:
        mod_file.write_text(patched)


def insert_after_anchor(*, source: str, anchor: str, addition: str, what: str) -> str:
    if addition in source:
        return source
    if source.count(anchor) != 1:
        warn(f"spaces-chat changed; {what} not added")
        return source
    return source.replace(anchor, anchor + addition)


def replace_anchor(*, source: str, anchor: str, replacement: str, what: str) -> str:
    if replacement in source:
        return source
    if source.count(anchor) != 1:
        warn(f"spaces-chat changed; {what} not added")
        return source
    return source.replace(anchor, replacement)


def make_layout_active(*, layout_name: str) -> None:
    """The running window switches live; with none running, the next start reads shared.json."""
    switched = subprocess.run(
        ["herdr-app", "do", "layout.switch", "--name", layout_name], capture_output=True, text=True,
    )
    if switched.returncode == 0:
        return
    shared_state = json.loads(SHARED_STATE_FILE.read_text()) if SHARED_STATE_FILE.exists() else {}  # no-smell: Herdr's shared state, only the layout key is set
    write_json_atomically(path=SHARED_STATE_FILE, data={**shared_state, "layout": layout_name})


def find_node(*, node: JsonObject, node_id: str) -> JsonObject | None:
    if node.get("id") == node_id:
        return node
    for child in node.get("children", []):
        found = find_node(node=child, node_id=node_id)
        if found is not None:
            return found
    return None


def write_json_atomically(*, path: pathlib.Path, data: JsonObject) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(temporary, path)


def warn(message: str) -> None:
    print(f"customize-shepherdr: {message}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
