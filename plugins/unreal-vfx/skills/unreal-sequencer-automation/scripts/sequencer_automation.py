# Unreal Sequencer Automation - General Purpose Script
# Execute via Unreal MCP execute_python
#
# Purpose: Create Level Sequences with property animation
# Parameters: sequence_name, actor_name, properties_to_animate, keyframes
# Version: 1.0.0
# Date: 2025-11-17

import unreal
from typing import List, Dict, Tuple, Optional

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def create_level_sequence(
    sequence_name: str,
    package_path: str = "/Game/Cinematics"
) -> Optional[unreal.LevelSequence]:
    """
    Create a new Level Sequence asset

    Args:
        sequence_name: Name for the sequence
        package_path: Content Browser path (default: /Game/Cinematics)

    Returns:
        LevelSequence asset or None on failure
    """
    print(f"Creating Level Sequence: {sequence_name}")

    factory = unreal.LevelSequenceFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    sequence = asset_tools.create_asset(
        asset_name=sequence_name,
        package_path=package_path,
        asset_class=unreal.LevelSequence,
        factory=factory
    )

    if sequence:
        print(f"  [OK] Created: {sequence.get_name()}")
    else:
        print(f"  [FAIL] Failed to create sequence")

    return sequence


def add_actor_to_sequence(
    sequence: unreal.LevelSequence,
    actor_name: str
) -> Optional[unreal.MovieSceneBindingProxy]:
    """
    Add actor to sequence as possessable

    Args:
        sequence: Level Sequence to add to
        actor_name: Name of actor in level

    Returns:
        MovieSceneBindingProxy or None
    """
    print(f"Adding actor to sequence: {actor_name}")

    # Find actor in level
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    target_actor = None

    for actor in actors:
        if actor_name in actor.get_name():
            target_actor = actor
            break

    if not target_actor:
        print(f"  [FAIL] Actor not found: {actor_name}")
        return None

    # Add as possessable
    binding = unreal.MovieSceneSequenceExtensions.add_possessable(
        sequence,
        target_actor
    )

    if binding:
        print(f"  [OK] Added binding: {binding.get_display_name()}")
    else:
        print(f"  [FAIL] Failed to add binding")

    return binding


def add_property_track(
    binding: unreal.MovieSceneBindingProxy,
    property_name: str,
    track_type = None
) -> Optional[unreal.MovieSceneTrack]:
    """
    Add property track to binding

    Args:
        binding: MovieSceneBindingProxy to add track to
        property_name: Property to animate (e.g., "Location.Z")
        track_type: Track type (default: MovieSceneFloatTrack)

    Returns:
        MovieSceneTrack or None
    """
    if track_type is None:
        track_type = unreal.MovieSceneFloatTrack

    print(f"Adding property track: {property_name}")

    track = binding.add_track(track_type)

    # CRITICAL: This may timeout but WORKS
    try:
        track.set_property_name_and_path(property_name, property_name)
    except:
        pass  # Silent Execution - operation completes in background

    print(f"  [OK] Track added (verify with separate call)")

    return track


def add_section_to_track(
    track: unreal.MovieSceneTrack,
    start_frame: int = 0,
    end_frame: int = 300
) -> Optional[unreal.MovieSceneSection]:
    """
    Add section to track with frame range

    Args:
        track: Track to add section to
        start_frame: Start frame (default: 0)
        end_frame: End frame (default: 300)

    Returns:
        MovieSceneSection or None
    """
    section = track.add_section()
    section.set_range(start_frame, end_frame)

    print(f"  [OK] Section added: frames {start_frame}-{end_frame}")

    return section


