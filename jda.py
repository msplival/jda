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

    duplicates = []

    file_id = 0
    if not args.summary:
        print(f'Reading {jdupes_report_filename}...', file=sys.stderr)
    with open(jdupes_report_filename, 'r', errors='replace') as report_file:
        line = report_file.readline().rstrip('\n')
        while line:
            if "bytes each" not in line and "byte  each" not in line:
                parser.error(f'{jdupes_report_filename} does not seem to be an fdupes/jdupes report file')
            file_id += 1
            file_size = int(line.split()[0])

            while True:
                line = report_file.readline().rstrip('\n')
                if not line:
                    break
                dir, file_name = os.path.split(line)
                duplicates.append({
                    'id': file_id,
                    'dir': dir,
                    'name': file_name,
                    'size': file_size
                })

            line = report_file.readline().rstrip('\n')

    if args.summary:
        # duplicate sets: distinct ids/files
        # duplicate copies: sum(n-1)
        # wasted space: sum((n-1)*size)
        count_by_id = defaultdict(int)
        size_by_id = {}
        for fi in duplicates:
            fid = fi['id']
            count_by_id[fid] += 1
            if fid not in size_by_id:
                size_by_id[fid] = fi['size']

        num_sets = len(count_by_id)
        dup_copies = 0
        wasted = 0
        for fid, n in count_by_id.items():
            if n > 1:
                dup_copies += (n - 1)
                wasted += (n - 1) * int(size_by_id.get(fid, 0))

        print(f"Duplicate sets: {num_sets}")
        print(f"Duplicate copies: {dup_copies}")
        print(f"Wasted space: {pretty_print_bytes(wasted)}")
        # it's a bit ugly, but... minimal intrusion :)
        return

    print('Building directory list...', file=sys.stderr)
    dirs = defaultdict(dict)
    for file_info in duplicates:
        file_id = file_info['id']
        directory = file_info['dir']
        file_size = file_info['size']
        if directory not in dirs[file_id]:
            dirs[file_id][directory] = file_size


    print('Calculating directory pairs...', file=sys.stderr)
    directory_pairs = defaultdict(int)
    for file, dir in dirs.items():
        sorted_dirs = sorted(dir.items())
        for (d1, s1), (d2, s2) in itertools.combinations(sorted_dirs, 2):
            shared_size = s1
            if s1 != s2:
                print(f'For file {file} size discrepancies: {s1} / {s2} for dirs "{d1}" and "{d2}"')
            sorted_pair = tuple(sorted((d1, d2)))
            directory_pairs[sorted_pair] += shared_size

    print('Sorting directory pairs...', file=sys.stderr)
    sorted_directory_pairs = sorted(directory_pairs.items(), key=lambda x: -x[1])

    for pair in sorted_directory_pairs:
        print(f'Size: {pretty_print_bytes(pair[1])},  meld "{pair[0][0]}" "{pair[0][1]}"')

if __name__ == "__main__":
    main()
