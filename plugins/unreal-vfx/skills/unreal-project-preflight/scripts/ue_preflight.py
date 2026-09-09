"""Unreal project preflight: prove the plugins and project settings a plan
needs are in place BEFORE step 1 runs, and batch every restart-requiring
change into one restart.

Usage (see --help for every flag):

    # What does this feature set need, and what does THIS project have?
    python ue_preflight.py --project path/to/Show.uproject --features megaplants,pcg,mrq

    # Same, but ask the running editor which project it has open and read
    # plugin state + CVars back from it (authoritative when it is up)
    python ue_preflight.py --live --features megaplants,pcg,mrq

    # Ad-hoc requirements without the catalog
    python ue_preflight.py --project X.uproject --require plugin:ImagePlate \
        --require "ini:DefaultEngine:/Script/Engine.RendererSettings:r.Nanite.Foliage=True"

    # Emit the markdown 'Step 0' block for the plan
    python ue_preflight.py --live --features megaplants --plan-block

    # Apply the .uproject / ini edits (backs up first; editor should be closed)
    python ue_preflight.py --project X.uproject --features megaplants --apply

Requirement spec grammar:
    plugin:<Name>                                   .uplugin basename
    ini:<Stem>:<Section>:<Key>=<Value>              Default*.ini under Config/; any other
                                                    stem = Saved/Config/WindowsEditor/<Stem>.ini
    ini:<StemA|StemB>:<Section>:<Key>=<Value>       accept either file (--apply writes StemA)
    ini:<Stem>:<Section>:+<Key>=<Value>             list entry must be present
    cvar:<r.Name>=<Value>                           live read-back only (int/float)

Exit codes: 0 = everything satisfied, 1 = changes needed, 2 = error.

Sources of truth, in order: the .uproject and Config/Default*.ini on disk
(what the NEXT editor launch will load), then the live editor when --live
(what the CURRENT session actually has). A CVar read from the editor returns
0 for a variable that does not exist, so a live 0 is never trusted on its
own - the ini decides, the CVar only confirms.

No drive letters or usernames are built in: the project comes from
--project or from the live editor, the engine root from the .uproject's
EngineAssociation via the registry, --engine-root, or UE_ENGINE_ROOT.
ASCII only on purpose.
"""

import argparse
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

DEFAULT_MCP_URL = "http://127.0.0.1:8000/mcp"
CATALOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reference", "requirements_catalog.json")

STATUS_OK = "OK"
STATUS_MISSING = "MISSING"
STATUS_MISMATCH = "MISMATCH"
STATUS_NOT_IN_ENGINE = "NOT_IN_ENGINE"
STATUS_SKIPPED = "SKIPPED"
STATUS_UNKNOWN = "UNKNOWN"


# ----------------------------------------------------------------------------
# MCP transport (curl; the UE server's SSE body arrives empty through urllib)
# ----------------------------------------------------------------------------

def _curl_post(url, payload, session_id=None, timeout=30, capture_headers=False):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(payload, handle)
        payload_path = handle.name
    cmd = [
        "curl", "-s", "-m", str(timeout), "-X", "POST", url,
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json, text/event-stream",
        "--data-binary", "@" + payload_path,
    ]
    if session_id:
        cmd += ["-H", "Mcp-Session-Id: " + session_id]
    if capture_headers:
        cmd += ["-D", "-"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    finally:
        os.unlink(payload_path)
    if result.returncode != 0:
        raise RuntimeError("curl rc=" + str(result.returncode) + " " + result.stderr[:200])
    return result.stdout


def _parse_body(raw):
    if "data: " in raw:
        raw = raw.split("data: ", 1)[1]
    else:
        brace = raw.find("{")
        if brace > 0:
            raw = raw[brace:]
    return json.loads(raw)


def mcp_run_python(url, code, timeout=60):
    """Run Python inside the editor; returns the parsed execute_python_code envelope."""
    init_payload = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "ue_preflight", "version": "1.0"}},
    }
    raw = _curl_post(url, init_payload, timeout=10, capture_headers=True)
    session_id = None
    for line in raw.splitlines():
        if line.lower().startswith("mcp-session-id:"):
            session_id = line.split(":", 1)[1].strip()
            break
    if not session_id:
        raise RuntimeError("no Mcp-Session-Id from " + url)
    call_payload = {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "execute_python_code", "arguments": {"code": code}},
    }
    data = _parse_body(_curl_post(url, call_payload, session_id=session_id, timeout=timeout))
    if "error" in data:
        raise RuntimeError("MCP error: " + json.dumps(data["error"]))
    return json.loads(data["result"]["content"][0]["text"])


