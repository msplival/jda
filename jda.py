#!/usr/bin/env python3

import argparse
from collections import defaultdict
import itertools
import os
import sys


def pretty_print_bytes(num_bytes):
    for unit in ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0


def main():
    parser = argparse.ArgumentParser(description="Process some parameters.")
    parser.add_argument('--summary', action='store_true', help='Print only summary (suppress normal output)')
    parser.add_argument('report_file', nargs='?', help='Mandatory report file (positional argument)')

    args = parser.parse_args()
    jdupes_report_filename = args.report_file

    if not jdupes_report_filename:
        parser.error('The report file must be specified using --report-file or as a positional argument.')

    if not os.path.exists(jdupes_report_filename):
        parser.error(f'Report file "{jdupes_report_filename}" does not exist.')

    file_id = 0
    directory_pairs = defaultdict(int)

    num_sets = 0
    dup_copies = 0
    wasted = 0

    if not args.summary:
        print(f'Reading {jdupes_report_filename}...', file=sys.stderr)

    with open(jdupes_report_filename, 'r', errors='replace') as report_file:
        line = report_file.readline().rstrip('\n')
        while line:
            if "bytes each" not in line and "byte  each" not in line:
                parser.error(f'{jdupes_report_filename} does not seem to be an fdupes/jdupes report file')

            file_id += 1
            file_size = int(line.split()[0])

            current_dirs = {}
            count_in_set = 0

            while True:
                line = report_file.readline().rstrip('\n')
                if not line:
                    break
                dir, file_name = os.path.split(line)
                if dir not in current_dirs:
                    current_dirs[dir] = file_size
                count_in_set += 1

            if count_in_set > 0:
                num_sets += 1
                if count_in_set > 1:
                    dup_copies += (count_in_set - 1)
                    wasted += (count_in_set - 1) * int(file_size)

            if not args.summary:
                sorted_dirs = sorted(current_dirs.items())
                for (d1, s1), (d2, s2) in itertools.combinations(sorted_dirs, 2):
                    shared_size = s1
                    if s1 != s2:
                        print(f'Warning: Unexpected discrepancy in file sizes between {d1[0]}/ and {d2[0]}/', file=sys.stderr)
                    sorted_pair = tuple(sorted((d1, d2)))
                    directory_pairs[sorted_pair] += shared_size

            line = report_file.readline().rstrip('\n')

    if args.summary:
        print(f"Duplicate sets: {num_sets}")
        print(f"Duplicate copies: {dup_copies}")
        print(f"Wasted space: {pretty_print_bytes(wasted)}")
        return

    print('Sorting directory pairs...', file=sys.stderr)
    sorted_directory_pairs = sorted(directory_pairs.items(), key=lambda x: -x[1])

    for pair in sorted_directory_pairs:
        print(f'Size: {pretty_print_bytes(pair[1])},  meld "{pair[0][0]}" "{pair[0][1]}"')


if __name__ == "__main__":
    main()
