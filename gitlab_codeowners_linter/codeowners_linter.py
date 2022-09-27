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
import sys
from pathlib import Path

from gitlab_codeowners_linter.autofix import fix
from gitlab_codeowners_linter.checks import check
from gitlab_codeowners_linter.parser import parse_codeowners

# TODO: manage logging level via args
logging.basicConfig(level=logging.DEBUG)


class CodeownersViolations:
    def __init__(self):
        self.violation_error_messages = []
        self.section_names_sorted = False
        self.sections_with_blank_lines = []
        self.unsorted_paths_in_sections = []
        self.sections_with_duplicate_paths = []
        self.sections_with_non_existing_paths = []
        self.non_existing_paths = []


class OwnersList:
    def __init__(self, file_path, no_autofix):
        """
        file_path: path of the CODEOWNERS file
        """
        self.file_path = file_path
        self.codeowners_data = parse_codeowners(self.file_path)
        self.autofix = not no_autofix

    def lint(self):
        violations = check(self.codeowners_data)
        if self.autofix:
            fix(self.codeowners_data, violations, self.file_path)
        return violations


def lint_codeowners_file(codeowners_file, no_autofix):
    codeowners = OwnersList(codeowners_file, no_autofix)
    return codeowners.lint()


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
    if violations.violation_error_messages:
        logging.error(
            'There are the following linting violations: %s', violations.violation_error_messages)
        sys.exit(1)


if __name__ == '__main__':
    main()
