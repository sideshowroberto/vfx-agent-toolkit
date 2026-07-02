# Media Track Python API Reference

**Complete documentation for MovieSceneMediaTrack and MovieSceneMediaSection**

**Source:** Unreal Python StubHub (Context7)
**Validated:** 2025-11-20

---

## Overview

Media tracks in Sequencer allow playback of video/image sequences synchronized with cinematic timing. Full Python API support exists contrary to previous research.

**Primary Classes:**
- `unreal.MovieSceneMediaTrack` - Track container
- `unreal.MovieSceneMediaSection` - Section with media configuration
- `unreal.MovieSceneMediaPlayerPropertySection` - Alternative for MediaPlayer control

---

## MovieSceneMediaSection

### Class Definition

```python
class MovieSceneMediaSection(MovieSceneSection)
```

Inherits all MovieSceneSection functionality (ranges, easing, conditions).

---

## Properties (All Read-Write)

### 1. media_source

**Type:** `MediaSource`
**Purpose:** Primary MediaSource asset for playback (used if no proxy specified)

```python
@property
def media_source() -> MediaSource

@media_source.setter
def media_source(value: MediaSource) -> None
```

**Usage:**
```python
# Set media source
section.media_source = unreal.load_asset('/Game/Media/MyVideo')

# Get current source
current_source = section.media_source
```

**Media Source Types:**
- `FileMediaSource` - Single video file (MP4, MOV, AVI)
- `ImgMediaSource` - Image sequence (EXR, PNG, JPG)
- `StreamMediaSource` - Network stream (RTSP, HLS)

---

### 2. start_frame_offset

**Type:** `FrameNumber`
**Purpose:** Offset (in frames) into the source media where playback begins

```python
@property
def start_frame_offset() -> FrameNumber

@start_frame_offset.setter
def start_frame_offset(value: FrameNumber) -> None
```

**Usage:**
```python
# Skip first 30 frames of media
section.start_frame_offset = unreal.FrameNumber(30)

# Start at timecode 00:00:02:00 (at 24fps = frame 48)
section.start_frame_offset = unreal.FrameNumber(48)

# Get current offset
offset = section.start_frame_offset
print(f"Starting at frame: {offset.value}")
```

**Common Use Cases:**
- Trim unwanted intro frames
- Align media with specific timecode
- Loop from mid-point in source
- Match edit decision list (EDL) timing

---

### 3. media_source_proxy_index

**Type:** `int`
**Purpose:** Index for MediaSourceProxy to determine which MediaSource to use

```python
@property
def media_source_proxy_index() -> int

@media_source_proxy_index.setter
def media_source_proxy_index(value: int) -> None
```

**Usage:**
```python
# Select proxy variant (e.g., quality levels)
section.media_source_proxy_index = 0  # High quality
section.media_source_proxy_index = 1  # Medium quality
section.media_source_proxy_index = 2  # Low quality (proxy)

# Get active proxy index
index = section.media_source_proxy_index
```

**Proxy Workflow:**
MediaSourceProxy allows multiple MediaSource variants (quality levels, formats) selected by index.

**Use Cases:**
- Development proxy (lowres) vs final render (highres)
- Platform-specific codecs (H.264 vs ProRes)
- Network bandwidth adaptation

---

### 4. cache_settings

**Type:** `MediaSourceCacheSettings`
**Purpose:** Override default caching behavior for this section

```python
@property
def cache_settings() -> MediaSourceCacheSettings

@cache_settings.setter
def cache_settings(value: MediaSourceCacheSettings) -> None
```

**Usage:**
```python
# Configure cache settings
cache = unreal.MediaSourceCacheSettings()
cache.override_cache_time = True
cache.cache_time_ahead = 5.0  # Seconds
cache.cache_time_behind = 2.0

section.cache_settings = cache
```

**Note:** Settings ignored if player proxy used.

**Cache Settings Control:**
- Ahead/behind buffer sizes
- Memory vs disk caching
- Pre-roll behavior
- Seek performance tuning

---

## MovieSceneMediaTrack

### Class Definition

```python
class MovieSceneMediaTrack(MovieSceneNameableTrack)
```

