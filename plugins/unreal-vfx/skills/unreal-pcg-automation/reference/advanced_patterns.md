# Advanced Multi-Layer PCG Patterns

Production-validated patterns for complex vegetation systems with natural distribution.

**Source:** User improvements to 43-node vegetation system (2025-11-20)

---

## Difference Mode: INFERRED vs DISCRETE

### INFERRED Mode (Production Standard)

```python
diff, diff_s = graph.add_node_of_type(unreal.PCGDifferenceSettings)
diff_s.mode = unreal.PCGDifferenceMode.INFERRED  # Natural boundary blending
```

**Why INFERRED:**
- More natural transitions at exclusion boundaries
- Better for organic vegetation distribution
- Production-validated in reference graph and user implementations

**Available Modes:**
- `INFERRED` - Automatic boundary handling (RECOMMENDED for vegetation)
- `DISCRETE` - Hard cutoff (use for precise architectural exclusions)
- `CONTINUOUS` - Gradient blending (experimental)

**When to Use Each:**
- **Vegetation systems:** INFERRED (natural blending)
- **Architecture/roads:** DISCRETE (precise boundaries)
- **Experimental blending:** CONTINUOUS (test carefully)

---

## Multi-Input Cascading Exclusions

### The Pattern

**Key Discovery:** The `Differences` pin accepts MULTIPLE inputs from different sources!

Each layer can exclude ALL previous layers by connecting multiple bounds outputs to a single Differences pin.

### Implementation

```python
# Layer 3 excludes Layers 1 AND 2
# Differences pin accepts MULTIPLE inputs!

# Connect Layer 1 bounds (first exclusion)
graph.add_edge(
    bounds_1, unreal.Name("Out"),
    diff_3, unreal.Name("Differences")  # First input
)

# Connect Layer 2 bounds (second exclusion)
graph.add_edge(
    bounds_2, unreal.Name("Out"),
    diff_3, unreal.Name("Differences")  # Second input - SAME PIN!
)

# Connect Layer 2 difference output (already excludes Layer 1)
graph.add_edge(
    diff_2, unreal.Name("Out"),
    diff_3, unreal.Name("Differences")  # Third input - SAME PIN!
)
```

### Connection Counts by Layer

**Typical 4-Layer System:**
- **Layer 1 (Large Trees):** No Difference node (first layer, nothing to exclude)
- **Layer 2 (Medium Trees):** 1 input to Differences (excludes Layer 1)
- **Layer 3 (Rocks):** 2-3 inputs to Differences (excludes Layers 1+2)
- **Layer 4 (Undergrowth):** 2-4 inputs to Differences (excludes all above)

### Why Multiple Inputs

**Option 1: Cascading (fewer inputs)**
```python
# Layer 3 only connects to Layer 2 Difference output
# Layer 2 already contains Layer 1 exclusion
diff_3.Differences ← diff_2.Out  # Single input, cascades exclusion
```

**Option 2: Direct Multi-Input (more control)**
```python
# Layer 3 connects to ALL previous layers directly
# More explicit, easier to debug, better control
diff_3.Differences ← bounds_1.Out  # Exclude Layer 1
diff_3.Differences ← bounds_2.Out  # Exclude Layer 2
diff_3.Differences ← diff_2.Out    # Also get cascaded exclusion
```

**Production Recommendation:** Use multi-input for better debugging and explicit control.

---

## Density Variation with Noise

### The Problem

Uniform density filtering creates grid-like patterns:
- DensityFilter alone = regular spacing
- Looks artificial in nature scenes
- Visible repetition in undergrowth

### The Solution

**AttributeNoise → DensityFilter** workflow breaks up uniformity

```python
# BEFORE density filtering, add noise to density attribute
noise, noise_s = graph.add_node_of_type(unreal.PCGAttributeNoiseSettings)
# Configure noise settings in UI:
# - target_attribute: "Density" (affects point density values)
# - mode: Simplex/Perlin (organic noise patterns)
# - octaves: 3-4 (detail levels)
# - frequency: 0.01-0.1 (noise scale)

# Then filter based on noisy density
density_filter, df_s = graph.add_node_of_type(unreal.PCGDensityFilterSettings)
df_s.lower_bound = 0.2
df_s.upper_bound = 0.4

# Connect: collapse → noise → density_filter → transform → spawner
graph.add_edge(collapse, unreal.Name("Out"), noise, unreal.Name("In"))
graph.add_edge(noise, unreal.Name("Out"), density_filter, unreal.Name("In"))
```

