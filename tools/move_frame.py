#!/usr/bin/env python3
"""Move or copy beamer frames between positions within a file or across files."""

import argparse
import re
import sys
from pathlib import Path


def parse_range(range_str: str) -> list[int]:
    """Parse a range string like '3-5' or '3' into a list of integers."""
    if '-' in range_str:
        parts = range_str.split('-')
        if len(parts) != 2:
            raise ValueError(f"Invalid range format: {range_str}")
        start, end = int(parts[0]), int(parts[1])
        if start > end:
            raise ValueError(f"Invalid range: start ({start}) > end ({end})")
        return list(range(start, end + 1))
    else:
        return [int(range_str)]


def parse_frames(content: str) -> list[tuple[int, int, str]]:
    r"""Parse content and return list of (start_idx, end_idx, frame_text) tuples.

    Includes preceding comment lines as part of each frame.
    Handles both \begin{frame}...\end{frame} and \frame{...} syntax.
    Skips \againframe references.
    """
    frames = []
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip \againframe (it's a reference, not a frame definition)
        if re.match(r'\s*\\againframe', line):
            i += 1
            continue

        # Look for \begin{frame}
        if re.match(r'\s*\\begin\{frame\}', line):
            # Collect preceding comment lines
            start_idx = i
            while start_idx > 0 and re.match(r'\s*%', lines[start_idx - 1]):
                start_idx -= 1

            # Find matching \end{frame}
            depth = 1
            end_idx = i + 1
            while end_idx < len(lines) and depth > 0:
                if re.match(r'\s*\\begin\{frame\}', lines[end_idx]):
                    depth += 1
                elif re.match(r'\s*\\end\{frame\}', lines[end_idx]):
                    depth -= 1
                end_idx += 1

            frame_text = '\n'.join(lines[start_idx:end_idx])
            frames.append((start_idx, end_idx, frame_text))
            i = end_idx

        # Look for \frame{...} shorthand (single line, e.g., \frame{\titlepage})
        elif re.match(r'\s*\\frame\{', line):
            # Collect preceding comment lines
            start_idx = i
            while start_idx > 0 and re.match(r'\s*%', lines[start_idx - 1]):
                start_idx -= 1

            # For single-line \frame{...}, just include that line
            frame_text = '\n'.join(lines[start_idx:i + 1])
            frames.append((start_idx, i + 1, frame_text))
            i += 1
        else:
            i += 1

    return frames


def get_frame_title(frame_text: str) -> str:
    """Extract frame title from frame text."""
    # Match \begin{frame}{Title} or \begin{frame}[options]{Title}
    match = re.search(r'\\begin\{frame\}(?:<[^>]*>)?(?:\[[^\]]*\])?\{([^}]*)\}', frame_text)
    if match:
        return match.group(1)
    # Match \frame{\titlepage} or similar
    match = re.search(r'\\frame\{\\(\w+)\}', frame_text)
    if match:
        return f"\\{match.group(1)}"
    return "(no title)"


def list_frames(input_file: Path) -> None:
    """List all frames with their numbers."""
    content = input_file.read_text()
    frames = parse_frames(content)

    if not frames:
        print(f"No frames found in {input_file}")
        return

    print(f"Frames in {input_file.name}:")
    for i, (_, _, frame_text) in enumerate(frames, 1):
        title = get_frame_title(frame_text)
        print(f"  {i}: {title}")


def delete_frames(input_file: Path, from_positions: list[int]) -> None:
    """Delete frame(s) from the file."""
    content = input_file.read_text()
    frames = parse_frames(content)

    if not frames:
        print(f"Error: No frames found in {input_file}", file=sys.stderr)
        sys.exit(1)

    # Validate all from positions
    for pos in from_positions:
        if pos < 1 or pos > len(frames):
            print(f"Error: --from {pos} is out of range (1-{len(frames)})", file=sys.stderr)
            sys.exit(1)

    lines = content.split('\n')

    # Remove frames in reverse order to preserve indices
    for pos in reversed(from_positions):
        start_idx, end_idx, _ = frames[pos - 1]
        lines = lines[:start_idx] + lines[end_idx:]

    input_file.write_text('\n'.join(lines))
    from_range_str = f"{from_positions[0]}-{from_positions[-1]}" if len(from_positions) > 1 else str(from_positions[0])
    print(f"Deleted frame(s) {from_range_str} from {input_file.name}")


def move_frames(input_file: Path, from_positions: list[int], to_pos: int,
                output_file: Path | None, copy_mode: bool) -> None:
    """Move or copy frame(s) from one position to another."""
    content = input_file.read_text()
    frames = parse_frames(content)

    if not frames:
        print(f"Error: No frames found in {input_file}", file=sys.stderr)
        sys.exit(1)

    # Validate all from positions
    for pos in from_positions:
        if pos < 1 or pos > len(frames):
            print(f"Error: --from {pos} is out of range (1-{len(frames)})", file=sys.stderr)
            sys.exit(1)

    # Get the frames to move (combined text)
    frame_texts = [frames[pos - 1][2] for pos in from_positions]
    combined_frame_text = '\n'.join(frame_texts)
    from_range_str = f"{from_positions[0]}-{from_positions[-1]}" if len(from_positions) > 1 else str(from_positions[0])

    # Determine destination
    if output_file and output_file != input_file:
        # Cross-file operation
        if not output_file.exists():
            print(f"Error: Output file {output_file} does not exist", file=sys.stderr)
            sys.exit(1)

        dest_content = output_file.read_text()
        dest_frames = parse_frames(dest_content)

        if to_pos < 1 or to_pos > len(dest_frames) + 1:
            print(f"Error: --to {to_pos} is out of range (1-{len(dest_frames) + 1})", file=sys.stderr)
            sys.exit(1)

        # Insert into destination
        dest_lines = dest_content.split('\n')
        if to_pos <= len(dest_frames):
            insert_at = dest_frames[to_pos - 1][0]
        else:
            insert_at = dest_frames[-1][1] if dest_frames else len(dest_lines)

        new_dest_lines = dest_lines[:insert_at] + combined_frame_text.split('\n') + dest_lines[insert_at:]
        output_file.write_text('\n'.join(new_dest_lines))
        print(f"Inserted frame(s) {from_range_str} at position {to_pos} in {output_file.name}")

        # Remove from source if move mode
        if not copy_mode:
            lines = content.split('\n')
            # Remove frames in reverse order to preserve indices
            for pos in reversed(from_positions):
                start_idx, end_idx, _ = frames[pos - 1]
                lines = lines[:start_idx] + lines[end_idx:]
            input_file.write_text('\n'.join(lines))
            print(f"Removed frame(s) {from_range_str} from {input_file.name}")
    else:
        # In-place operation
        if to_pos < 1 or to_pos > len(frames):
            print(f"Error: --to {to_pos} is out of range (1-{len(frames)})", file=sys.stderr)
            sys.exit(1)

        # Check if moving to same position (no-op for single frame)
        if len(from_positions) == 1 and from_positions[0] == to_pos:
            print("Nothing to do: source and destination are the same")
            return

        lines = content.split('\n')

        # For contiguous ranges, get the span from first to last frame
        first_frame_start = frames[from_positions[0] - 1][0]
        last_frame_end = frames[from_positions[-1] - 1][1]

        # Remove the entire range at once
        lines_without_moved = lines[:first_frame_start] + lines[last_frame_end:]

        # Calculate how many lines were removed
        removed_count = last_frame_end - first_frame_start

        # Determine insert position based on remaining frames
        # Build list of remaining frame positions after removal
        remaining_frame_idx = 0
        insert_at = 0

        for i, (s, e, _) in enumerate(frames):
            if (i + 1) in from_positions:
                continue  # Skip removed frames

            remaining_frame_idx += 1
            # Adjust position if frame was after the removed range
            adj_s = s - removed_count if s > first_frame_start else s

            if remaining_frame_idx == to_pos:
                insert_at = adj_s
                break
        else:
            # Insert at end if to_pos is past all remaining frames
            if frames:
                last_remaining = None
                for i, (s, e, _) in enumerate(frames):
                    if (i + 1) not in from_positions:
                        adj_e = e - removed_count if e > first_frame_start else e
                        last_remaining = adj_e
                insert_at = last_remaining if last_remaining else len(lines_without_moved)

        # Insert the moved frames at the new position
        final_lines = lines_without_moved[:insert_at] + combined_frame_text.split('\n') + lines_without_moved[insert_at:]

        dest = output_file if output_file else input_file
        dest.write_text('\n'.join(final_lines))
        print(f"Moved frame(s) {from_range_str} to position {to_pos} in {dest.name}")


def main():
    parser = argparse.ArgumentParser(
        description='Move or copy beamer frames between positions.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s lecture.tex --list                      # List all frames
  %(prog)s lecture.tex --from 5 --to 3             # Move frame 5 to position 3
  %(prog)s lecture.tex --from 3-5 --to 1           # Move frames 3-5 to position 1
  %(prog)s lecture.tex --from 4-12 --delete        # Delete frames 4-12
  %(prog)s a.tex -o b.tex --from 2-4 --to 1 --copy # Copy frames to another file
''')

    parser.add_argument('input_file', type=Path, help='Source .tex file')
    parser.add_argument('--from', dest='from_pos', type=str, metavar='N|N-M',
                        help='Frame number or range to move (1-indexed, e.g., 5 or 3-5)')
    parser.add_argument('--to', dest='to_pos', type=int, metavar='N',
                        help='Destination position (1-indexed)')
    parser.add_argument('-o', '--output', type=Path, metavar='FILE',
                        help='Destination file (defaults to in-place)')
    parser.add_argument('--copy', action='store_true',
                        help='Copy mode - keep original frame')
    parser.add_argument('--move', action='store_true',
                        help='Move mode - remove from source (default for cross-file)')
    parser.add_argument('--delete', action='store_true',
                        help='Delete the specified frame(s)')
    parser.add_argument('--list', action='store_true',
                        help='List all frames with numbers')

    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Error: Input file {args.input_file} does not exist", file=sys.stderr)
        sys.exit(1)

    if args.list:
        list_frames(args.input_file)
        return

    if args.from_pos is None:
        parser.error("--from is required when not using --list")

    if args.delete:
        try:
            from_positions = parse_range(args.from_pos)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        delete_frames(args.input_file, from_positions)
        return

    if args.to_pos is None:
        parser.error("--to is required when not using --list or --delete")

    try:
        from_positions = parse_range(args.from_pos)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    copy_mode = args.copy and not args.move
    move_frames(args.input_file, from_positions, args.to_pos, args.output, copy_mode)


if __name__ == '__main__':
    main()
