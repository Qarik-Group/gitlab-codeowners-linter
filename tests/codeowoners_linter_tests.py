from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from dataclasses import dataclass
from functools import cmp_to_key
from pathlib import Path
from typing import List

from gitlab_codeowners_linter.codeowners_linter import CodeownerEntry
from gitlab_codeowners_linter.codeowners_linter import CodeownerSection
from gitlab_codeowners_linter.codeowners_linter import lint_codeowners_file
from gitlab_codeowners_linter.codeowners_linter import sort_paths


class Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_sort_function(self):
        @dataclass
        class TestCase:
            name: str
            input: list[str]
            expected: list[str]

        testcases = [
            TestCase(
                name='unsorted',
                input=[
                    '*.md test@email.com',
                    '.gitlab test@email.com',
                    '/.pylintrc test@email.com',
                    '/ui test@email.com',
                    '* test@email.com',
                    '/ui/components/ test@email.com',
                    '/ui/lighting test@email.com',
                    '/ui/lighting/client test@email.com',
                    'WORKSPACE test@email.com',
                    '/WORKSPACE test@email.com',
                    '/www/ test@email.com',
                    '/www/gitlab/test/pa test@email.com #this is a comment',
                    '/www/**/*.md test@email.com',
                    r'\#file_with_pound.rb test@email.com',
                    '/www/* test@email.com',
                ],
                expected=[
                    '* test@email.com',
                    '*.md test@email.com',
                    '.gitlab test@email.com',
                    r'\#file_with_pound.rb test@email.com',
                    'WORKSPACE test@email.com',
                    '/.pylintrc test@email.com',
                    '/ui test@email.com',
                    '/ui/components/ test@email.com',
                    '/ui/lighting test@email.com',
                    '/ui/lighting/client test@email.com',
                    '/WORKSPACE test@email.com',
                    '/www/ test@email.com',
                    '/www/* test@email.com',
                    '/www/**/*.md test@email.com',
                    '/www/gitlab/test/pa test@email.com #this is a comment',
                ],
            ),
            TestCase(name='empty_slice', input=[], expected=[]),
            TestCase(
                name='already_sorted',
                input=[
                    '* test@email.com',
                    '*.md test@email.com',
                    '.gitlab test@email.com',
                    r'\#file_with_pound.rb test@email.com',
                    'WORKSPACE test@email.com',
                    '/.pylintrc test@email.com',
                    '/ui test@email.com',
                    '/ui/components/ test@email.com',
                    '/ui/lighting test@email.com',
                    '/ui/lighting/client test@email.com',
                    '/WORKSPACE test@email.com',
                    '/www/ test@email.com',
                    '/www/gitlab/test/pa test@email.com #this is a comment',
                ],
                expected=[
                    '* test@email.com',
                    '*.md test@email.com',
                    '.gitlab test@email.com',
                    r'\#file_with_pound.rb test@email.com',
                    'WORKSPACE test@email.com',
                    '/.pylintrc test@email.com',
                    '/ui test@email.com',
                    '/ui/components/ test@email.com',
                    '/ui/lighting test@email.com',
                    '/ui/lighting/client test@email.com',
                    '/WORKSPACE test@email.com',
                    '/www/ test@email.com',
                    '/www/gitlab/test/pa test@email.com #this is a comment',
                ],
            ),
        ]
        sort_paths_key = cmp_to_key(sort_paths)

        for case in testcases:
            data = CodeownerSection('Test', [], [])
            actual = data
            for path in case.input:
                data.entries.append(CodeownerEntry(path, ''))
            actual.entries = sorted(data.entries, key=sort_paths_key)
            self.assertListEqual(
                case.expected,
                actual.get_paths(),
                'failed test {} expected {}, actual {}'.format(
                    case.name,
                    case.expected,
                    actual.get_paths(),
                ),
            )

    def test_autofix_feature(self):
        @dataclass
        class TestCase:
            name: str
            input: Path
            expected_check: list[str]
            expected_fix: Path

        testcases = [
            TestCase(
                name='already_formatted',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/formatted_input.txt',
                ),
                expected_check=[],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/formatted_autofix.txt',
                ),
            ),
            TestCase(
                name='not_formatted',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/unformatted_input.txt',
                ),
                expected_check=[
                    'Sections are not sorted',
                    'There are blank lines in the sections __default_codeowner_section__, BUILD, SECURITY',
                    'The paths in sections __default_codeowner_section__, BUILD, SYSTEM, TEST_SECTION are not sorted',
                    'The sections __default_codeowner_section__ have duplicate paths',
                ],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/unformatted_autofix.txt',
                ),
            ),
            TestCase(
                name='empty_file',
                input=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/empty_input.txt',
                ),
                expected_check=[],
                expected_fix=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'resources/empty_autofix.txt',
                ),
            ),
        ]
        for case in testcases:
            actual = os.path.join(
                self.test_dir,
                'formatted_autofix_input.txt',
            )
            shutil.copyfile(case.input, actual)
            violations = lint_codeowners_file(actual, True)
            self.assertEqual(violations, case.expected_check)
            with open(actual) as input, open(case.expected_fix) as expected_output:
                self.assertListEqual(
                    list(input),
                    list(expected_output),
                    'failed autofix feature for test {} expected {}, actual {}'.format(
                        case.name,
                        case.expected_fix,
                        actual,
                    ),
                )


if __name__ == '__main__':
    unittest.main()
