# Property Verification Workflow

**Version:** 1.5.0
**Last Updated:** 2025-11-17
**Context:** Critical workflow for ensuring property settings succeed via Python API

Extracted from unreal-pcg-automation skill for on-demand reference.

---

## Critical Lesson: Timeout ≠ Success!

When setting properties via Python API, Silent Execution timeouts only mean "async operation started" - **NOT** "operation succeeded". Always verify critical settings.

---

## The Problem

```python
# ❌ WRONG: Assume timeout = success
spline_settings = graph.nodes[0].get_settings()
actor_selector = spline_settings.actor_selector

# Set properties
actor_selector.actor_selection = unreal.PCGActorSelection.BY_CLASS
actor_selector.actor_selection_class = unreal.Landscape

# Got timeout → assumed it worked → WRONG!
# Properties may not have been set correctly!
```

**What Actually Happens:**
- MCP sends Python command to Unreal
- Unreal starts async operation
- MCP timeout occurs before operation completes
- **Properties may not stick** due to:
  - Property validation failures
  - Asset state conflicts
  - Editor subsystem locks
  - Deferred property updates

---

## The Solution: Always Verify

```python
# ✅ CORRECT: Set → Verify → Confirm

# Phase 1: Set properties
actor_selector.actor_selection = unreal.PCGActorSelection.BY_CLASS
actor_selector.actor_selection_class = unreal.Landscape

# Phase 2: Check Unreal log for errors (separate script!)
import os, glob

log_dir = "<workspace>/UnrealEngine/MCPGameProject/Saved/Logs"
logs = glob.glob(f"{log_dir}/*.log")
latest_log = max(logs, key=os.path.getmtime)

# Read last 50 lines for errors
with open(latest_log, 'r', encoding='utf-8') as f:
    for line in f.readlines()[-50:]:
        if 'Error:' in line or 'Exception' in line or 'Warning:' in line:
            print(line.strip())

# Phase 3: Read properties back to confirm (separate script!)
graph = unreal.load_asset('/Game/PCG/MyGraph')
actor_selector = graph.nodes[0].get_settings().actor_selector

print(f"✓ Verified actor_selection: {actor_selector.actor_selection}")
print(f"✓ Verified actor_selection_class: {actor_selector.actor_selection_class}")
```

---

## When to Verify

### Always verify after:

**1. Setting actor selector properties**
   - `actor_selection` (BY_CLASS, ALL_WORLD_ACTORS, etc.)
   - `actor_selection_class` (Landscape, StaticMeshActor, etc.)
   - `actor_selection_tag` (tag-based filtering)

**2. Setting complex nested properties**
   - `sampler_params` on Spline Sampler
   - `projection_params` on Projection node
   - `spawn_params` on Spawn Actor node

**3. Getting timeouts on critical settings**
   - Any timeout after setting a property you'll rely on
   - Properties that affect graph behavior

**4. Any property requiring UI configuration**
   - Mesh spawner meshes (read-only via Python)
   - Material parameters
   - Blueprint references

### Don't need to verify:

**1. Simple numeric properties**
   - `distance_increment` (float)
   - `points_per_squared_meter` (float)
   - `interior_sample_spacing` (float)

**2. Vector/Rotator values**
   - `offset_min` / `offset_max`
   - `rotation_min` / `rotation_max`
   - Transform settings

**3. Boolean flags**
   - `unbounded` (True/False)
   - `absolute_scale` (True/False)
   - Simple toggles

**Rule of Thumb:** If it's a complex object reference or enum, verify. If it's a simple value type, don't worry.

---

## Real-World Example: Landscape Spline Detection

**Problem:** Get Spline Data node not finding landscape spline.

**Cause:** Actor selector properties not set correctly (timeout assumed success).

**Solution:**
```python
# 1. Set properties
actor_selector.actor_selection = unreal.PCGActorSelection.BY_CLASS
actor_selector.actor_selection_class = unreal.Landscape

# 2. Verify in separate script
graph = unreal.load_asset('/Game/PCG/RoadGraph')
settings = graph.nodes[0].get_settings()

if settings.actor_selector.actor_selection == unreal.PCGActorSelection.BY_CLASS:
    print("✓ Actor selection correctly set")
else:
    print("✗ Actor selection NOT set - need to configure in UI")

# 3. If verification fails, configure manually in UI
# Open graph → Select Get Spline Data node → Details panel
# Actor Selector → Actor Selection: By Class
# Actor Selection Class: Landscape
```

**Result:** Once configured in UI (after Python set failed), spline detection worked perfectly.

**Key Insight:** The timeout didn't mean failure - it meant "async operation may or may not have succeeded." Verification revealed the truth.

---

## Verification Checklist

Use this checklist when setting critical properties:

- [ ] Set properties via Python
- [ ] Check Unreal log for errors/warnings
- [ ] Read properties back to confirm values
- [ ] If verification fails, configure in UI
- [ ] Re-verify after UI changes
- [ ] Test graph execution to confirm behavior

**Remember:** Silent Execution is a feature for async graph creation, not a guarantee of property setting success!

---

## Log Checking Pattern

**Find Latest Log:**
```python
import os, glob

log_dir = "<workspace>/UnrealEngine/MCPGameProject/Saved/Logs"
logs = glob.glob(f"{log_dir}/*.log")
latest_log = max(logs, key=os.path.getmtime) if logs else None
print(f"Latest log: {latest_log}")
```

**Read Errors:**
```python
with open(latest_log, 'r', encoding='utf-8') as f:
    for line in f.readlines()[-100:]:  # Last 100 lines
        if any(keyword in line for keyword in ['Error:', 'Warning:', 'Exception', 'Failed']):
            print(line.strip())
```

**Look for PCG-specific errors:**
```python
with open(latest_log, 'r', encoding='utf-8') as f:
    for line in f.readlines()[-100:]:
        if 'LogPCG' in line and ('Error' in line or 'Warning' in line):
            print(line.strip())
```

---

## Property Readback Pattern

**Single Property:**
```python
graph = unreal.load_asset('/Game/PCG/MyGraph')
settings = graph.nodes[0].get_settings()

# Read specific property
value = settings.property_name
print(f"Current value: {value}")
```

**Nested Property:**
```python
# Example: Sampler params
sampler_settings = graph.nodes[1].get_settings()
distance = sampler_settings.sampler_params.distance_increment
print(f"Distance increment: {distance}")
```

**Actor Selector:**
```python
get_spline_settings = graph.nodes[0].get_settings()
selector = get_spline_settings.actor_selector

print(f"Selection mode: {selector.actor_selection}")
print(f"Selection class: {selector.actor_selection_class}")
print(f"Selection tag: {selector.actor_selection_tag}")
```

---

## Why This Matters

**Production Context:**
- Building car commercial environment (road + props)
- Landscape spline detection critical for workflow
- Python set appeared to succeed (timeout occurred)
- Graph didn't work - spline not detected
- Verification revealed actor selector not set
- UI configuration fixed the issue

**Without Verification:**
- Would've assumed Python set succeeded
- Would've debugged graph structure, connections, etc.
- Would've wasted hours troubleshooting wrong layer

**With Verification:**
- Identified root cause in 2 minutes
- Fixed via UI configuration
- Confirmed fix via re-verification
- Graph worked perfectly

**Lesson:** Trust, but verify. Timeout is not confirmation.

---

**End of Property Verification Reference**
