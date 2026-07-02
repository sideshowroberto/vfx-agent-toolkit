# MCP Tools Reference - Unreal Blueprint Automation

Complete reference for all MCP tools used in Blueprint automation workflows.

## create_blueprint
```python
{
    "name": str,          # Blueprint asset name
    "parent_class": str   # Parent class (Actor, Pawn, Character, etc.)
}
```

## add_component_to_blueprint
```python
{
    "blueprint_name": str,       # Target Blueprint name
    "component_type": str,       # Component class (StaticMeshComponent, etc.)
    "component_name": str,       # Unique component name
    "location": [x, y, z],       # Optional relative location
    "rotation": [p, y, r],       # Optional relative rotation
    "scale": [x, y, z],          # Optional relative scale
    "component_properties": {}   # Optional additional properties
}
```

## set_static_mesh_properties
```python
{
    "blueprint_name": str,    # Target Blueprint name
    "component_name": str,    # StaticMeshComponent name
    "static_mesh": str        # Asset path (e.g., "/Engine/BasicShapes/Cube.Cube")
}
```

## set_component_property
```python
{
    "blueprint_name": str,    # Target Blueprint name
    "component_name": str,    # Component name
    "property_name": str,     # Property to set (Intensity, RelativeLocation, etc.)
    "property_value": str     # Value as string (auto-converted by Unreal)
}
```

## compile_blueprint
```python
{
    "blueprint_name": str     # Blueprint to compile
}
```

## spawn_blueprint_actor
```python
{
    "blueprint_name": str,    # Blueprint to spawn
    "actor_name": str,        # Instance name
    "location": [x, y, z],    # World location
    "rotation": [p, y, r]     # World rotation
}
```

## Common Component Types

```python
# Mesh Components
"StaticMeshComponent"
"SkeletalMeshComponent"

# Light Components
"PointLightComponent"
"SpotLightComponent"
"DirectionalLightComponent"

# Audio Components
"AudioComponent"

# VFX Components
"ParticleSystemComponent"
"NiagaraComponent"

# Collision Components
"BoxComponent"
"SphereComponent"
"CapsuleComponent"

# Utility Components
"SceneComponent"         # Dummy parent for hierarchy
"CameraComponent"
"SpringArmComponent"
```
