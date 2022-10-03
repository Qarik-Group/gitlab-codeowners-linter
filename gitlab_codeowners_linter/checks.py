from __future__ import annotations

import os
from functools import cmp_to_key

from pathspec import PathSpec

from gitlab_codeowners_linter.sorting import sort_paths


class CodeownersViolations:
    def __init__(self):
        self.violation_error_messages = []
        self.section_names_sorted = False
        self.sections_with_blank_lines = []
        self.unsorted_paths_in_sections = []
        self.sections_with_duplicate_paths = []
        self.sections_with_non_existing_paths = []
        self.non_existing_paths = []


def check(codeowners_data):
    violations = CodeownersViolations()

    if _is_codeowners_empty(codeowners_data):
        return violations

    # Are custom section names sorted?
    if [
        section.codeowner_section for section in codeowners_data[1:]
    ] != sorted(
        section.codeowner_section for section in codeowners_data[1:]
    ):
        violations.violation_error_messages.append('Sections are not sorted')
        violations.section_names_sorted = True

    # Are there blank lines in sections?
    violations.sections_with_blank_lines = _get_sections_with_blank_lines(
        codeowners_data)
    if violations.sections_with_blank_lines != []:
        violations.violation_error_messages.append(
            f"There are blank lines in the sections {', '.join(map(str, violations.sections_with_blank_lines))}",
        )

    # Are there unsorted paths in sections?
    violations.unsorted_paths_in_sections = _get_unsorted_paths_in_sections(
        codeowners_data)
    if violations.unsorted_paths_in_sections != []:
        violations.violation_error_messages.append(
            f"The paths in sections {', '.join(map(str, violations.unsorted_paths_in_sections))} are not sorted",
        )

    # Are there duplicated paths?
    violations.sections_with_duplicate_paths = _get_sections_with_duplicate_paths(
        codeowners_data)
    if violations.sections_with_duplicate_paths != []:
        violations.violation_error_messages.append(
            f"The sections {', '.join(map(str, violations.sections_with_duplicate_paths))} have duplicate paths",
        )

    # Do paths exist?
    violations.sections_with_non_existing_paths, violations.non_existing_paths = _get_non_existing_paths(
        codeowners_data)
    if violations.sections_with_non_existing_paths != []:
        violations.violation_error_messages.append(
            f"The sections {', '.join(map(str, violations.sections_with_non_existing_paths))} have non-existing paths",
        )

    return violations


def _is_codeowners_empty(codeowners_data):
    empty = False
    if all(not section.get_paths() for section in codeowners_data):
        empty = True
    return empty


def _get_sections_with_blank_lines(codeowners_data):
    sections_with_blank_lines = []
    for section in codeowners_data:
        if '' in section.get_paths():
            sections_with_blank_lines.append(section.codeowner_section)
    return sections_with_blank_lines


def _get_unsorted_paths_in_sections(codeowners_data):
    unsorted_sections = []
    sort_paths_key = cmp_to_key(sort_paths)
    for section in codeowners_data:
        if sorted(section.entries, key=sort_paths_key) != section.entries:
            unsorted_sections.append(section.codeowner_section)
    return unsorted_sections


def _get_sections_with_duplicate_paths(codeowners_data):
    sections_with_duplicate_paths = []
    for section in codeowners_data:
        if len(set(section.get_paths())) != len(section.get_paths()):
            sections_with_duplicate_paths.append(section.codeowner_section)
    return sections_with_duplicate_paths


def _get_all_filepaths():
    """
    This function will generate the file names in a directory
    tree by walking the tree
    """
    file_paths = []  # List which will store all of the full filepaths.

    for root, _, files in os.walk('.'):
        for filename in files:
            # Join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            # we ignore the ./ at the beginning of the path
            file_paths.append(filepath[2:])

    return file_paths  # Self-explanatory.


def _get_non_existing_paths(codeowners_data):
    sections_with_non_existing_paths = []
    non_existing_paths = []
    files = _get_all_filepaths()
    for section in codeowners_data:
        spec = PathSpec.from_lines(
            'gitwildmatch', list(section.get_paths()))
        data = list(zip(section.get_paths(), spec.patterns))
        non_existing_paths_in_section = []
        for path, pattern in data:
            match = list(filter(pattern.regex.match, files))
            if not match:
                non_existing_paths_in_section.append(path)
        if non_existing_paths_in_section:
            sections_with_non_existing_paths.append(
                section.codeowner_section)
        non_existing_paths.append(non_existing_paths_in_section)

    return sections_with_non_existing_paths, non_existing_paths
