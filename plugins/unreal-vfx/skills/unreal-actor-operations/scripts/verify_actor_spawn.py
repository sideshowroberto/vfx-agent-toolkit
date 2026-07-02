#!/usr/bin/env python3
"""
Verify Actor Spawn - Test Script

Purpose: Validates that execute_python MCP tool can spawn actors in Unreal Engine.
Usage: Run via execute_python MCP tool to verify actor operations work.
Returns: 0 on success, 1 on failure

Constitutional Compliance:
- Article I: General purpose (tests ANY project)
- Article IV: Tests independently before agent integration
- Article V: Follows official EditorLevelLibrary patterns
"""

import sys

def verify_actor_spawn():
    """
    Verify actor spawn capabilities via EditorLevelLibrary.

    Returns:
        0 if all tests pass
        1 if any test fails
    """
    try:
        import unreal
    except ImportError:
        print("ERROR: unreal module not available (must run in Unreal Python context)")
        return 1

    print("=== Actor Spawn Verification ===")
    print()

    # Test 1: Verify EditorLevelLibrary is available
    print("Test 1: EditorLevelLibrary availability")
    try:
        editor_lib = unreal.EditorLevelLibrary
        print("  ✅ EditorLevelLibrary available")
    except AttributeError as e:
        print(f"  ❌ EditorLevelLibrary not available: {e}")
        return 1

    # Test 2: Get editor world
    print()
    print("Test 2: Get editor world")
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        if world is None:
            print("  ❌ Editor world is None")
            return 1
        print(f"  ✅ Editor world: {world.get_name()}")
    except Exception as e:
        print(f"  ❌ Failed to get editor world: {e}")
        return 1

    # Test 3: Spawn test actor
    print()
    print("Test 3: Spawn StaticMeshActor")
    try:
        test_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(0, 0, 1000),  # High Z to avoid collision
            unreal.Rotator(0, 0, 0)
        )

        if test_actor is None:
            print("  ❌ spawn_actor_from_class returned None")
            return 1

        if not test_actor.is_valid():
            print("  ❌ Spawned actor is invalid")
            return 1

        print(f"  ✅ Actor spawned: {test_actor.get_name()}")

    except Exception as e:
        print(f"  ❌ Failed to spawn actor: {e}")
        return 1

    # Test 4: Set actor label
    print()
    print("Test 4: Set actor label")
    try:
        test_label = "VerificationTest_Actor"
        test_actor.set_editor_property('actor_label', test_label)

        actual_label = test_actor.get_editor_property('actor_label')
        if actual_label != test_label:
            print(f"  ❌ Label mismatch: expected '{test_label}', got '{actual_label}'")
            return 1

        print(f"  ✅ Label set: {actual_label}")

    except Exception as e:
        print(f"  ❌ Failed to set label: {e}")
        return 1

    # Test 5: Set transform
    print()
    print("Test 5: Set actor transform")
    try:
        test_location = unreal.Vector(100, 200, 1000)
        success = unreal.EditorLevelLibrary.set_actor_location(
            test_actor,
            test_location,
            False
        )

        if not success:
            print("  ❌ set_actor_location returned False")
            return 1

        actual_location = test_actor.get_actor_location()
        if (abs(actual_location.x - test_location.x) > 1.0 or
            abs(actual_location.y - test_location.y) > 1.0 or
            abs(actual_location.z - test_location.z) > 1.0):
            print(f"  ❌ Location mismatch: expected {test_location}, got {actual_location}")
            return 1

        print(f"  ✅ Transform set: {actual_location}")

    except Exception as e:
        print(f"  ❌ Failed to set transform: {e}")
        return 1

    # Test 6: Query actor
    print()
    print("Test 6: Query actors in level")
    try:
        all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

        if test_actor not in all_actors:
            print("  ❌ Test actor not found in level actors")
            return 1

        print(f"  ✅ Query successful: {len(all_actors)} actors in level")

    except Exception as e:
        print(f"  ❌ Failed to query actors: {e}")
        return 1

    # Test 7: Cleanup - delete test actor
    print()
    print("Test 7: Delete test actor (cleanup)")
    try:
        unreal.EditorLevelLibrary.destroy_actor(test_actor)

        # Verify deletion
        if test_actor.is_valid():
            print("  ❌ Actor still valid after destroy")
            return 1

        print("  ✅ Test actor deleted")

    except Exception as e:
        print(f"  ❌ Failed to delete actor: {e}")
        return 1

    # All tests passed
    print()
    print("=== ALL TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    exit_code = verify_actor_spawn()
    sys.exit(exit_code)
