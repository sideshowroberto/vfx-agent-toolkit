"""
Media Tools for Unreal MCP
Provides automation for media and image sequence workflows
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP, Context

# Get logger
logger = logging.getLogger("UnrealMCP")


def _find_editor_utilities() -> Optional[str]:
    """
    Locate the editor_utilities directory (ForegroundPlateSetup et al.).

    Resolution order:
      1. UNREAL_MCP_EDITOR_UTILS environment variable (explicit override)
      2. <bridge root>/editor_utilities (relative to this file:
         tools/media_tools.py -> bridge/editor_utilities)

    Returns the absolute path as a string, or None if neither location exists.
    """
    env_path = os.environ.get("UNREAL_MCP_EDITOR_UTILS")
    if env_path:
        candidate = Path(env_path)
        if candidate.is_dir():
            return str(candidate.resolve())
        logger.warning(
            "UNREAL_MCP_EDITOR_UTILS is set but does not exist: %s", env_path
        )

    default = Path(__file__).resolve().parent.parent / "editor_utilities"
    if default.is_dir():
        return str(default)

    return None


def register_media_tools(mcp: FastMCP):
    """Register media tools with the MCP server."""

    @mcp.tool()
    def create_foreground_plate(
        ctx: Context,
        sequence_path: str,
        plate_name: str,
        camera_name: Optional[str] = None,
        proxy_path: Optional[str] = None,
        opacity_multiplier: float = 1.0,
        emissive_multiplier: float = 1.0,
        enable_loop: bool = True,
        add_to_sequencer: bool = False
    ) -> Dict[str, Any]:
        """
        Create complete foreground plate setup for VFX workflows.

        Creates ImgMediaSource, MediaPlayer, MediaTexture, VFX-optimized Material
        (with alpha channel + artist controls), ImagePlate attached to camera,
        and optional Sequencer MediaTrack.

        **VFX Workflow:**
        - Material: Unlit, Masked blend (hard alpha cutout), Two-Sided
        - Parameters: OpacityMultiplier (ghosting), EmissiveMultiplier (brightness)
        - Use Case: Set extensions with live action plates, preview in Unreal, final comp in Nuke

        Args:
            sequence_path: Path to first image in sequence (e.g., "D:/Plates/Shot001_0001.exr")
            plate_name: Base name for assets (e.g., "Shot001_FG")
            camera_name: Target CineCameraActor name (creates new if None)
            proxy_path: Optional lowres proxy folder name (e.g., "lowres")
            opacity_multiplier: Default opacity (0.0-1.0, for ghosting plate to see CG)
            emissive_multiplier: Default brightness (0.0-5.0, for adjusting plate brightness)
            enable_loop: Loop playback in MediaPlayer
            add_to_sequencer: Auto-create MediaTrack in active LevelSequence

        Returns:
            {
                "success": true,
                "assets_created": {
                    "media_source": "MS_Shot001_FG",
                    "media_player": "MP_Shot001_FG",
                    "media_texture": "MT_Shot001_FG",
                    "material": "M_Shot001_FG",
                    "camera": "Cam_Shot001_FG",
                    "image_plate": "IP_Shot001_FG"
                },
                "errors": []
            }

        Example:
            # Basic usage
            create_foreground_plate(
                sequence_path="D:/VFX/Plates/Shot001/Shot001_0001.exr",
                plate_name="Shot001_FG"
            )

            # With ghosting for alignment
            create_foreground_plate(
                sequence_path="D:/VFX/Plates/Shot001/Shot001_0001.exr",
                plate_name="Shot001_FG",
                opacity_multiplier=0.5,  # 50% transparent to see CG behind
                emissive_multiplier=2.0   # Brighter for better visibility
            )

            # With proxy workflow
            create_foreground_plate(
                sequence_path="D:/VFX/Plates/Shot001/Shot001_0001.exr",
                plate_name="Shot001_FG",
                proxy_path="lowres"  # Uses D:/VFX/Plates/Shot001/lowres/ for development
            )

        Naming Convention:
            - ImgMediaSource: MS_{plate_name}
            - MediaPlayer: MP_{plate_name}
            - MediaTexture: MT_{plate_name}
            - Material: M_{plate_name}
            - ImagePlate: IP_{plate_name}
            - Camera: Cam_{plate_name} (if created)

        Requirements:
            - ImagePlate plugin must be enabled
            - Image sequence must exist at sequence_path
            - For alpha support, use EXR or PNG with alpha channel
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                logger.warning("Failed to connect to Unreal Engine")
                return {"success": False, "error": "Failed to connect to Unreal Engine"}

            # Locate editor utilities (env var override, then bridge-relative default)
            editor_utils_path = _find_editor_utilities()
            if not editor_utils_path:
                error_msg = (
                    "Could not locate the 'editor_utilities' directory "
                    "(needed for ForegroundPlateSetup). Set the "
                    "UNREAL_MCP_EDITOR_UTILS environment variable to the "
                    "directory containing ForegroundPlateSetup.py, or place "
                    "'editor_utilities' next to unreal_mcp_server.py in the "
                    "bridge directory."
                )
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            # Build Python script to execute in Unreal
            python_code = f"""
import sys
import os

# Add editor utilities to path (resolved by the MCP bridge)
editor_utils_path = r"{editor_utils_path}"
if editor_utils_path not in sys.path:
    sys.path.append(editor_utils_path)

# Import and reload
import ForegroundPlateSetup
import importlib
importlib.reload(ForegroundPlateSetup)

# Create plate
setup = ForegroundPlateSetup.ForegroundPlateSetup()
result = setup.create_foreground_plate(
    sequence_path=r"{sequence_path}",
    plate_name="{plate_name}",
    camera_name={f'"{camera_name}"' if camera_name else 'None'},
    proxy_path={f'"{proxy_path}"' if proxy_path else 'None'},
    opacity_multiplier={opacity_multiplier},
    emissive_multiplier={emissive_multiplier},
    enable_loop={str(enable_loop)},
    add_to_sequencer={str(add_to_sequencer)}
)

# Return result as JSON
import json
print(json.dumps(result))
"""

            logger.info(f"Creating foreground plate: {plate_name}")
            logger.debug(f"Python script: {python_code[:200]}...")

            # Send Python execution command to Unreal
            response = unreal.send_command("execute_python", {"script": python_code})

            logger.info(f"Received response: {response}")

            # Parse response
            if response and response.get("status") != "error":
                # Try to extract JSON from output
                output = response.get("output", "")
                if output:
                    try:
                        import json
                        result = json.loads(output)
                        logger.info(f"Plate creation result: {result}")
                        return result
                    except json.JSONDecodeError:
                        logger.warning("Could not parse JSON from output")
                        return {
                            "success": True,
                            "message": "Foreground plate creation initiated",
                            "output": output
                        }
                else:
                    return {
                        "success": True,
                        "message": "Foreground plate creation completed",
                        "response": response
                    }
            else:
                error_msg = response.get("error", "Unknown error") if response else "No response"
                logger.error(f"Failed to create foreground plate: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

        except Exception as e:
            logger.error(f"Exception creating foreground plate: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def open_media_player(
        ctx: Context,
        media_player_name: str,
        media_source_name: str = None
    ) -> Dict[str, Any]:
        """
        Open and start playing a MediaPlayer with an optional MediaSource.

        Args:
            media_player_name: Name of the MediaPlayer asset (e.g., "MP_Shot001_FG")
            media_source_name: Optional MediaSource to play (e.g., "MS_Shot001_FG")

        Returns:
            {"success": true, "message": "MediaPlayer started"}

        Example:
            open_media_player("MP_Shot001_FG", "MS_Shot001_FG")
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return {"success": False, "error": "Failed to connect to Unreal Engine"}

            python_code = f"""
import unreal

# Find MediaPlayer
media_player = unreal.EditorAssetLibrary.load_asset("/Game/Media/{media_player_name}")
if not media_player:
    print("ERROR: MediaPlayer not found: {media_player_name}")
else:
    """

            if media_source_name:
                python_code += f"""
    # Find MediaSource
    media_source = unreal.EditorAssetLibrary.load_asset("/Game/Media/{media_source_name}")
    if media_source:
        media_player.open_source(media_source)
        print("SUCCESS: Opened {media_source_name} in {media_player_name}")
    else:
        print("ERROR: MediaSource not found: {media_source_name}")
    """
            else:
                python_code += f"""
    media_player.play()
    print("SUCCESS: Started playing {media_player_name}")
    """

            response = unreal.send_command("execute_python", {"script": python_code})
            return response

        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def list_image_sequences_in_folder(
        ctx: Context,
        folder_path: str
    ) -> Dict[str, Any]:
        """
        List image sequences found in a folder (useful for batch operations).

        Args:
            folder_path: Path to folder containing image sequences (e.g., "D:/VFX/Plates")

        Returns:
            {
                "success": true,
                "sequences": [
                    {
                        "name": "Shot001",
                        "first_frame": "D:/VFX/Plates/Shot001/Shot001_0001.exr",
                        "frame_count": 120,
                        "has_proxy": true
                    },
                    ...
                ]
            }

        Example:
            list_image_sequences_in_folder("D:/VFX/Plates")
        """
        try:
            import os
            import re
            from pathlib import Path

            folder = Path(folder_path)
            if not folder.exists():
                return {"success": False, "error": f"Folder not found: {folder_path}"}

            sequences = {}

            # Pattern to match image sequences (e.g., name_0001.exr, name_001.png)
            pattern = re.compile(r'^(.+?)_(\d+)\.(exr|png|jpg|jpeg|tga|dpx)$', re.IGNORECASE)

            for file in folder.rglob('*'):
                if file.is_file() and 'lowres' not in file.parts:
                    match = pattern.match(file.name)
                    if match:
                        seq_name = match.group(1)
                        frame_num = match.group(2)
                        extension = match.group(3)

                        if seq_name not in sequences:
                            sequences[seq_name] = {
                                "name": seq_name,
                                "first_frame": None,
                                "frames": [],
                                "extension": extension,
                                "folder": str(file.parent),
                                "has_proxy": (file.parent / "lowres").exists()
                            }

                        sequences[seq_name]["frames"].append(int(frame_num))

            # Determine first frame for each sequence
            results = []
            for seq_name, seq_data in sequences.items():
                if seq_data["frames"]:
                    seq_data["frames"].sort()
                    first_frame_num = seq_data["frames"][0]
                    first_frame_padded = str(first_frame_num).zfill(len(str(seq_data["frames"][0])))
                    first_frame_file = f"{seq_name}_{first_frame_padded}.{seq_data['extension']}"
                    seq_data["first_frame"] = str(Path(seq_data["folder"]) / first_frame_file)
                    seq_data["frame_count"] = len(seq_data["frames"])

                    results.append({
                        "name": seq_name,
                        "first_frame": seq_data["first_frame"],
                        "frame_count": seq_data["frame_count"],
                        "has_proxy": seq_data["has_proxy"]
                    })

            return {
                "success": True,
                "sequences": results,
                "folder": str(folder)
            }

        except Exception as e:
            logger.error(f"Error listing sequences: {str(e)}")
            return {"success": False, "error": str(e)}