Inherits track naming and organization from MovieSceneNameableTrack.

### Creating Media Tracks

**Pattern:** Generic `add_track()` (same as camera cuts)

```python
# Add media track to sequence
media_track = unreal.MovieSceneSequenceExtensions.add_track(
    sequence,
    unreal.MovieSceneMediaTrack
)

# Add section
section = unreal.MovieSceneTrackExtensions.add_section(media_track)

# Cast to correct type
media_section = section.cast(unreal.MovieSceneMediaSection)
```

**IMPORTANT:** No specialized `add_media_track()` method exists - use generic pattern.

---

## Complete Workflows

### Basic Media Playback

```python
def add_media_to_sequence(sequence, media_source_path):
    """
    Adds media playback track to sequence.

    Args:
        sequence: LevelSequence
        media_source_path: str - Asset path to MediaSource

    Returns:
        MovieSceneMediaSection
    """
    # Load media source
    media_source = unreal.load_asset(media_source_path)

    # Add track
    media_track = unreal.MovieSceneSequenceExtensions.add_track(
        sequence,
        unreal.MovieSceneMediaTrack
    )

    # Add section
    section = unreal.MovieSceneTrackExtensions.add_section(media_track)
    media_section = section.cast(unreal.MovieSceneMediaSection)

    # Configure
    media_section.media_source = media_source
    media_section.set_range(
        unreal.FrameNumber(0),
        unreal.FrameNumber(240)
    )

    return media_section
```

### Media with Start Offset

```python
def add_trimmed_media(sequence, media_source_path, trim_start_frames):
    """
    Adds media with trimmed beginning.

    Args:
        sequence: LevelSequence
        media_source_path: str
        trim_start_frames: int - Frames to skip at start
    """
    media_track = unreal.MovieSceneSequenceExtensions.add_track(
        sequence,
        unreal.MovieSceneMediaTrack
    )

    section = unreal.MovieSceneTrackExtensions.add_section(media_track)
    media_section = section.cast(unreal.MovieSceneMediaSection)

    # Load and configure
    media_section.media_source = unreal.load_asset(media_source_path)
    media_section.start_frame_offset = unreal.FrameNumber(trim_start_frames)

    # Set playback range (accounts for trim)
    media_section.set_range(
        unreal.FrameNumber(0),
        unreal.FrameNumber(240)
    )

    return media_section
```

### Multi-Track Media Composition

```python
def create_multi_layer_media(sequence, layers):
    """
    Creates multiple media tracks (e.g., background + overlay).

    Args:
        sequence: LevelSequence
        layers: List of (media_path, start_frame, end_frame) tuples

    Returns:
        List of MovieSceneMediaSection
    """
    sections = []

    for media_path, start, end in layers:
        # Create track
        track = unreal.MovieSceneSequenceExtensions.add_track(
            sequence,
            unreal.MovieSceneMediaTrack
        )
        track.set_display_name(f"Media_{len(sections)+1}")

        # Add section
        section = unreal.MovieSceneTrackExtensions.add_section(track)
        media_section = section.cast(unreal.MovieSceneMediaSection)

        # Configure
        media_section.media_source = unreal.load_asset(media_path)
        media_section.set_range(
            unreal.FrameNumber(start),
            unreal.FrameNumber(end)
        )

        sections.append(media_section)

    return sections

# Example usage
layers = [
    ('/Game/Media/Background', 0, 300),   # Full sequence
    ('/Game/Media/Overlay', 100, 200)     # Middle section only
]
create_multi_layer_media(sequence, layers)
```

### Proxy Workflow (Development vs Final)

