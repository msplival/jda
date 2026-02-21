#!/usr/bin/env python3

import argparse
from collections import defaultdict
import itertools
import os
import sys
import subprocess
import tempfile


def pretty_print_bytes(num_bytes):
    for unit in ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0


def _run_sort(in_path, out_path, sort_args):
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    subprocess.run(["sort", *sort_args, "-o", out_path, in_path], check=True, env=env)


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
    num_sets = 0
    dup_copies = 0
    wasted = 0

    print(f'Reading {jdupes_report_filename}...', file=sys.stderr)

    if args.summary:
        with open(jdupes_report_filename, 'r', errors='replace') as report_file:
            line = report_file.readline().rstrip('\n')
            while line:
                if "bytes each" not in line and "byte each" not in line:
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

                line = report_file.readline().rstrip('\n')

        print(f"Duplicate sets: {num_sets}")
        print(f"Duplicate copies: {dup_copies}")
        print(f"Wasted space: {pretty_print_bytes(wasted)}")
        return

    # External sort path: write (dir1, dir2, size) records to disk.
    with tempfile.TemporaryDirectory(dir="/var/tmp") as tmpdir:
        pairs_path = os.path.join(tmpdir, "pairs.tsv")
        sorted_pairs_path = os.path.join(tmpdir, "pairs.sorted.tsv")
        agg_path = os.path.join(tmpdir, "pairs.agg.tsv")
        final_path = os.path.join(tmpdir, "pairs.final.tsv")

        pairs_fh = open(pairs_path, "w", encoding="utf-8", buffering=1024 * 1024)

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

                sorted_dirs = sorted(current_dirs.items())
                for (d1, s1), (d2, s2) in itertools.combinations(sorted_dirs, 2):
                    shared_size = s1
                    if s1 != s2:
                        print(f'Warning: Unexpected discrepancy in file sizes between {d1[0]}/ and {d2[0]}/', file=sys.stderr)
                    sorted_pair = tuple(sorted((d1, d2)))
                    pairs_fh.write(f"{sorted_pair[0]}\t{sorted_pair[1]}\t{shared_size}\n")

                line = report_file.readline().rstrip('\n')

        pairs_fh.close()

        print('Sorting directory pairs...', file=sys.stderr)

        if os.path.getsize(pairs_path) == 0:
            return

        # 1) sort by (dir1, dir2)
        _run_sort(pairs_path, sorted_pairs_path, ["-t", "\t", "-k1,1", "-k2,2"])

        # 2) streaming reduce -> agg_path: (dir1, dir2, total_size)
        with open(sorted_pairs_path, "r", encoding="utf-8") as inp, open(
            agg_path, "w", encoding="utf-8", buffering=1024 * 1024
        ) as out:
            last_d1 = None
            last_d2 = None
            acc = 0

            for row in inp:
                row = row.rstrip("\n")
                if not row:
                    continue
                d1, d2, sz = row.split("\t", 2)
                sz = int(sz)

                if last_d1 is None:
                    last_d1 = d1
                    last_d2 = d2
                    acc = sz
                    continue

                if d1 == last_d1 and d2 == last_d2:
                    acc += sz
                else:
                    out.write(f"{last_d1}\t{last_d2}\t{acc}\n")
                    last_d1 = d1
                    last_d2 = d2
                    acc = sz

            if last_d1 is not None:
                out.write(f"{last_d1}\t{last_d2}\t{acc}\n")

        # 3) sort by total size descending
        _run_sort(agg_path, final_path, ["-t", "\t", "-k3,3nr"])

        # 4) print exactly like before
        with open(final_path, "r", encoding="utf-8") as f:
            for row in f:
                row = row.rstrip("\n")
                if not row:
                    continue
                d1, d2, total = row.split("\t", 2)
                print(f'Size: {pretty_print_bytes(int(total))},  meld "{d1}" "{d2}"')


if __name__ == "__main__":
    main()