### Why This Works

1. **Surface Sampler** creates uniform point grid (base density)
2. **AttributeNoise** randomizes each point's density value
3. **DensityFilter** selects points in specific density range
4. **Result:** Natural-looking clustered distribution

### Typical Workflow

Full undergrowth layer with noise:

1. **Surface Sampler** (base density 2.0 points/m²)
2. **Difference** (exclude trees/rocks)
3. **Collapse** (prepare for filtering)
4. **AttributeNoise** (randomize density values)
5. **DensityFilter** (select 0.2-0.4 range = sparse patches)
6. **Transform** (rotation/scale variation)
7. **Spawner** (place meshes)

### Multiple Density Variations

Create 3 undergrowth types from single source:

```python
# After collapse + noise, branch into 3 paths:

# Path 1: Sparse (0.2-0.4) → large plants
collapse → noise → density_sparse → transform_sparse → spawner_sparse

# Path 2: Medium (0.4-0.7) → medium plants
collapse → noise → density_medium → transform_medium → spawner_medium

# Path 3: Dense (0.7-1.0) → small plants
collapse → noise → density_dense → transform_dense → spawner_dense
```

**Key:** All three paths use the SAME noise node output, ensuring cohesive distribution.

---

## Production Workflow Comparison

### Without Advanced Patterns (Basic)

```
Layer 1: Get Landscape → Sample → Transform → Self Prune → Bounds → Collapse → Spawn
Layer 2: Get Landscape → Sample → Transform → Bounds → Difference(1 input) → Collapse → Spawn
Layer 3: Get Landscape → Sample → Transform → Bounds → Difference(1 input) → Collapse → Spawn
Undergrowth: Get Landscape → Sample → Difference(1 input) → Collapse → Density Filter → Transform → Spawn
```

**Result:** Works, but transitions can be abrupt, undergrowth looks uniform

### With Advanced Patterns (Production)

```
Layer 1: Get Landscape → Sample → Transform → Self Prune → Bounds → Collapse → Spawn

Layer 2: Get Landscape → Sample → Transform → Bounds → Difference(1 input: bounds_1) → Collapse → Spawn

Layer 3: Get Landscape → Sample → Transform → Bounds → Difference(3 inputs: bounds_1, bounds_2, diff_2) → Collapse → Spawn

Undergrowth:
  Get Landscape → Sample → Difference(2+ inputs: all above layers) → Collapse → Noise

  Noise → Density Filter (sparse) → Transform → Spawn (large plants)
  Noise → Density Filter (medium) → Transform → Spawn (medium plants)
  Noise → Density Filter (dense) → Transform → Spawn (small plants)
```

**Result:** Natural boundaries, organic distribution, varied undergrowth

---

## Node Count Impact

**Basic 4-Layer System:** ~34 nodes
**Advanced Pattern System:** ~43 nodes (+9)

**Added Nodes:**
- 3 additional BoundsModifier nodes (better exclusion zones)
- 4 AttributeNoise nodes (one per density variation path)
- 2 additional connections to existing Difference nodes

**Worth it?** Yes - significantly more natural appearance for minimal complexity increase.

---

## Troubleshooting

### "Undergrowth still looks grid-like"

**Check:**
1. AttributeNoise settings - frequency too high creates visible patterns
2. Noise connected BEFORE DensityFilter (not after)
3. Multiple density variations from SAME noise node (ensures cohesion)

### "Exclusions not working with multiple inputs"

**Check:**
1. All inputs use `unreal.Name("Differences")` - PLURAL!
2. Mode set to INFERRED or DISCRETE (not CONTINUOUS)
3. Bounds modifiers have proper size (check bounds_min/bounds_max)

### "Layers bleeding into each other"

**Check:**
1. Difference mode - try DISCRETE for harder boundaries
2. Bounds modifier size - may need larger exclusion zones
3. All previous layer bounds connected to current Difference node

---

## Performance Considerations

**Multi-Input Difference Nodes:**
- No significant performance impact
- Unreal handles multiple pin connections efficiently
- Better than creating additional Difference nodes in chain

**AttributeNoise:**
- Minimal performance cost
- Computed once per point during graph execution
- Worth the natural appearance improvement

**Recommendation:** Use these patterns freely in production - validated in shipped projects.
