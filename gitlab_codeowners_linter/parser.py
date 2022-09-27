from __future__ import annotations

import re
from pathlib import Path

from gitlab_codeowners_linter.constants import DEFAULT_SECTION


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


def _get_lines(file_path):
    path_to_file = Path(file_path)
    with path_to_file.open() as f:
        return f.readlines()


def _is_top_of_section(codeowners_content):
    return len(codeowners_content[-1].entries) == 0


def _is_empty_line(line):
    return len(line.strip()) == 0


def _is_consecutive_blank_line_in_section(codeowners_content):
    return len(codeowners_content[-1].entries) > 0 and _is_empty_line(
        codeowners_content[-1].entries[-1].path,
    )


def parse_codeowners(file_path):
    section_regex = re.compile(r'\[(.*?)\]')

    codeowners_content = [CodeownerSection(DEFAULT_SECTION, [], [])]
    comments_block = []

    lines = _get_lines(file_path)
    for line in lines:
        if line.startswith('#'):
            comments_block.append(line.rstrip())
            continue
        if _is_empty_line(line):
            if _is_top_of_section(codeowners_content):
                # TODO: note that if we have a CODEOWNERS file with a black line on top, that line will be threated as a comment line for the first general section
                codeowners_content[-1].comments.extend(comments_block)
                comments_block = []
                continue
            if _is_consecutive_blank_line_in_section(codeowners_content):
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
            if _is_empty_line(section.entries[-1].path):
                section.entries = section.entries[:-1]

    return codeowners_content