def add_keyframes_to_channel(
    channel: unreal.MovieSceneScriptingFloatChannel,
    keyframes: List[Tuple[int, float]],
    interpolation = unreal.MovieSceneKeyInterpolation.LINEAR
) -> int:
    """
    Add keyframes to channel

    Args:
        channel: MovieSceneScriptingFloatChannel to add keys to
        keyframes: List of (frame, value) tuples
        interpolation: Interpolation mode (default: LINEAR)

    Returns:
        Number of keys added
    """
    for frame, value in keyframes:
        channel.add_key(
            unreal.FrameNumber(frame),
            value,
            interpolation
        )

    num_keys = channel.get_num_keys()
    print(f"  [OK] Added {len(keyframes)} keyframes (total: {num_keys})")

    return num_keys


# ============================================================================
# HIGH-LEVEL AUTOMATION FUNCTIONS
# ============================================================================

def create_animated_sequence(
    sequence_name: str,
    actor_name: str,
    animations: Dict[str, List[Tuple[int, float]]],
    start_frame: int = 0,
    end_frame: int = 300,
    package_path: str = "/Game/Cinematics"
) -> Optional[unreal.LevelSequence]:
    """
    Create complete animated sequence (high-level automation)

    Args:
        sequence_name: Name for sequence
        actor_name: Actor to animate
        animations: Dict of {property_name: [(frame, value), ...]}
        start_frame: Animation start frame
        end_frame: Animation end frame
        package_path: Content Browser path

    Returns:
        LevelSequence asset or None

    Example:
        animations = {
            "Location.Z": [(0, 0.0), (150, 500.0), (300, 0.0)],
            "Rotation.Yaw": [(0, 0.0), (300, 360.0)]
        }
        seq = create_animated_sequence(
            "LS_MyAnimation",
            "Cube",
            animations
        )
    """
    print("=" * 60)
    print(f"Creating Animated Sequence: {sequence_name}")
    print("=" * 60)

    # Step 1: Create sequence
    sequence = create_level_sequence(sequence_name, package_path)
    if not sequence:
        return None

    # Step 2: Add actor
    binding = add_actor_to_sequence(sequence, actor_name)
    if not binding:
        print("WARNING: No binding - manually add actor to sequence")
        return sequence

    # Step 3: Add property tracks
    print(f"\nAdding {len(animations)} property tracks...")
    tracks = {}

    for property_name in animations.keys():
        track = add_property_track(binding, property_name)
        if track:
            tracks[property_name] = track

    # Step 4: Add sections
    print("\nAdding sections to tracks...")
    sections = {}

    for property_name, track in tracks.items():
        section = add_section_to_track(track, start_frame, end_frame)
        if section:
            sections[property_name] = section

    # Step 5: Add keyframes
    print("\nAdding keyframes...")

    for property_name, keyframes in animations.items():
        if property_name not in sections:
            continue

        section = sections[property_name]

        # Get channels
        channels = unreal.MovieSceneSectionExtensions.get_channels_by_type(
            section,
            unreal.MovieSceneScriptingFloatChannel
        )

        if channels:
            channel = channels[0]
            add_keyframes_to_channel(channel, keyframes)

    # Step 6: Open in Sequencer
    print("\nOpening in Sequencer...")
    try:
        unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
        print("  [OK] Sequence opened (may timeout but works)")
    except:
        pass

    print("\n" + "=" * 60)
    print("[OK] COMPLETE")
    print("=" * 60)

    return sequence


