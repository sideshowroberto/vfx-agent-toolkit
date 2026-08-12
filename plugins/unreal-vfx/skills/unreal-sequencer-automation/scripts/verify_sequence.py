# Sequence Verification Script
# Execute via Unreal MCP execute_python
#
# Purpose: Test script that creates, verifies, and cleans up test sequence
# Returns: 0 on success, 1 on failure
# Version: 1.0.0
# Date: 2025-11-17

import unreal
import sys

def create_test_sequence() -> bool:
    """
    Create a simple test sequence

    Returns:
        True on success, False on failure
    """
    print("Creating test sequence...")

    try:
        factory = unreal.LevelSequenceFactoryNew()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

        sequence = asset_tools.create_asset(
            asset_name="LS_SequencerTest",
            package_path="/Game/Temp",
            asset_class=unreal.LevelSequence,
            factory=factory
        )

        if sequence:
            print(f"  [OK] Created: {sequence.get_name()}")
            return True
        else:
            print(f"  [FAIL] Failed to create sequence")
            return False

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def verify_test_sequence() -> bool:
    """
    Verify test sequence exists

    Returns:
        True if exists, False otherwise
    """
    print("Verifying test sequence...")

    try:
        sequence = unreal.load_asset("/Game/Temp/LS_SequencerTest")

        if sequence:
            print(f"  [OK] Sequence exists: {sequence.get_name()}")
            return True
        else:
            print(f"  [FAIL] Sequence not found")
            return False

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def cleanup_test_sequence() -> bool:
    """
    Delete test sequence

    Returns:
        True on success, False on failure
    """
    print("Cleaning up test sequence...")

    try:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        deleted = unreal.EditorAssetLibrary.delete_asset("/Game/Temp/LS_SequencerTest")

        if deleted:
            print(f"  [OK] Deleted test sequence")
            return True
        else:
            print(f"  [WARN] Could not delete (may not exist)")
            return True  # Not a failure

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def run_verification() -> int:
    """
    Run complete verification workflow

    Returns:
        0 on success, 1 on failure
    """
    print("=" * 60)
    print("Sequencer API Verification Test")
    print("=" * 60)

    # Step 1: Create test sequence
    if not create_test_sequence():
        print("\n[FAIL] FAILED: Could not create sequence")
        return 1

    # Step 2: Verify it exists
    if not verify_test_sequence():
        print("\n[FAIL] FAILED: Sequence not found after creation")
        cleanup_test_sequence()
        return 1

    # Step 3: Clean up
    if not cleanup_test_sequence():
        print("\n[FAIL] FAILED: Could not clean up")
        return 1

    print("\n" + "=" * 60)
    print("[OK] ALL TESTS PASSED")
    print("=" * 60)

    return 0


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    exit_code = run_verification()
    sys.exit(exit_code)
