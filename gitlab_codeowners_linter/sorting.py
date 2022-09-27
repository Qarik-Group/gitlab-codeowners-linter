from __future__ import annotations


def sort_paths(entry1, entry2):
    line1 = entry1.path.lower()
    line2 = entry2.path.lower()
    if line1.startswith('*') and line2.startswith('*'):
        return -1 if (line1 < line2) else 1
    if line1.startswith('*'):
        return -1
    if line2.startswith('*'):
        return 1
    if line1.startswith('/') and line2.startswith('/'):
        return -1 if (line1 < line2) else 1
    if line1.startswith('/'):
        return 1
    if line2.startswith('/'):
        return -1

    return -1 if (line1 < line2) else 1