```python
def setup_proxy_media(sequence, highres_source, lowres_source):
    """
    Setup media with quality switching capability.

    Args:
        sequence: LevelSequence
        highres_source: str - Full quality media path
        lowres_source: str - Proxy media path
    """
    # Create MediaSourceProxy
    proxy = unreal.MediaSourceProxy()
    # Note: MediaSourceProxy configuration depends on UE version
    # This is conceptual - actual API may vary

    # Add track
    media_track = unreal.MovieSceneSequenceExtensions.add_track(
        sequence,
        unreal.MovieSceneMediaTrack
    )

    section = unreal.MovieSceneTrackExtensions.add_section(media_track)
    media_section = section.cast(unreal.MovieSceneMediaSection)

    # Configure primary source
    media_section.media_source = unreal.load_asset(highres_source)

    # Switch to proxy during development
    media_section.media_source_proxy_index = 1  # Lowres

    # Switch back for final render
    # media_section.media_source_proxy_index = 0  # Highres

    media_section.set_range(unreal.FrameNumber(0), unreal.FrameNumber(240))

    return media_section
```

---

## MovieSceneMediaPlayerPropertySection (Alternative)

For controlling MediaPlayer component properties instead of direct media playback.

### Class Definition

```python
class MovieSceneMediaPlayerPropertySection(MovieSceneSection)
```

### Additional Properties

```python
@property
def media_source() -> MediaSource

@media_source.setter
def media_source(value: MediaSource) -> None

@property
def loop() -> bool

@loop.setter
def loop(value: bool) -> None
```

### Usage

```python
# Add MediaPlayer property track
player_track = unreal.MovieSceneSequenceExtensions.add_track(
    sequence,
    unreal.MovieSceneMediaPlayerPropertyTrack
)

section = unreal.MovieSceneTrackExtensions.add_section(player_track)
player_section = section.cast(unreal.MovieSceneMediaPlayerPropertySection)

# Configure
player_section.media_source = unreal.load_asset('/Game/Media/Video')
player_section.loop = True  # Enable looping
player_section.set_range(unreal.FrameNumber(0), unreal.FrameNumber(300))
```

**Use Case:** Control MediaPlayer actors in level (screens, TVs, monitors) via Sequencer.

---

## Media Source Types Reference

### FileMediaSource
**Use:** Single video files (MP4, MOV, AVI, WMV)
```python
file_source = unreal.load_asset('/Game/Media/MyVideo')
# Or create new
factory = unreal.FileMediaSourceFactory()
file_source = asset_tools.create_asset(
    asset_name="Video_Source",
    package_path="/Game/Media",
    asset_class=unreal.FileMediaSource,
    factory=factory
)
file_source.set_editor_property("file_path", "D:/Videos/clip.mp4")
```

### ImgMediaSource
**Use:** Image sequences (EXR, PNG, JPG, TGA)
```python
img_source = asset_tools.create_asset(
    asset_name="Sequence_Source",
    package_path="/Game/Media",
    asset_class=unreal.ImgMediaSource,
    factory=unreal.ImgMediaSourceFactory()
)
img_source.set_editor_property("sequence_path", "D:/Renders/Shot001_####.exr")
```

### StreamMediaSource
**Use:** Network streams (RTSP, HLS, HTTP)
```python
stream_source = asset_tools.create_asset(
    asset_name="Stream_Source",
    package_path="/Game/Media",
    asset_class=unreal.StreamMediaSource,
    factory=unreal.StreamMediaSourceFactory()
)
stream_source.set_editor_property("stream_url", "rtsp://server/stream")
```

---

## Integration with Other Systems

### Media + Camera Cuts

```python
def create_video_with_cuts(sequence, video_path, camera_bindings_with_timing):
    """
    Combines media playback with camera cuts.

    Args:
        sequence: LevelSequence
        video_path: str - Background video
        camera_bindings_with_timing: List of (binding, start, end)
    """
    # Add background media
    media_track = unreal.MovieSceneSequenceExtensions.add_track(
        sequence,
        unreal.MovieSceneMediaTrack
    )
    media_section = unreal.MovieSceneTrackExtensions.add_section(media_track)
    media_section = media_section.cast(unreal.MovieSceneMediaSection)
    media_section.media_source = unreal.load_asset(video_path)
    media_section.set_range(unreal.FrameNumber(0), unreal.FrameNumber(300))

    # Add camera cuts
    camera_cut_track = unreal.MovieSceneSequenceExtensions.add_track(
        sequence,
        unreal.MovieSceneCameraCutTrack
    )

    for camera_binding, start, end in camera_bindings_with_timing:
        section = unreal.MovieSceneTrackExtensions.add_section(camera_cut_track)
        cut_section = section.cast(unreal.MovieSceneCameraCutSection)

        camera_id = unreal.MovieSceneSequenceExtensions.get_binding_id(
            sequence, camera_binding
        )
        cut_section.set_camera_binding_id(camera_id)
        cut_section.set_range(start, end)
```

