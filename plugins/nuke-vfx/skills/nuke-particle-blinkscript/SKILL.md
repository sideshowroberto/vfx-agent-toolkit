---
name: nuke-particle-blinkscript
description: ParticleBlinkScript node development for NukeX 16+ - custom particle systems, GPU particle physics, and Foundry gadget templates. Also covers procedural BlinkScript atmospheric effects (snow, embers, dust) that bypass the particle system entirely. Use when user mentions particle blinkscript, ParticleBlinkScript node, custom particles nuke, blinkscript particles, GPU particles nuke, particle gadgets, procedural snow nuke, atmospheric blinkscript.
allowed-tools: Read,Write,Bash
---

# nuke-particle-blinkscript

**Version:** 1.0.0
**Last Updated:** 2026-03-11
**Dependencies:** NukeX 16+ (for ParticleBlinkScript node) OR Nuke 13+ (for procedural BlinkScript approach)

---

## Two Approaches - Choose Based on What You Have

| Approach | Nuke Version | Node Used | What You Get |
|----------|-------------|-----------|--------------|
| **Procedural BlinkScript** | Nuke 13+, any license | `BlinkScript` (ImageComputationKernel) | GPU math-only particles - no sim, no caching, real-time |
| **ParticleBlinkScript node** | NukeX 16+ only | `ParticleBlinkScript` | Real particle physics, Foundry gadget library, Blink API |

**Decision rule:**
- Need real physics (gravity, collisions, inter-particle forces)? -> ParticleBlinkScript node (NukeX 16+)
- Need atmospheric effects (snow, embers, sparks, dust)? -> Procedural BlinkScript (any Nuke, faster, easier)
- Don't have NukeX 16+? -> Procedural BlinkScript is your only option

---

## Approach 1: Procedural BlinkScript (Any Nuke)

No particle node required. Mathematically generates particle positions per-frame using noise, sin/cos, and pseudo-random seeds. GPU-accelerated, zero caching, compositing-friendly.

**Why this approach:**
- No simulation time - renders immediately
- No caching - always current frame
- Works in any Nuke license
- Easily keyframable and art-directable

### Core Pattern: Procedural Particles

```cpp
kernel ProceduralParticles : ImageComputationKernel<ePixelWise>
{
  Image<eRead, eAccessPoint, eEdgeClamped> src;
  Image<eWrite, eAccessPoint> dst;

  param:
    float time;           // Wire to frame/fps expression
    float count;          // Number of particles
    float size;           // Particle radius in pixels
    float4 color;         // Particle color (creates color picker)
    float speed;          // Fall/drift speed
    float spread;         // Horizontal spread

  local:
    int imgWidth;
    int imgHeight;
    float invWidth;
    float invHeight;

  void init() {
    imgWidth = dst.bounds.width();
    imgHeight = dst.bounds.height();
    invWidth = 1.0f / (float)imgWidth;
    invHeight = 1.0f / (float)imgHeight;
  }

  // Deterministic pseudo-random from seed
  float rand(float seed) {
    return fmod(sin(seed * 127.1f + 311.7f) * 43758.5453f, 1.0f);
  }

  void process(int2 pos) {
    float4 output = src();
    float px = (float)pos.x;
    float py = (float)pos.y;

    for (int i = 0; i < (int)count; i++) {
      float fi = (float)i;

      // Each particle gets a unique seed-based starting position
      float startX = rand(fi * 1.7f) * (float)imgWidth;
      float lane = rand(fi * 3.1f) * spread;  // Horizontal drift

      // Y position driven by time (wraps when off screen)
      float yOffset = fmod(rand(fi * 2.3f) + time * speed * (0.5f + rand(fi * 0.9f) * 0.5f), 1.0f);
      float particleX = startX + sin(time * 0.5f + fi) * lane;
      float particleY = yOffset * (float)imgHeight;

      // Wrap particle back to top when it exits bottom
      if (particleY > (float)imgHeight) {
        particleY = fmod(particleY, (float)imgHeight);
      }

      // Distance test (circular particle)
      float dx = px - particleX;
      float dy = py - particleY;
      float dist = sqrt(dx * dx + dy * dy);

      if (dist < size) {
        // Soft edge fade
        float alpha = (1.0f - dist / size) * color.w;
        output.x = output.x * (1.0f - alpha) + color.x * alpha;
        output.y = output.y * (1.0f - alpha) + color.y * alpha;
        output.z = output.z * (1.0f - alpha) + color.z * alpha;
      }
    }

    dst() = output;
  }
};
```