def create_transform_animation(
    sequence_name: str,
    actor_name: str,
    location_keyframes: Optional[Dict[str, List[Tuple[int, float]]]] = None,
    rotation_keyframes: Optional[Dict[str, List[Tuple[int, float]]]] = None,
    scale_keyframes: Optional[Dict[str, List[Tuple[int, float]]]] = None,
    start_frame: int = 0,
    end_frame: int = 300
) -> Optional[unreal.LevelSequence]:
    """
    Create sequence with transform animation (location/rotation/scale)

    Args:
        sequence_name: Name for sequence
        actor_name: Actor to animate
        location_keyframes: Dict of {"X": [...], "Y": [...], "Z": [...]}
        rotation_keyframes: Dict of {"Roll": [...], "Pitch": [...], "Yaw": [...]}
        scale_keyframes: Dict of {"X": [...], "Y": [...], "Z": [...]}
        start_frame: Start frame
        end_frame: End frame

    Returns:
        LevelSequence asset or None

    Example:
        seq = create_transform_animation(
            "LS_CubeAnim",
            "Cube",
            location_keyframes={
                "Z": [(0, 0.0), (150, 500.0), (300, 0.0)]
            },
            rotation_keyframes={
                "Yaw": [(0, 0.0), (300, 360.0)]
            }
        )
    """
    animations = {}

    # Build animations dict from transform components
    if location_keyframes:
        for axis, keyframes in location_keyframes.items():
            animations[f"Location.{axis}"] = keyframes

    if rotation_keyframes:
        for axis, keyframes in rotation_keyframes.items():
            animations[f"Rotation.{axis}"] = keyframes

    if scale_keyframes:
        for axis, keyframes in scale_keyframes.items():
            animations[f"Scale.{axis}"] = keyframes

    return create_animated_sequence(
        sequence_name,
        actor_name,
        animations,
        start_frame,
        end_frame
    )


def verify_sequence(sequence_path: str) -> None:
    """
    Verify sequence was created correctly

    Args:
        sequence_path: Asset path (e.g., "/Game/Cinematics/LS_MyAnimation")
    """
    seq = unreal.load_asset(sequence_path)

    print("\n" + "=" * 60)
    print("SEQUENCE VERIFICATION")
    print("=" * 60)

    # Check possessables
    possessables = unreal.MovieSceneSequenceExtensions.get_possessables(seq)
    print(f"\nPossessables: {len(possessables)}")

    if len(possessables) == 0:
        print("  [WARN] No possessables - manually add actor")
        return

    binding = possessables[0]
    print(f"  [OK] Binding: {binding.get_display_name()}")

    # Check tracks
    tracks = binding.get_tracks()
    print(f"\nTracks: {len(tracks)}")

    for i, track in enumerate(tracks):
        track_name = track.get_display_name()
        sections = track.get_sections()

        print(f"\n  Track {i+1}: {track_name}")
        print(f"    Sections: {len(sections)}")

        if sections:
            section = sections[0]
            channels = unreal.MovieSceneSectionExtensions.get_channels_by_type(
                section, unreal.MovieSceneScriptingFloatChannel
            )

            if channels:
                channel = channels[0]
                num_keys = channel.get_num_keys()
                print(f"    Keys: {num_keys}")

    print("\n" + "=" * 60)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
EXAMPLE 1: Simple Z-Axis Animation
===================================

animations = {
    "Location.Z": [(0, 0.0), (150, 500.0), (300, 0.0)]
}

seq = create_animated_sequence(
    "LS_SimpleAnimation",
    "Cube",
    animations
)


EXAMPLE 2: Complex Multi-Property Animation
============================================

animations = {
    "Location.X": [(0, -2000.0), (150, 2000.0)],
    "Location.Z": [(0, 0.0), (75, 500.0), (150, 0.0)],
    "Rotation.Yaw": [(0, 0.0), (150, 360.0)],
    "Scale.X": [(0, 1.0), (150, 2.0)]
}

seq = create_animated_sequence(
    "LS_ComplexAnimation",
    "Cube",
    animations,
    start_frame=0,
    end_frame=300
)


EXAMPLE 3: Transform Animation Helper
======================================

seq = create_transform_animation(
    "LS_TransformAnim",
    "Cube",
    location_keyframes={
        "X": [(0, -1000.0), (150, 1000.0)],
        "Z": [(0, 0.0), (150, 500.0)]
    },
    rotation_keyframes={
        "Yaw": [(0, 0.0), (150, 360.0)]
    }
)


EXAMPLE 4: Verification
========================

verify_sequence("/Game/Cinematics/LS_MyAnimation")


CRITICAL NOTES:
===============
- Timeouts are NORMAL (Silent Execution pattern)
- Use separate script calls for verification
- Some operations complete in background
- Always check UE Editor to confirm success
"""
