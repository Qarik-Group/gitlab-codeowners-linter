from __future__ import annotations

import re


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
    section_name1 = re.search(re.compile(
        r'\[([^]]*)\]'), section1.codeowner_section).group(1).lower()
    section_name2 = re.search(re.compile(
        r'\[([^]]*)\]'), section2.codeowner_section).group(1).lower()
    is_section_1_optional = section1.codeowner_section.startswith('^')
    is_section_2_optional = section2.codeowner_section.startswith('^')

    if section_name1 == section_name2:
        if is_section_1_optional and is_section_2_optional:
            return 0
        if is_section_1_optional:
            return -1
        if is_section_2_optional:
            return 1
        return 0
    return -1 if (section_name1 < section_name2) else 1