**Expression for time parameter:**
```
# In the Nuke expression field for the time param:
frame / fps
```

### BugSwarm Pattern (Community Reference)

The BugSwarm gadget (community-developed, NukeX 16+) demonstrates a similar approach using the ParticleBlinkScript node with swarm/flock behavior. The procedural version above replicates the concept without requiring NukeX.

Key differences from BugSwarm:
- BugSwarm uses ParticleBlinkScript (real particles, inter-particle awareness)
- Procedural version uses independent math per-particle (no inter-awareness, but simpler and faster)

### Snowfall Variant

```cpp
// Replace the particle section with:
float swayAmt = sin(time * 0.8f + fi * 4.2f) * spread;
float particleX = startX + swayAmt;
float particleY = fmod(rand(fi * 2.3f) + time * speed * (0.3f + rand(fi * 0.9f) * 0.4f), 1.0f) * (float)imgHeight;

// Snowflake shape: softer edge, slightly elliptical
float dx = px - particleX;
float dy = py - particleY;
float dist = sqrt(dx * dx * 0.8f + dy * dy);  // Slight horizontal compression
```

### Embers/Sparks Variant

```cpp
// Embers rise, drift, and fade
float riseSpeed = speed * (0.5f + rand(fi * 1.1f) * 1.5f);
float particleX = startX + sin(time * 1.2f + fi * 2.7f) * spread;
// Embers rise (y decreases in Nuke's coordinate system)
float particleY = (float)imgHeight - fmod(rand(fi * 2.3f) + time * riseSpeed, 1.0f) * (float)imgHeight;

// Flicker: vary alpha over time
float flicker = 0.5f + 0.5f * sin(time * 8.0f + fi * 13.7f);
float alpha = flicker * color.w * (1.0f - dist / size);
```

---

## Approach 2: ParticleBlinkScript Node (NukeX 16+)

A dedicated node type introduced in Nuke 16. Separate from the regular `BlinkScript` node - uses a different kernel declaration and is only available in NukeX.

### Accessing the Node

1. Tab menu -> search "ParticleBlinkScript"
2. Or: Particles menu -> ParticleBlinkScript
3. The node ships with 14 Foundry gadgets as starting templates

### Kernel Structure (Different from ImageComputationKernel)

ParticleBlinkScript uses the Blink API directly - the kernel declaration syntax differs from regular BlinkScript:

```cpp
// IMPORTANT: Do NOT use ImageComputationKernel here
// ParticleBlinkScript uses Blink API particle kernel format

kernel ParticleEffect : ParticleBlinkKernel<eParticleWise>
{
  param:
    float gravity;
    float turbulenceStrength;
    float3 windDir;

  void init() {
    // Runs once per simulation step
  }

  void process(int particleIndex) {
    // Access current particle state via particle.* accessors
    // Modify velocity, position, properties
  }
};
```

**Key differences from ImageComputationKernel:**
- `ParticleBlinkKernel` instead of `ImageComputationKernel`
- `eParticleWise` granularity
- `process(int particleIndex)` instead of `process(int2 pos)`
- Particle state accessed via built-in accessors (position, velocity, age, etc.)
- No `Image<>` declarations - works on particle data, not pixels

### The 14 Foundry Gadgets

