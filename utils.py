"""
Utility functions for the Sonos Last.fm scrobbler.
"""

import sys
from typing import Dict

# Track display state
_last_line_count = 0
_display_started = False


def create_progress_bar(
    current: int, total: int, threshold: int, width: int = 50
) -> str:
    """
    Create an ASCII progress bar showing current position and scrobble threshold.

    Args:
        current: Current position in seconds
        total: Total duration in seconds
        threshold: Scrobble threshold in seconds
        width: Width of the progress bar in characters

    Returns:
        A string containing the progress bar
    """
    if total == 0:
        return "[" + " " * width + "] 0%"

    # Calculate exact percentage and positions
    percentage = (current * 100) // total if total > 0 else 0
    progress = int((current * width) / total) if total > 0 else 0
    threshold_pos = int((threshold * width) / total) if total > 0 else 0

    # Create the bar
    bar = list("." * width)

    # Add threshold marker
    if 0 <= threshold_pos < width:
        bar[threshold_pos] = "|"

    # Fill progress
    for i in range(progress):
        if i < width:
            bar[i] = "="

    # Add position marker (only if within bounds)
    if 0 <= progress < width:
        bar[progress] = ">"

    return f"[{''.join(bar)}] {percentage}%"


def update_all_progress_displays(speakers_info: Dict[str, Dict]) -> None:
    """
    Update progress display for all speakers in a coordinated way.

    Args:
        speakers_info: Dictionary mapping speaker IDs to their current track info
            Each track info should contain:
            - speaker_name: str
            - artist: str
            - title: str
            - position: int (seconds)
            - duration: int (seconds)
            - threshold: int (seconds)
            - state: str
    """
    global _last_line_count, _display_started

    # Prepare the display content
    lines = []

    # Generate display for each speaker
    for speaker_info in speakers_info.values():
        current = speaker_info["position"]
        total = speaker_info["duration"]

        # Format time as MM:SS
        current_time = f"{current // 60:02d}:{current % 60:02d}"
        total_time = f"{total // 60:02d}:{total % 60:02d}"

        # Create status lines
        status = f"{speaker_info['speaker_name']}: {speaker_info['artist']} - {speaker_info['title']} [{speaker_info['state']}]"
        progress = create_progress_bar(current, total, speaker_info["threshold"])
        percentage = (current * 100) // total if total > 0 else 0
        time_display = f"Time: {current_time}/{total_time} ({percentage}%)"

        # Add this speaker's display (with single newline after)
        lines.extend([status, progress, time_display, ""])

    # Count total lines we'll display:
    # 1 newline + 1 header + 1 newline + content lines + 1 final newline
    total_lines = 4 + len(lines)

    # Initial display setup
    if not _display_started:
        sys.stdout.write("\n")  # Initial newline
        sys.stdout.write("=== Progress Display ===\n")  # Header with newline
        sys.stdout.write("\n".join(lines))  # Content
        sys.stdout.write("\n")  # Final newline
        sys.stdout.flush()
        _display_started = True
        _last_line_count = total_lines
    else:
        # Move cursor up to the start of the previous display
        sys.stdout.write(f"\033[{_last_line_count-len(speakers_info)}A")
        # Clear from cursor to end of screen
        sys.stdout.write("\033[J")
        # Write everything with explicit newlines
        sys.stdout.write("\n")  # Initial newline
        sys.stdout.write("=== Progress Display ===\n")  # Header with newline
        sys.stdout.write("\n".join(lines))  # Content
        sys.stdout.write("\n")  # Final newline
        sys.stdout.flush()
        _last_line_count = total_lines
