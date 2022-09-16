# Gitlab CODEOWNERS linter
# What we want to check:
# The CODEOWNERS file must be formatted respecting the following rules:
#   - every section must be sorted alphabetically
#   - within a section, paths must be ordered alphabetically
#   - there must be no empty lines between paths
#   - paths in a section must be unique
#   - paths must exist
#   Note: there's the assumption that on the top of the file there are paths that
#       are not under any section. This may not be always true, like in a CODEOWNERS
#       file that only uses sections TODO: manage this corner case
#
from __future__ import annotations

import argparse
import logging
import operator
import os
import re
import sys
from functools import cmp_to_key
from pathlib import Path


DEFAULT_SECTION = '__default_codeowner_section__'


# TODO: manage logging level via args
logging.basicConfig(level=logging.DEBUG)


class CodeownerSection:
    def __init__(self, section_name, comment_block, entries):
        self.codeowner_section = section_name
        self.comments = comment_block
        self.entries = entries

    def get_paths(self):
        return [entries.path for entries in self.entries]


class CodeownerEntry:
    def __init__(self, path, comment_block, owners=''):
        self.path = path
        self.comments = comment_block
        self.owners = owners


class OwnersList:
    def __init__(self, file_path, no_autofix):
        """
        file_path: path of the CODEOWNERS file
        """
        self.file_path = file_path
        self.codeowners_data = self.parse_codeowners()
        self.autofix = not no_autofix

    def check(self):
        violations = []

        if self.is_codeowners_empty():
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
        sections_with_blank_lines = self.get_sections_with_blank_lines()
        if sections_with_blank_lines != []:
            violations.append(
                f"There are blank lines in the sections {', '.join(map(str, sections_with_blank_lines))}",
            )
            if self.autofix:
                codeowners_data_updated = []
                entries_updated = []
                for section in self.codeowners_data:
                    for entry in section.entries:
                        if not self.is_empty_line(entry.path):
                            entries_updated.append(entry)
                    codeowners_data_updated.append(section)
                    codeowners_data_updated[-1].entries = entries_updated
                    entries_updated = []
                self.codeowners_data = codeowners_data_updated

        # Are there unsorted paths in sections?
        unsorted_paths_in_sections = self.get_unsorted_paths_in_sections()
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
        sections_with_duplicate_paths = self.get_sections_with_duplicate_paths()
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
        sections_with_non_existing_paths = self.get_sections_with_non_existing_paths()
        if sections_with_non_existing_paths != []:
            violations.append(
                f"The sections {', '.join(map(str, sections_with_non_existing_paths))} have non-existing paths",
            )
            if self.autofix:
                codeowners_updated = []
                for section in self.codeowners_data:
                    codeowners_updated.append(section)
                    entries_updated = []
                    for entry in section.entries:
                        if not os.path.exists(entry.path):
                            continue
                        entries_updated.append(entry)
                    codeowners_updated[-1].entries = entries_updated
                self.codeowners_data = codeowners_updated

        if self.autofix:
            self.update_codeowners_file()
        return violations

    def is_codeowners_empty(self):
        empty = False
        for section in self.codeowners_data:
            if not section.get_paths():
                empty = True
        return empty

    def get_sections_with_blank_lines(self):
        sections_with_blank_lines = []
        for section in self.codeowners_data:
            if '' in section.get_paths():
                sections_with_blank_lines.append(section.codeowner_section)
        return sections_with_blank_lines

    def get_unsorted_paths_in_sections(self):
        unsorted_sections = []
        sort_paths_key = cmp_to_key(sort_paths)
        for section in self.codeowners_data:
            if sorted(section.entries, key=sort_paths_key) != section.entries:
                unsorted_sections.append(section.codeowner_section)
        return unsorted_sections

    def get_sections_with_duplicate_paths(self):
        sections_with_duplicate_paths = []
        for section in self.codeowners_data:
            if len(set(section.get_paths())) != len(section.get_paths()):
                sections_with_duplicate_paths.append(section.codeowner_section)
        return sections_with_duplicate_paths

    def get_sections_with_non_existing_paths(self):
        sections_with_non_existing_paths = []
        for section in self.codeowners_data:
            for path in section.get_paths():
                if not os.path.exists(path):
                    sections_with_non_existing_paths.append(
                        section.codeowner_section)
                    break
        return sections_with_non_existing_paths

    def update_codeowners_file(self):
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

    def parse_codeowners(self):
        section_regex = re.compile(r'\[(.*?)\]')

        codeowners_content = [CodeownerSection(DEFAULT_SECTION, [], [])]
        comments_block = []

        lines = self.get_lines()
        for line in lines:
            if line.startswith('#'):
                comments_block.append(line.rstrip())
                continue
            if self.is_empty_line(line):
                if self.is_top_of_section(codeowners_content):
                    # TODO: note that if we have a CODEOWNERS file with a black line on top, that line will be threated as a comment line for the first general section
                    codeowners_content[-1].comments.extend(comments_block)
                    comments_block = []
                    continue
                if self.is_consecutive_blank_line_in_section(codeowners_content):
                    # we just need 1 consecutive blank line in a section, ignore if more
                    continue
                # here we have a new blank entry, let's append it
                codeowners_content[-1].entries.append(
                    CodeownerEntry(line.rstrip(), comments_block),
                )
                comments_block = []
                continue
            if section_regex.search(line):
                # TODO: handle sections with duplicate names
                # TODO: manage gitlab optional sections, the ones starting with ^
                # TODO: at the moment for any section with a following comment like
                #       [Section]#this is a comment
                #       the comment is ignored without any message to the user.
                #       A solution could be to create a function that scans all the parsed lines for
                #       trailing comments, both on gitlab sections names and on entries, and appends them to
                #       the proper comment space, CodeownerSection.comments or CodeownerEntry.comments

                # Here we have a new section

                codeowners_content.append(
                    CodeownerSection(
                        section_regex.search(line).group(
                            1), comments_block, [],
                    ),
                )
                comments_block = []
                continue
            # if we arrive here it means we have a new entry
            codeowners_content[-1].entries.append(
                CodeownerEntry(line.rstrip().split()[
                               0], comments_block, line.rstrip().split()[1:]),
            )
            comments_block = []

        # before returning, let's normalize the data by removing the trailing empty line at the end of every section
        for section in codeowners_content:
            if section.entries:
                if self.is_empty_line(section.entries[-1].path):
                    section.entries = section.entries[:-1]

        return codeowners_content

    def get_lines(self):
        path_to_file = Path(self.file_path)
        with path_to_file.open() as f:
            return f.readlines()

    def is_top_of_section(self, codeowners_content):
        return len(codeowners_content[-1].entries) == 0

    def is_empty_line(self, line):
        return len(line.strip()) == 0

    def is_consecutive_blank_line_in_section(self, codeowners_content):
        return len(codeowners_content[-1].entries) > 0 and self.is_empty_line(
            codeowners_content[-1].entries[-1].path,
        )


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


def lint_codeowners_file(codeowners_file, no_autofix):
    codeowners = OwnersList(codeowners_file, no_autofix)
    return codeowners.check()


def parse_arguments(args):
    parser = argparse.ArgumentParser(description='Check codeowners file')
    parser.add_argument('--codeowners_file', type=Path,
                        help='path to the codeowners file')
    parser.add_argument(
        '--no_autofix',
        default=False,
        required=False,
        action='store_true',
        help='Set to disable autofix',
    )
    return parser.parse_known_args(args)


def main():
    args, _ = parse_arguments(sys.argv[1:])
    violations = lint_codeowners_file(
        args.codeowners_file, args.no_autofix)
    if violations:
        logging.error(
            'There are the following linting violations: %s', violations)
        sys.exit(1)


if __name__ == '__main__':
    main()
