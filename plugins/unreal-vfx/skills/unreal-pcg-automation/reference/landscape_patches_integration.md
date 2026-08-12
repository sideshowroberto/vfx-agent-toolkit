# Landscape Patches Integration

**Plugin:** LandscapePatch (Experimental in UE 5.5)
**Use Case:** Procedural landscape deformation without manual sculpting

---

## Overview

LandscapeCircleHeightPatch allows PCG to deform landscapes procedurally. Spawned at each point, patches blend together to create roads, rivers, trenches, etc.

---

## Setup Blueprint

### Create Patch Blueprint (Manual - One Time)

**Steps:**
1. Content Browser -> Add -> Blueprint Class
2. Parent: Actor
3. Name: BP_LandscapePatch
4. Open Blueprint
5. Add Component -> LandscapeCircleHeightPatch
6. Configure in Details:
   - Radius: 10cm (will scale via PCG)
   - Falloff: 100cm (blend distance)
   - Height Encoding: ZeroToOne
   - Edit Layer: None
7. Save

**Why Manual:** Python `set_component_property()` + `save_loaded_asset()` crashes in UE 5.5

---

## Use in PCG

### Spawn Actor Configuration

```python
# Load Blueprint
bp = unreal.load_asset('/Game/Blueprints/BP_LandscapePatch')

# Configure Spawn Actor node
spawn_node, spawn_settings = graph.add_node_of_type(unreal.PCGSpawnActorSettings)
spawn_settings.template_actor_class = bp.generated_class()
spawn_settings.option = unreal.EPCGSpawnActorOption.COLLAPSEACTOR
```

---

## Parameters

### Radius
**Property:** `radius` (float, in cm)
**Effect:** Size of deformation circle
**Typical Values:**
- Roads: 150-300cm (1.5-3m)
- Rivers: 200-500cm (2-5m)
- Paths: 100-200cm (1-2m)

### Falloff
**Property:** `falloff` (float, in cm)
**Effect:** Blend distance to surrounding terrain
**Typical Values:**
- Smooth blend: 50-100cm
- Sharp edge: 10-30cm
- Very gradual: 100-200cm

### Height Encoding
**Property:** `height_encoding`
**Options:**
- ZERO_TO_ONE: 0 = low, 1 = high (most common)
- NATIVE: Direct height values
- WORLD_UNITS: Height in world space

---

## Workflow: Road Creation

```
1. Spline defines road path
2. Spline Sampler: 100cm spacing
3. Projection: Project to landscape
4. Transform Points: Offset -30cm (carve into terrain)
5. Spawn Actor: BP_LandscapePatch at each point
6. Result: Road-shaped depression
```

**Performance:** 100m road = ~100 patches = <1 second generation

---

## Troubleshooting

**Issue: Patches visible but no deformation**
- Check: Landscape Patches plugin enabled
- Check: Edit Layer set correctly (None for main layer)
- Check: Height Encoding matches use case

**Issue: Visible seams between patches**
- Increase Falloff distance
- Decrease Sampler distance_increment
- Ensure patches overlap

**Issue: Deformation too deep/shallow**
- Adjust Transform Points Z offset
- Modify patch Radius

---

## Reference

**Plugin Docs:** Edit -> Plugins -> Search "Landscape Patch" -> Documentation
**Session:** `Session_2025-10-26_PCG_LandscapeDeformation.md`
