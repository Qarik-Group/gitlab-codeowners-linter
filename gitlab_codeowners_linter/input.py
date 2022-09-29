from __future__ import annotations

import argparse
from pathlib import Path

from gitlab_codeowners_linter.constants import VALID_CODEOWNERS_PATHS


def _parse_arguments(args):
    parser = argparse.ArgumentParser(description='Check codeowners file')
    parser.add_argument('--codeowners_file', type=Path, required=False,
                        help='path to the codeowners file')
    parser.add_argument(
        '--no_autofix',
        default=False,
        required=False,
        action='store_true',
        help='Set to disable autofix',
    )
    return parser.parse_known_args(args)


def _get_codeowners_path(positional_args):
    for arg in positional_args:
        if arg in VALID_CODEOWNERS_PATHS:
            return arg
    return None


def get_arguments(args):
    args, positional_args = _parse_arguments(args)
    codeowners_file = None
    if str(args.codeowners_file) in VALID_CODEOWNERS_PATHS:
        codeowners_file = args.codeowners_file
    elif not args.codeowners_file:
        codeowners_file = _get_codeowners_path(positional_args)
    else:
        print("You didn't provide a valid path for the CODEOWNERS file")
    return codeowners_file, args.no_autofix
