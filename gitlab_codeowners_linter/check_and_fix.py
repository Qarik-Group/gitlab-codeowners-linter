from __future__ import annotations

import operator
import os
from functools import cmp_to_key

from pathspec import PathSpec

from gitlab_codeowners_linter.constants import DEFAULT_SECTION
from gitlab_codeowners_linter.parser import parse_codeowners
from gitlab_codeowners_linter.sorting import sort_paths


class OwnersList:
    def __init__(self, file_path, no_autofix):
        """
        file_path: path of the CODEOWNERS file
        """
        self.file_path = file_path
        self.codeowners_data = parse_codeowners(self.file_path)
        self.autofix = not no_autofix

    def check(self):
        violations = []

        if self._is_codeowners_empty():
            return violations

        # Are custom section names sorted?
        if [
            section.codeowner_section for section in self.codeowners_data[1:]
        ] != sorted(
            section.codeowner_section for section in self.codeowners_data[1:]
        ):
            violations.append('Sections are not sorted')
            if self.autofix:
                sorted_sections_names = sorted(
                    self.codeowners_data[1:],
                    key=operator.attrgetter('codeowner_section'),
                )
                codeowners_data_updated = []
                codeowners_data_updated.append(self.codeowners_data[0])
                codeowners_data_updated.extend(sorted_sections_names)
                self.codeowners_data = codeowners_data_updated

        # Are there blank lines in sections?
        sections_with_blank_lines = self._get_sections_with_blank_lines()
        if sections_with_blank_lines != []:
            violations.append(
                f"There are blank lines in the sections {', '.join(map(str, sections_with_blank_lines))}",
            )
            if self.autofix:
                codeowners_data_updated = []
                entries_updated = []
                for section in self.codeowners_data:
                    for entry in section.entries:
                        if not len(entry.path.strip()) == 0:
                            entries_updated.append(entry)
                    codeowners_data_updated.append(section)
                    codeowners_data_updated[-1].entries = entries_updated
                    entries_updated = []
                self.codeowners_data = codeowners_data_updated

        # Are there unsorted paths in sections?
        unsorted_paths_in_sections = self._get_unsorted_paths_in_sections()
        if unsorted_paths_in_sections != []:
            violations.append(
                f"The paths in sections {', '.join(map(str, unsorted_paths_in_sections))} are not sorted",
            )
            if self.autofix:
                codeowners_data_updated = []

                for section in self.codeowners_data:
                    sort_paths_key = cmp_to_key(sort_paths)

                    sorted_entries = sorted(
                        section.entries, key=sort_paths_key)
                    codeowners_data_updated.append(section)
                    codeowners_data_updated[-1].entries = sorted_entries

                self.codeowners_data = codeowners_data_updated

        # Are there duplicated paths?
        sections_with_duplicate_paths = self._get_sections_with_duplicate_paths()
        if sections_with_duplicate_paths != []:
            violations.append(
                f"The sections {', '.join(map(str, sections_with_duplicate_paths))} have duplicate paths",
            )
            if self.autofix:
                codeowners_updated = []
                for section in self.codeowners_data:
                    codeowners_updated.append(section)
                    if section.codeowner_section not in sections_with_duplicate_paths:
                        continue
                    updated_entries = []
                    for entry in section.entries:
                        if updated_entries == []:
                            updated_entries.append(entry)
                            continue
                        if entry.path == updated_entries[-1].path:
                            # we have a duplicate
                            updated_entries[-1].comments.extend(entry.comments)
                            new_owners = updated_entries[-1].owners + \
                                entry.owners
                            updated_entries[-1].owners = sorted(
                                list(set(new_owners)))
                            continue
                        updated_entries.append(entry)
                        codeowners_updated[-1].entries = updated_entries
                self.codeowners_data = codeowners_updated

        # Do paths exist?
        sections_with_non_existing_paths, non_existing_paths = self._get_non_existing_paths()
        if sections_with_non_existing_paths != []:
            violations.append(
                f"The sections {', '.join(map(str, sections_with_non_existing_paths))} have non-existing paths",
            )
            if self.autofix:
                codeowners_updated = []
                for i in range(0, len(self.codeowners_data)):
                    codeowners_updated.append(self.codeowners_data[i])
                    entries_updated = []
                    for entry in self.codeowners_data[i].entries:
                        if entry.path in non_existing_paths[i]:
                            continue
                        entries_updated.append(entry)
                    codeowners_updated[-1].entries = entries_updated
                self.codeowners_data = codeowners_updated

        if self.autofix:
            self._update_codeowners_file()
        return violations

    def _is_codeowners_empty(self):
        empty = False
        for section in self.codeowners_data:
            if not section.get_paths():
                empty = True
        return empty

    def _get_sections_with_blank_lines(self):
        sections_with_blank_lines = []
        for section in self.codeowners_data:
            if '' in section.get_paths():
                sections_with_blank_lines.append(section.codeowner_section)
        return sections_with_blank_lines

    def _get_unsorted_paths_in_sections(self):
        unsorted_sections = []
        sort_paths_key = cmp_to_key(sort_paths)
        for section in self.codeowners_data:
            if sorted(section.entries, key=sort_paths_key) != section.entries:
                unsorted_sections.append(section.codeowner_section)
        return unsorted_sections

    def _get_sections_with_duplicate_paths(self):
        sections_with_duplicate_paths = []
        for section in self.codeowners_data:
            if len(set(section.get_paths())) != len(section.get_paths()):
                sections_with_duplicate_paths.append(section.codeowner_section)
        return sections_with_duplicate_paths

    def _get_all_filepaths(self):
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

    def _get_non_existing_paths(self):
        sections_with_non_existing_paths = []
        non_existing_paths = []
        files = self._get_all_filepaths()
        for section in self.codeowners_data:
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

    def _update_codeowners_file(self):
        with open(self.file_path, 'w') as f:
            for section in self.codeowners_data:
                if section.codeowner_section != DEFAULT_SECTION:
                    f.write('\n')
                if section.comments:
                    for comment_line in section.comments:
                        f.write(f'{str(comment_line)}\n')
                if section.codeowner_section != DEFAULT_SECTION:
                    f.write(f'[{section.codeowner_section}]')
                f.write('\n')
                for entry in section.entries:
                    if entry.comments:
                        for comment_line in entry.comments:
                            f.write(f'{str(comment_line)}\n')
                    owners = ' '.join(str(x) for x in entry.owners)
                    f.write(f'{entry.path} {owners}\n')
        return
