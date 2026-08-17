"""
detect_live_v1_reconstructed.py

SUPERSEDED — kept for the record only. Do not use.

This was a reconstruction of StopSign.py built from chat logs and terminal
output alone, before the Pi's SD card was recovered and the real file found.
Every numeric parameter it contains (threshold 0.88, input size 64x64,
serial message format, Arduino reset delay) was independently confirmed by
terminal output and turned out correct.

What it got wrong: it invented a simpler single-purpose script. The real
file (now at ../inference/detect_live.py) has a full CLI with --input and
--display flags and a batch/directory-processing mode that never appeared
in any chat log — there was no way to know it existed without the actual
file. See PROVENANCE.md for the full comparison.

Kept as a demonstration that a transcript can verify facts (numbers,
formats, behaviour that was printed or described) but not structure that
was never described.
"""
