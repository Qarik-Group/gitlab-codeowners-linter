from __future__ import annotations

import operator
from functools import cmp_to_key

from gitlab_codeowners_linter.constants import DEFAULT_SECTION
from gitlab_codeowners_linter.sorting import sort_paths


def fix(codeowners_data, violations, file_path):
    # Are custom section names sorted?
    if violations.section_names_sorted:
        sorted_sections_names = sorted(
            codeowners_data[1:],
            key=operator.attrgetter('codeowner_section'),
        )
        codeowners_data_updated = []
        codeowners_data_updated.append(codeowners_data[0])
        codeowners_data_updated.extend(sorted_sections_names)
        codeowners_data = codeowners_data_updated

    # Are there blank lines in sections?
    if violations.sections_with_blank_lines != []:
        codeowners_data_updated = []
        entries_updated = []
        for section in codeowners_data:
            for entry in section.entries:
                if not len(entry.path.strip()) == 0:
                    entries_updated.append(entry)
            codeowners_data_updated.append(section)
            codeowners_data_updated[-1].entries = entries_updated
            entries_updated = []
        codeowners_data = codeowners_data_updated

    # Are there unsorted paths in sections?
    if violations.unsorted_paths_in_sections != []:
        codeowners_data_updated = []

        for section in codeowners_data:
            sort_paths_key = cmp_to_key(sort_paths)

            sorted_entries = sorted(
                section.entries, key=sort_paths_key)
            codeowners_data_updated.append(section)
            codeowners_data_updated[-1].entries = sorted_entries

        codeowners_data = codeowners_data_updated

    # Are there duplicated paths?
    if violations.sections_with_duplicate_paths != []:
        codeowners_updated = []
        for section in codeowners_data:
            codeowners_updated.append(section)
            if section.codeowner_section not in violations.sections_with_duplicate_paths:
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
        codeowners_data = codeowners_updated

    # Do paths exist?
    if violations.sections_with_non_existing_paths != []:
        codeowners_updated = []
        for i in range(0, len(codeowners_data)):
            codeowners_updated.append(codeowners_data[i])
            entries_updated = []
            for entry in codeowners_data[i].entries:
                if entry.path in violations.non_existing_paths[i]:
                    continue
                entries_updated.append(entry)
            codeowners_updated[-1].entries = entries_updated
        codeowners_data = codeowners_updated

    _update_codeowners_file(codeowners_data, file_path)


def _update_codeowners_file(codeowners_data, file_path):
    with open(file_path, 'w') as f:
        for section in codeowners_data:
            # if the default section is empty let's skip it
            if section.codeowner_section == DEFAULT_SECTION and section.entries == []:
                continue
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