NukeX 16 ships these ParticleBlinkScript starting templates (access via the node's gadget picker):

1. **Snowfall** - Basic snow with gravity and drift
2. **Rain** - Directional rain with streaks
3. **Embers** - Rising fire embers with flicker
4. **Dust** - Atmospheric dust suspension
5. **BugSwarm** - Flocking/swarm behavior
6. **Fireworks** - Burst and trail effects
7. **Galaxy** - Orbital particle distribution
8. **Vortex** - Rotating/spiraling particles
9. **Smoke Puff** - Expanding smoke volumes
10. **Confetti** - Tumbling flat particles
11. **Bubbles** - Rising spherical particles with wobble
12. **Lightning Particles** - Charged particle branching
13. **Fluid Surface** - Water surface simulation
14. **Attractor** - Particles drawn toward a point

These are starting points - modify and extend for your shot.

### Blink API (Advanced Extension)

The ParticleBlinkScript node is built on the **Blink API** - a lower-level C++ interface that Foundry uses internally. Advanced users can extend via:

```cpp
// Foundry Blink API (lower level than BlinkScript node)
// Requires: Nuke Developer Kit (NDK)
#include "Blink/Blink.h"

// The ParticleBlinkScript node itself is implemented using
// the Blink API particle extensions. The gadget templates
// are Blink API kernels exposed through the NukeX UI.
```

For custom Blink API development, see:
- Foundry NDK documentation: `learn.foundry.com/nuke/developers`
- Blink API headers: shipped with NukeX install under `include/Blink/`

---

## Comparing Kernel Declarations

```cpp
// Regular BlinkScript node - image processing
kernel MyEffect : ImageComputationKernel<ePixelWise>
{
  Image<eRead, eAccessPoint, eEdgeClamped> src;
  Image<eWrite, eAccessPoint> dst;
  // ...
  void process(int2 pos) { ... }
};

// ParticleBlinkScript node - particle simulation
kernel MyParticles : ParticleBlinkKernel<eParticleWise>
{
  // No Image<> declarations
  // ...
  void process(int particleIndex) { ... }
};
```

---

## Node Setup Patterns

### Procedural BlinkScript Setup (Any Nuke)

```python
import nuke

def create_procedural_particles(source_node=None):
    """Create a procedural particle BlinkScript node wired to a source."""
    blink = nuke.createNode("BlinkScript")
    blink["name"].setValue("ProceduralParticles")

    # Wire source if provided
    if source_node:
        blink.setInput(0, source_node)

    # Set the kernel (paste kernel code here)
    # blink["kernelSourceCode"].setValue(KERNEL_CODE)

    # Wire time expression
    blink["time"].setExpression("frame / fps")

    # Set defaults
    blink["count"].setValue(200)
    blink["size"].setValue(4.0)
    blink["speed"].setValue(0.15)

    return blink
```

### ParticleBlinkScript Setup (NukeX 16+)

```python
import nuke

def create_particle_blinkscript():
    """Create a ParticleBlinkScript node with a Foundry gadget loaded."""
    # Create the node
    pbs = nuke.createNode("ParticleBlinkScript")
    pbs["name"].setValue("CustomParticles")

    # Load a gadget as starting point (gadget name from the 14 Foundry templates)
    # Access via the node's gadget UI dropdown, not scriptable directly
    # Instead: open node, click "Load Gadget", select template, then modify

    return pbs
```

---

## Performance Considerations

### Procedural BlinkScript
- **Particle count:** Keep under 500 for real-time. 1000+ is slow per frame.
- **Per-particle loop:** Runs for every pixel x every particle. O(pixels x count) complexity.
- **Optimization:** Use `init()` for all expensive math (sin constants, image dimensions).
- **GPU:** Runs fully on GPU - much faster than Nuke particle system for simple shapes.

### ParticleBlinkScript
- **Sim caching:** Unlike procedural approach, simulation results are cached.
- **Complex interactions:** Inter-particle forces are possible but expensive.
- **NukeX only:** Will not load in Nuke non-commercial or standard Nuke.

---

## When to Use Which

| Need | Use |
|------|-----|
| Snow, rain, embers, dust overlay | Procedural BlinkScript |
| Art-directable, keyframable particles | Procedural BlinkScript |
| Standard Nuke license | Procedural BlinkScript |
| Real gravity, collisions, flocking | ParticleBlinkScript (NukeX 16+) |
| Starting from Foundry gadgets | ParticleBlinkScript (NukeX 16+) |
| Atmospheric VFX that composites cleanly | Procedural BlinkScript |
| Physics simulation for hero elements | ParticleBlinkScript (NukeX 16+) |

---

## Related Skills

- **nuke-blinkscript** - Image processing kernels (ImageComputationKernel), composition overlays, GPU pixel effects. The foundation for understanding Blink syntax before tackling particles.
- **nuke-compositing** - Integrating particle effects into comp trees.

---

## Version History

**1.0.0 (2026-03-11):**
- Initial release
- Covers both procedural BlinkScript and ParticleBlinkScript node approaches
- Documented all 14 Foundry gadgets (NukeX 16+)
- Included snowfall, embers, and swarm variants for procedural approach
- Blink API relationship documented for advanced users
