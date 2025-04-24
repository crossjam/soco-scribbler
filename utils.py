"""
Utility functions for the Sonos Last.fm scrobbler.
"""

import sys
from typing import Dict
import logging

# Track display state
_last_line_count = 0
_display_started = False
_log_lines_since_last_display = 0


class LogLineCounter(logging.Handler):
    def emit(self, record):
        global _log_lines_since_last_display
        _log_lines_since_last_display += 1


# Add our custom handler to the root logger
logging.getLogger().addHandler(LogLineCounter())


def custom_print(message: str, level: str = "INFO") -> None:
    """
    Custom print function that tracks lines and formats output consistently.

    Args:
        message: The message to print
        level: The log level (INFO, WARNING, ERROR, etc.)
    """
    global _log_lines_since_last_display

    # Count how many newlines are in the message
    newline_count = message.count("\n")

    # Format the message with timestamp and level
    timestamp = logging.Formatter("%(asctime)s").format(
        logging.LogRecord("", 0, "", 0, None, None, None)
    )
    formatted_message = f"{timestamp[:-4]} - {level} - {message}"

    # Print the message
    print(formatted_message, flush=True)

    # Update the line counter - add 1 for the print itself plus any additional newlines in the message
    _log_lines_since_last_display += 1 + newline_count


def reset_log_line_counter():
    """Reset the counter for log lines since last display update."""
    global _log_lines_since_last_display
    _log_lines_since_last_display = 0


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
    global _last_line_count, _display_started, _log_lines_since_last_display

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
        # Move past any existing log lines
        if _log_lines_since_last_display > 0:
            sys.stdout.write("\n")  # Add extra newline after logs
        sys.stdout.write("\n")  # Initial newline
        sys.stdout.write("=== Progress Display ===\n")  # Header with newline
        sys.stdout.write("\n".join(lines))  # Content
        sys.stdout.write("\n")  # Final newline
        sys.stdout.flush()
        _display_started = True
        _last_line_count = total_lines
    else:
        # BEGIN OF IMPORTANT CODE #
        clean_up_lines = _last_line_count - len(speakers_info)
        total_move_up = _log_lines_since_last_display + clean_up_lines

        # Move cursor up by total_move_up lines
        sys.stdout.write(f"\033[{total_move_up}A")
        # Clear only clean_up_lines number of lines
        for _ in range(clean_up_lines):
            sys.stdout.write("\033[K")  # Clear current line
            sys.stdout.write("\033[1B")  # Move down 1 line
        # Move back to start position
        sys.stdout.write(f"\033[{clean_up_lines}A")
        # END of IMPORANT CODE #

        # Add extra newline after any new log messages
        if _log_lines_since_last_display > 0:
            sys.stdout.write("\n")

        # Write everything with explicit newlines
        sys.stdout.write("\n")  # Initial newline
        sys.stdout.write("=== Progress Display ===\n")  # Header with newline
        sys.stdout.write("\n".join(lines))  # Content
        sys.stdout.write("\n")  # Final newline
        sys.stdout.flush()
        _last_line_count = total_lines

    # Reset the log line counter after updating display
    reset_log_line_counter()
