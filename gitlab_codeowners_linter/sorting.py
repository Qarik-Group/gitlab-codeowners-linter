from __future__ import annotations


def sort_paths(entry1, entry2):
    line1 = entry1.path.lower()
    line2 = entry2.path.lower()
    if len(line1) == 0 or len(line2) == 0:
        return 0
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


def sort_section_names(section1, section2):
    section_name1 = section1.codeowner_section.lower()
    section_name2 = section2.codeowner_section.lower()
    if section_name1 == section_name2:
        return 0
    return -1 if (section_name1 < section_name2) else 1