### Media + ImagePlate (Compositing)

```python
def create_composite_shot(sequence, bg_video_path, fg_plate_path):
    """
    Background video + foreground ImagePlate composite.

    Args:
        sequence: LevelSequence
        bg_video_path: str - Background media
        fg_plate_path: str - Foreground image sequence
    """
    # Background video track
    bg_track = unreal.MovieSceneSequenceExtensions.add_track(
        sequence,
        unreal.MovieSceneMediaTrack
    )
    bg_section = unreal.MovieSceneTrackExtensions.add_section(bg_track)
    bg_section = bg_section.cast(unreal.MovieSceneMediaSection)
    bg_section.media_source = unreal.load_asset(bg_video_path)
    bg_section.set_range(unreal.FrameNumber(0), unreal.FrameNumber(240))

    # Foreground ImagePlate on camera (see ImagePlate section in main SKILL.md)
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CineCameraActor,
        unreal.Vector(0, 0, 200)
    )

    # Setup ImagePlate with foreground
    # ... (see SKILL.md for complete ImagePlate workflow)

    # Add camera to sequence
    binding = unreal.MovieSceneSequenceExtensions.add_possessable(sequence, camera)
```

---

## Troubleshooting

### Media Not Playing in Sequencer

**Check:**
1. MediaSource asset configured correctly (file path, sequence path)
2. Media section range set properly
3. MediaPlayer/MediaTexture linked (if using)
4. File format supported by platform
5. start_frame_offset not exceeding media duration

### Timing Mismatch

**Cause:** Frame rate mismatch between media and sequence

**Solution:**
```python
# Check media frame rate
# Match sequence display rate to media
sequence.set_display_rate(unreal.FrameRate(24, 1))  # 24 fps

# Or adjust start_frame_offset for rate conversion
```

### Cache/Stutter Issues

**Solution:**
```python
# Increase cache settings
cache = unreal.MediaSourceCacheSettings()
cache.override_cache_time = True
cache.cache_time_ahead = 10.0  # More pre-roll
section.cache_settings = cache
```

### Proxy Not Switching

**Cause:** MediaSourceProxy not configured or index out of range

**Check:**
```python
# Verify proxy index valid
index = section.media_source_proxy_index
print(f"Current proxy index: {index}")

# Reset to primary source
section.media_source_proxy_index = 0
```

---

## Performance Considerations

**Media Playback:**
- Image sequences (ImgMediaSource) more reliable than video files
- EXR sequences support alpha/deep data for compositing
- Pre-cache media before scrubbing for smooth playback

**Memory:**
- Large image sequences can consume significant RAM
- Use proxy workflow during development
- Configure cache settings based on available memory

**Formats:**
- **Best:** EXR sequences (production standard)
- **Good:** PNG sequences (alpha support)
- **Acceptable:** MP4/MOV (compressed, may have GOP issues)
- **Avoid:** Highly compressed formats (artifacting)

---

## Related APIs

**See also:**
- `unreal.MediaPlayer` - Playback control
- `unreal.MediaTexture` - Rendering target
- `unreal.MediaSoundComponent` - Audio playback
- `unreal.ImgMediaSource` - Image sequence configuration
- `unreal.MediaSourceCacheSettings` - Caching control

**Documentation:**
- Main skill: `.claude/skills/unreal-sequencer-automation/SKILL.md`
- ImagePlate API: Same skill, ImagePlate section
- Camera cuts: Same skill, Camera Cuts section

---

## Version History

**v1.0** (2025-11-20)
- Initial comprehensive documentation
- Validated all properties via Unreal Python StubHub
- Complete workflow examples
- Integration patterns with camera cuts and ImagePlate

---

**End of Media Track API Reference**
