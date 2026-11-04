// Sections, icons and pins of the spaces sidebar (Shepherdr's spaces-chat), changed from a shell.
//
// spaces-chat keeps them in shared "spaces-chat" (see its sections.js). Shared state lives in the
// app and is saved with the latest change winning, so editing shared.json from outside gets
// overwritten: changes have to be made in here, with setShared. This mod has no UI; the layout
// holds it in a 0px block so it's always loaded.
//
// From the shell (bin/herdr-sections does this): write data/sections-req.json =
//   { "ops": [ ...ops ] }   then   herdr-app do sections-api.apply
// and read data/sections-res.json = { ok, sections, error? }.
//
// Ops (sections are named by name; machine null/omitted: this computer):
//   { op: "create",  name, spaces?: [space ids], icon? }     made if missing; the spaces move in
//   { op: "move",    space, section: name | null }            null: back to the top, out of sections
//   { op: "rename",  section, name }
//   { op: "delete",  section }                                its spaces go back to the top
//   { op: "fold",    section, folded: bool }
//   { op: "icon",    space, icon: emoji | null }              the space's emoji instead of "#"
//   { op: "pin",     space, pinned: bool }

import { View, div } from "gpui-kit";
import { shared, setShared, nextCommand, appHome } from "herdr";
import * as fs from "fs/promises";

const KEY = "spaces-chat";
const REQUEST = () => `${appHome()}/data/sections-req.json`;
const RESULT = () => `${appHome()}/data/sections-res.json`;

export default class SectionsApi extends View {
  init(_props, cx) {
    cx.spawn(async () => {
      for (;;) {
        const command = await nextCommand();
        if (command === "apply") await answerRequest();
      }
    });
  }

  render() {
    return div();
  }
}

async function answerRequest() {
  const result = await applyRequest().catch((e) => ({ ok: false, error: String(e?.message ?? e) }));
  await fs.writeFile(RESULT(), JSON.stringify({ ...result, sections: sidebarData().sections }, null, 2));
}

async function applyRequest() {
  const request = JSON.parse(await fs.readFile(REQUEST(), "utf8"));
  await fs.unlink(REQUEST()).catch(() => {});
  const ops = Array.isArray(request?.ops) ? request.ops : [];
  const next = ops.reduce((data, op) => applyOp({ data, op }), sidebarData());
  setShared(KEY, next);
  return { ok: true };
}

function sidebarData() {
  const d = shared(KEY) ?? {};
  return { ...d, sections: d.sections ?? [], icons: d.icons ?? {}, pinned: d.pinned ?? [], machines: d.machines ?? {} };
}

const OPS = {
  create: createSection,
  move: moveSpace,
  rename: renameSection,
  delete: deleteSection,
  fold: foldSection,
  icon: setSpaceIcon,
  pin: pinSpace,
};

function applyOp({ data, op }) {
  const apply = OPS[op?.op];
  if (!apply) throw new Error(`unknown op ${JSON.stringify(op?.op)} (one of: ${Object.keys(OPS).join(", ")})`);
  return apply({ data, op });
}

function createSection({ data, op }) {
  const machine = op.machine ?? null;
  const existing = findSection({ data, name: op.name, machine });
  const withSection = existing ? data : {
    ...data,
    sections: [...data.sections, { id: newSectionId(), machine, name: requireName(op.name), folded: false, spaces: [], ...(op.icon ? { icon: op.icon } : {}) }],
  };
  return (op.spaces ?? []).reduce((d, space) => moveSpace({ data: d, op: { space, section: op.name, machine } }), withSection);
}

function moveSpace({ data, op }) {
  const target = op.section == null ? null : requireSection({ data, name: op.section, machine: op.machine ?? null });
  const sections = data.sections.map((s) => ({
    ...s,
    spaces: [...s.spaces.filter((x) => x !== op.space), ...(target && s.id === target.id ? [op.space] : [])],
  }));
  return { ...data, sections };
}

function renameSection({ data, op }) {
  const section = requireSection({ data, name: op.section, machine: op.machine ?? null });
  return { ...data, sections: data.sections.map((s) => (s.id === section.id ? { ...s, name: requireName(op.name) } : s)) };
}

function deleteSection({ data, op }) {
  const section = requireSection({ data, name: op.section, machine: op.machine ?? null });
  return { ...data, sections: data.sections.filter((s) => s.id !== section.id) };
}

function foldSection({ data, op }) {
  const section = requireSection({ data, name: op.section, machine: op.machine ?? null });
  return { ...data, sections: data.sections.map((s) => (s.id === section.id ? { ...s, folded: Boolean(op.folded) } : s)) };
}

function setSpaceIcon({ data, op }) {
  const { [op.space]: _old, ...icons } = data.icons;
  return { ...data, icons: op.icon ? { ...icons, [op.space]: op.icon } : icons };
}

function pinSpace({ data, op }) {
  const pinned = data.pinned.filter((x) => x !== op.space);
  return { ...data, pinned: op.pinned ? [...pinned, op.space] : pinned };
}

function findSection({ data, name, machine }) {
  const wanted = String(name ?? "").trim().toLowerCase();
  return data.sections.find((s) => (s.machine ?? null) === machine && s.name.toLowerCase() === wanted) ?? null;
}

function requireSection({ data, name, machine }) {
  const section = findSection({ data, name, machine });
  if (!section) throw new Error(`no section named ${JSON.stringify(name)}`);
  return section;
}

function requireName(name) {
  const trimmed = String(name ?? "").trim();
  if (!trimmed) throw new Error("a section needs a name");
  return trimmed;
}

function newSectionId() {
  return `sec-${Math.random().toString(36).slice(2, 10)}`;
}