LIVE_PROBE = r'''
import unreal, json
out = {}
out["project_file"] = unreal.Paths.get_project_file_path()
out["engine_version"] = unreal.SystemLibrary.get_engine_version()
out["enabled_plugins"] = [str(n) for n in unreal.PluginBlueprintLibrary.get_enabled_plugin_names()]
out["cvars"] = {}
for name in __CVARS__:
    try:
        out["cvars"][name] = {"int": unreal.SystemLibrary.get_console_variable_int_value(name),
                              "float": unreal.SystemLibrary.get_console_variable_float_value(name)}
    except Exception as exc:
        out["cvars"][name] = {"error": str(exc)[:120]}
print(json.dumps(out))
'''


def live_probe(url, cvar_names, timeout=60):
    code = LIVE_PROBE.replace("__CVARS__", json.dumps(sorted(set(cvar_names))))
    envelope = mcp_run_python(url, code, timeout=timeout)
    if not envelope.get("success"):
        raise RuntimeError("editor python failed: " + str(envelope.get("error_message", ""))[:300])
    text = envelope.get("output", "").strip()
    return json.loads(text.splitlines()[-1])


# ----------------------------------------------------------------------------
# Engine + plugin descriptors
# ----------------------------------------------------------------------------

def read_json(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def resolve_engine_root(uproject, explicit=None):
    """Engine root from --engine-root, UE_ENGINE_ROOT, or the registry via EngineAssociation."""
    if explicit:
        return os.path.abspath(explicit), "--engine-root"
    env = os.environ.get("UE_ENGINE_ROOT")
    if env:
        return os.path.abspath(env), "UE_ENGINE_ROOT"
    assoc = None
    try:
        assoc = read_json(uproject).get("EngineAssociation")
    except Exception:
        pass
    if assoc and sys.platform == "win32":
        try:
            import winreg
            for hive, key in ((winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\EpicGames\Unreal Engine\%s" % assoc),
                              (winreg.HKEY_CURRENT_USER, r"Software\Epic Games\Unreal Engine\Builds")):
                try:
                    with winreg.OpenKey(hive, key) as handle:
                        if key.endswith("Builds"):
                            value, _ = winreg.QueryValueEx(handle, assoc)
                        else:
                            value, _ = winreg.QueryValueEx(handle, "InstalledDirectory")
                        if value and os.path.isdir(value):
                            return os.path.abspath(value), "registry EngineAssociation=" + str(assoc)
                except OSError:
                    continue
        except ImportError:
            pass
    return None, "unresolved (EngineAssociation=%s)" % assoc


def index_plugin_descriptors(engine_root, project_dir):
    """name -> {path, enabled_by_default, experimental, beta, deps, origin}."""
    index = {}
    roots = []
    if engine_root:
        roots.append((os.path.join(engine_root, "Engine", "Plugins"), "engine"))
    roots.append((os.path.join(project_dir, "Plugins"), "project"))
    for root, origin in roots:
        if not os.path.isdir(root):
            continue
        for path in glob.glob(os.path.join(root, "**", "*.uplugin"), recursive=True):
            name = os.path.splitext(os.path.basename(path))[0]
            try:
                desc = read_json(path)
            except Exception:
                desc = {}
            index[name] = {
                "path": path,
                "origin": origin,
                "enabled_by_default": bool(desc.get("EnabledByDefault", False)),
                "experimental": bool(desc.get("IsExperimentalVersion", False)),
                "beta": bool(desc.get("IsBetaVersion", False)),
                "deps": [d.get("Name") for d in desc.get("Plugins", []) if d.get("Enabled", True)],
            }
    return index


# ----------------------------------------------------------------------------
# INI handling (tolerant: +/-/./! prefixes, duplicate keys, BOM, CRLF)
# ----------------------------------------------------------------------------

def ini_read(path):
    """Returns (lines, bom, newline). Lines keep no line endings."""
    if not os.path.isfile(path):
        return [], False, "\r\n"
    with open(path, "rb") as handle:
        raw = handle.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    if bom:
        raw = raw[3:]
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8", errors="replace")
    return text.split("\n") if newline == "\n" else text.split("\r\n"), bom, newline


def ini_write(path, lines, bom, newline):
    data = newline.join(lines).encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    with open(path, "wb") as handle:
        handle.write(data)


def ini_sections(lines):
    """section -> list of (line_index, op, key, value). op in '', '+', '-', '.', '!'."""
    sections = {}
    current = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith(";") or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1]
            sections.setdefault(current, [])
            continue
        if current is None or "=" not in stripped:
            continue
        op = ""
        if stripped[0] in "+-.!":
            op, stripped = stripped[0], stripped[1:]
        key, value = stripped.split("=", 1)
        sections[current].append((idx, op, key.strip(), value.strip()))
    return sections


def norm_value(value):
    v = str(value).strip().strip('"').lower()
    if v in ("true", "1"):
        return "1"
    if v in ("false", "0"):
        return "0"
    return v


def ini_current(sections, section, key, is_list):
    entries = sections.get(section, [])
    if is_list:
        present = []
        for _, op, k, v in entries:
            if k != key:
                continue
            if op == "!":
                present = []
            elif op in ("+", ".", ""):
                present.append(v)
            elif op == "-" and v in present:
                present.remove(v)
        return present
    value = None
    for _, op, k, v in entries:
        if k == key and op in ("", "."):
            value = v
    return value


def ini_apply(lines, sections, section, key, value, is_list):
    """Mutates lines in place; returns a description of the edit."""
    entries = sections.get(section)
    if entries is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("[" + section + "]")
        lines.append(("+" if is_list else "") + key + "=" + value)
        return "added section + key"
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == "[" + section + "]":
            header_idx = idx
            break
    last_idx = header_idx
    for idx, _, _, _ in entries:
        last_idx = max(last_idx, idx)
    if is_list:
        lines.insert(last_idx + 1, "+" + key + "=" + value)
        return "appended list entry"
    for idx, op, k, _ in reversed(entries):
        if k == key and op in ("", "."):
            lines[idx] = op + key + "=" + value
            return "replaced line %d" % (idx + 1)
    lines.insert(last_idx + 1, key + "=" + value)
    return "appended key"


# ----------------------------------------------------------------------------
# Requirement specs
# ----------------------------------------------------------------------------

def parse_spec(spec):
    kind, _, rest = spec.partition(":")
    kind = kind.strip().lower()
    if kind == "plugin":
        if not rest:
            raise ValueError("plugin spec needs a name: " + spec)
        return {"kind": "plugin", "name": rest.strip(), "spec": spec}
    if kind == "ini":
        parts = rest.split(":", 2)
        if len(parts) != 3 or "=" not in parts[2]:
            raise ValueError("ini spec is ini:<Stem>:<Section>:<Key>=<Value>: " + spec)
        stem, section, kv = parts
        key, value = kv.split("=", 1)
        key = key.strip()
        is_list = key.startswith("+")
        if is_list:
            key = key[1:]
        return {"kind": "ini", "stem": stem.strip(), "section": section.strip(), "key": key,
                "value": value.strip(), "is_list": is_list, "spec": spec}
    if kind == "cvar":
        if "=" not in rest:
            raise ValueError("cvar spec is cvar:<name>=<value>: " + spec)
        name, value = rest.split("=", 1)
        return {"kind": "cvar", "name": name.strip(), "value": value.strip(), "spec": spec}
    raise ValueError("unknown spec kind '%s' in %s" % (kind, spec))


def load_catalog(path):
    return read_json(path)


def expand_features(catalog, feature_names):
    specs, notes, unknown = [], [], []
    aliases = catalog.get("aliases", {})
    features = catalog.get("features", {})
    seen = set()
    for raw in feature_names:
        name = raw.strip().lower()
        if not name:
            continue
        name = aliases.get(name, name)
        entry = features.get(name)
        if entry is None:
            unknown.append(raw)
            continue
        for spec in entry.get("requires", []):
            if spec not in seen:
                seen.add(spec)
                specs.append((spec, name))
        for note in entry.get("notes", []):
            notes.append((name, note))
    return specs, notes, unknown


# ----------------------------------------------------------------------------
# Evaluation
# ----------------------------------------------------------------------------

def ini_path_for(project_dir, stem):
    if stem.lower().startswith("default"):
        return os.path.join(project_dir, "Config", stem + ".ini")
    return os.path.join(project_dir, "Saved", "Config", "WindowsEditor", stem + ".ini")


def effective_plugins(declared, descriptors):
    """Offline view of what the next launch enables: .uproject entries, descriptor
    defaults, then the transitive closure over each enabled plugin's dependencies.
    Returns name -> reason string."""
    enabled = {}
    for name, entry in declared.items():
        if entry.get("Enabled", True):
            enabled[name] = ".uproject"
    for name, desc in descriptors.items():
        if desc["enabled_by_default"] and name not in declared:
            enabled[name] = "descriptor default"
    queue = list(enabled)
    while queue:
        parent = queue.pop()
        for dep in descriptors.get(parent, {}).get("deps", []):
            if dep and dep not in enabled and dep in descriptors:
                if declared.get(dep, {}).get("Enabled", True) is False:
                    continue  # explicitly disabled in the .uproject wins
                enabled[dep] = "dependency of " + parent
                queue.append(dep)
    return enabled


def evaluate(specs, uproject, project_dir, descriptors, live):
    """Returns a list of result dicts, one per spec."""
    project = read_json(uproject)
    declared = {p.get("Name"): p for p in project.get("Plugins", [])}
    effective = effective_plugins(declared, descriptors)
    ini_cache = {}
    results = []
    for spec_text, feature in specs:
        req = parse_spec(spec_text)
        res = {"spec": spec_text, "feature": feature, "kind": req["kind"], "restart": False,
               "status": STATUS_UNKNOWN, "current": "", "fix": ""}
        if req["kind"] == "plugin":
            name = req["name"]
            desc = descriptors.get(name)
            decl = declared.get(name)
            if name in effective:
                disk_enabled = True
                disk_source = effective[name]
            elif decl is not None:
                disk_enabled = False
                disk_source = ".uproject Enabled=false"
            elif desc is not None:
                disk_enabled = False
                disk_source = "off by default"
            else:
                disk_enabled = False
                disk_source = "not declared"
            res["current"] = ("enabled" if disk_enabled else "disabled") + " (" + disk_source + ")"
            if live is not None:
                live_enabled = name in live.get("enabled_plugins", [])
                res["current"] += "; live " + ("enabled" if live_enabled else "disabled")
                if live_enabled and not disk_enabled:
                    # enabled through a dependency chain the offline view cannot see
                    disk_enabled = True
            if desc is None and decl is None:
                res["status"] = STATUS_NOT_IN_ENGINE
                res["fix"] = "install %s (Fab / project Plugins folder), then enable it in the .uproject" % name
                res["restart"] = True
            elif disk_enabled:
                res["status"] = STATUS_OK
            else:
                res["status"] = STATUS_MISSING
                res["fix"] = 'add {"Name": "%s", "Enabled": true} to Plugins in the .uproject' % name
                res["restart"] = True
            if desc is not None:
                flags = [f for f, on in (("experimental", desc["experimental"]), ("beta", desc["beta"])) if on]
                if flags:
                    res["current"] += " [" + ",".join(flags) + "]"
        elif req["kind"] == "ini":
            # First stem is where --apply writes; later stems (after '|') are
            # accepted read-only fallbacks, e.g. the per-user Saved config.
            stems = req["stem"].split("|")
            path = ini_path_for(project_dir, stems[0])
            current = None
            found_in = None
            for stem in stems:
                candidate = ini_path_for(project_dir, stem)
                if candidate not in ini_cache:
                    lines, _, _ = ini_read(candidate)
                    ini_cache[candidate] = ini_sections(lines)
                value = ini_current(ini_cache[candidate], req["section"], req["key"], req["is_list"])
                if value:
                    current, found_in = value, stem
                    break
            if current is None:
                current = [] if req["is_list"] else None
            target = "[%s] %s%s=%s" % (req["section"], "+" if req["is_list"] else "", req["key"], req["value"])
            if req["is_list"]:
                res["current"] = "+".join(current) if current else "(absent)"
                if any(norm_value(v) == norm_value(req["value"]) for v in current):
                    res["status"] = STATUS_OK
                else:
                    res["status"] = STATUS_MISSING
                    res["fix"] = "%s: append %s" % (os.path.basename(path), target)
                    res["restart"] = True
            else:
                res["current"] = current if current is not None else "(absent)"
                if current is None:
                    res["status"] = STATUS_MISSING
                    res["fix"] = "%s: add %s" % (os.path.basename(path), target)
                    res["restart"] = True
                elif norm_value(current) == norm_value(req["value"]):
                    res["status"] = STATUS_OK
                else:
                    res["status"] = STATUS_MISMATCH
                    res["fix"] = "%s: set %s (currently %s)" % (os.path.basename(path), target, current)
                    res["restart"] = True
            if found_in and found_in != stems[0]:
                res["current"] += " (in %s.ini)" % found_in
            if not os.path.isfile(path) and res["status"] != STATUS_OK:
                res["current"] += " [file missing]"
        elif req["kind"] == "cvar":
            if live is None:
                res["status"] = STATUS_SKIPPED
                res["current"] = "not checkable offline (needs --live)"
            else:
                reading = live.get("cvars", {}).get(req["name"], {})
                if "error" in reading:
                    res["status"] = STATUS_UNKNOWN
                    res["current"] = reading["error"]
                else:
                    want = req["value"]
                    try:
                        matched = abs(float(want) - float(reading.get("float", 0.0))) < 1e-6
                    except ValueError:
                        matched = False
                    res["current"] = "int=%s float=%s" % (reading.get("int"), reading.get("float"))
                    res["status"] = STATUS_OK if matched else STATUS_MISMATCH
                    if not matched:
                        res["fix"] = "console: %s %s (volatile - persist it in the ini or an MRQ preset)" % (req["name"], want)
        results.append(res)
    return results


# ----------------------------------------------------------------------------
# Apply
# ----------------------------------------------------------------------------

def backup(path):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = path + ".bak_" + stamp
    shutil.copy2(path, dest)
    return dest


def apply_changes(results, uproject, project_dir):
    """Edits the .uproject and ini files for every non-OK plugin/ini result. Returns log lines."""
    log = []
    plugin_adds = [r for r in results if r["kind"] == "plugin" and r["status"] == STATUS_MISSING]
    if plugin_adds:
        project = read_json(uproject)
        plugins = project.setdefault("Plugins", [])
        by_name = {p.get("Name"): p for p in plugins}
        for res in plugin_adds:
            name = parse_spec(res["spec"])["name"]
            if name in by_name:
                by_name[name]["Enabled"] = True
                log.append("uproject: set Enabled=true on " + name)
            else:
                plugins.append({"Name": name, "Enabled": True})
                log.append("uproject: added " + name)
        dest = backup(uproject)
        log.append("backup: " + dest)
        with open(uproject, "w", encoding="utf-8") as handle:
            json.dump(project, handle, indent="\t")
            handle.write("\n")
    ini_edits = [r for r in results if r["kind"] == "ini" and r["status"] in (STATUS_MISSING, STATUS_MISMATCH)]
    by_path = {}
    for res in ini_edits:
        req = parse_spec(res["spec"])
        by_path.setdefault(ini_path_for(project_dir, req["stem"].split("|")[0]), []).append(req)
    for path, reqs in by_path.items():
        lines, bom, newline = ini_read(path)
        if os.path.isfile(path):
            log.append("backup: " + backup(path))
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            log.append("creating " + path)
        for req in reqs:
            sections = ini_sections(lines)  # re-parse: indices shift after each edit
            what = ini_apply(lines, sections, req["section"], req["key"], req["value"], req["is_list"])
            log.append("%s: %s -> %s%s=%s" % (os.path.basename(path), what, "+" if req["is_list"] else "", req["key"], req["value"]))
        ini_write(path, lines, bom, newline)
    for res in results:
        if res["status"] == STATUS_NOT_IN_ENGINE:
            log.append("NOT APPLIED (needs an install, not a config edit): " + res["spec"])
    return log


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

def print_table(results):
    widths = [max(len(r["spec"]) for r in results) if results else 10, 13, 58]
    print("%-*s  %-*s  %-*s  RESTART  FIX" % (widths[0], "REQUIREMENT", widths[1], "STATUS", widths[2], "CURRENT"))
    for res in results:
        current = res["current"][:widths[2]]
        print("%-*s  %-*s  %-*s  %-7s  %s" % (widths[0], res["spec"], widths[1], res["status"], widths[2], current,
                                             "yes" if res["restart"] else "-", res["fix"]))


def plan_block(results, notes, uproject, engine_root, live, editor_running_this_project):
    todo = [r for r in results if r["status"] in (STATUS_MISSING, STATUS_MISMATCH, STATUS_NOT_IN_ENGINE)]
    ok = [r for r in results if r["status"] == STATUS_OK]
    skipped = [r for r in results if r["status"] in (STATUS_SKIPPED, STATUS_UNKNOWN)]
    restart = any(r["restart"] for r in todo)
    out = []
    out.append("### Step 0 - Environment preflight (runs before step 1)")
    out.append("")
    out.append("- Project: `%s`" % uproject)
    out.append("- Engine root: `%s`" % (engine_root or "unresolved"))
    if live is not None:
        out.append("- Editor: RUNNING on %s (%s)" % ("this project" if editor_running_this_project else "A DIFFERENT PROJECT: " + live.get("project_file", "?"), live.get("engine_version", "?")))
    else:
        out.append("- Editor: not reached (offline check of the files the next launch will load)")
    out.append("")
    if todo:
        out.append("**Changes required (%d), restart needed: %s**" % (len(todo), "YES" if restart else "no"))
        for res in todo:
            out.append("- [%s] %s -> %s" % (res["status"], res["spec"], res["fix"]))
        out.append("")
        if restart:
            out.append("Restart plan (ONE restart for all of the above):")
            out.append("1. Save open levels and assets in the editor (unsaved component edits do not survive a restart).")
            out.append("2. Close the editor - the operator does this, the agent never kills a live editor.")
            out.append("3. `ue_preflight.py --project <uproject> --features <same list> --apply` (backs up .uproject and ini first).")
            out.append("4. Relaunch the editor; wait for the MCP server on the configured port.")
            out.append("5. `ue_preflight.py --live --features <same list>` must report 0 changes - that read-back is the gate for step 1.")
    else:
        out.append("**No changes required - every requirement read back OK.**")
    if skipped:
        out.append("")
        out.append("Not verified (%d): %s" % (len(skipped), ", ".join(r["spec"] for r in skipped)))
    if ok:
        out.append("")
        out.append("Already satisfied (%d): %s" % (len(ok), ", ".join(r["spec"] for r in ok)))
    if notes:
        out.append("")
        out.append("Feature notes to carry into the plan:")
        for feature, note in notes:
            out.append("- (%s) %s" % (feature, note))
    return "\n".join(out)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Unreal project preflight: plugins + project settings a plan needs, checked before step 1.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument("--project", help="path to the .uproject (omit with --live to use the editor's open project)")
    parser.add_argument("--live", action="store_true", help="query the running editor via MCP for its project, enabled plugins and CVars")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL, help="UE MCP endpoint (default %(default)s)")
    parser.add_argument("--engine-root", help="engine install root (else UE_ENGINE_ROOT, else registry via EngineAssociation)")
    parser.add_argument("--catalog", default=CATALOG_PATH, help="requirements catalog JSON (default: the skill's reference copy)")
    parser.add_argument("--features", default="", help="comma-separated catalog features, e.g. megaplants,pcg,mrq")
    parser.add_argument("--require", action="append", default=[], help="ad-hoc requirement spec (repeatable)")
    parser.add_argument("--list-features", action="store_true", help="print the catalog features and exit")
    parser.add_argument("--plan-block", action="store_true", help="print the markdown Step 0 block for the plan")
    parser.add_argument("--json", help="write the full result to this JSON file")
    parser.add_argument("--apply", action="store_true", help="edit the .uproject / ini files to satisfy MISSING and MISMATCH rows (backs up first)")
    parser.add_argument("--apply-while-running", action="store_true", help="allow --apply even though the editor has this project open")
    parser.add_argument("--timeout", type=int, default=60, help="seconds for the live probe (default %(default)s)")
    args = parser.parse_args()

    try:
        catalog = load_catalog(args.catalog)
    except Exception as exc:
        print("ERROR: cannot read catalog %s: %s" % (args.catalog, exc))
        return 2

    if args.list_features:
        for name, entry in sorted(catalog.get("features", {}).items()):
            print("%-20s %s" % (name, entry.get("summary", "")))
        aliases = catalog.get("aliases", {})
        if aliases:
            print("aliases: " + ", ".join("%s->%s" % kv for kv in sorted(aliases.items())))
        return 0

    feature_names = [f for f in args.features.split(",") if f.strip()]
    specs, notes, unknown = expand_features(catalog, feature_names)
    for spec in args.require:
        parse_spec(spec)  # validate early
        specs.append((spec, "ad-hoc"))
    if unknown:
        print("ERROR: unknown feature(s) %s - see --list-features" % ", ".join(unknown))
        return 2
    if not specs:
        print("ERROR: nothing to check - pass --features and/or --require")
        return 2

    cvar_names = [parse_spec(s)["name"] for s, _ in specs if s.startswith("cvar:")]

    live = None
    live_error = None
    if args.live:
        try:
            live = live_probe(args.mcp_url, cvar_names, timeout=args.timeout)
        except Exception as exc:
            live_error = str(exc)
            print("WARN: live probe failed (%s) - continuing offline" % live_error[:200])

    uproject = args.project
    if not uproject and live is not None:
        uproject = live.get("project_file")
    if not uproject:
        print("ERROR: no project - pass --project, or --live with the editor running")
        return 2
    uproject = os.path.abspath(uproject)
    if not os.path.isfile(uproject):
        print("ERROR: .uproject not found: " + uproject)
        return 2
    project_dir = os.path.dirname(uproject)

    editor_running_this_project = False
    if live is not None:
        live_project = os.path.abspath(live.get("project_file", "") or "")
        editor_running_this_project = os.path.normcase(live_project) == os.path.normcase(uproject)
        if not editor_running_this_project:
            print("WARN: the running editor has %s open, NOT %s - live plugin/CVar readings below describe the OTHER project"
                  % (live.get("project_file"), uproject))
            live_for_eval = None
        else:
            live_for_eval = live
    else:
        live_for_eval = None

    engine_root, engine_source = resolve_engine_root(uproject, args.engine_root)
    descriptors = index_plugin_descriptors(engine_root, project_dir)

    print("project     : " + uproject)
    print("engine root : %s  (%s; %d plugin descriptors indexed)" % (engine_root or "UNRESOLVED", engine_source, len(descriptors)))
    if live is not None:
        print("live editor : %s  project=%s  enabled plugins=%d" % (live.get("engine_version"), live.get("project_file"), len(live.get("enabled_plugins", []))))
    elif args.live:
        print("live editor : unreachable at " + args.mcp_url)
    else:
        print("live editor : not queried (offline check; add --live for the read-back)")
    if not engine_root:
        print("WARN: engine root unresolved - plugins not declared in the .uproject will read as NOT_IN_ENGINE; pass --engine-root")
    print("")

    try:
        results = evaluate(specs, uproject, project_dir, descriptors, live_for_eval)
    except Exception as exc:
        print("ERROR: evaluation failed: " + str(exc))
        return 2

    print_table(results)
    todo = [r for r in results if r["status"] in (STATUS_MISSING, STATUS_MISMATCH, STATUS_NOT_IN_ENGINE)]
    restart = any(r["restart"] for r in todo)
    print("")
    print("summary     : %d checked, %d ok, %d need changes, %d not verified; restart needed: %s"
          % (len(results), sum(1 for r in results if r["status"] == STATUS_OK), len(todo),
             sum(1 for r in results if r["status"] in (STATUS_SKIPPED, STATUS_UNKNOWN)), "YES" if restart else "no"))

    if args.plan_block:
        print("")
        print(plan_block(results, notes, uproject, engine_root, live, editor_running_this_project))

    if args.apply:
        if not todo:
            print("apply       : nothing to apply")
        elif editor_running_this_project and not args.apply_while_running:
            print("apply       : REFUSED - the editor has this project open; close it first (or --apply-while-running, and know the editor may overwrite the files on exit)")
            return 1
        else:
            print("")
            for line in apply_changes(results, uproject, project_dir):
                print("apply       : " + line)
            print("apply       : done - relaunch the editor, then re-run with --live to read the result back")

    if args.json:
        payload = {"project": uproject, "engine_root": engine_root, "live": live, "live_error": live_error,
                   "editor_running_this_project": editor_running_this_project, "results": results,
                   "notes": notes, "restart_needed": restart}
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=1)
        print("json        : " + args.json)

    return 1 if todo else 0


if __name__ == "__main__":
    sys.exit(main())
