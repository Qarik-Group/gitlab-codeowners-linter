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

from gitlab_codeowners_linter.check_and_fix import OwnersList

# TODO: manage logging level via args
logging.basicConfig(level=logging.DEBUG)


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
