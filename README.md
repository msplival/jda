# jda

jdupes Report Analyzer

## What is jda?

jda is a tool designed to help you analyze fdupes/jdupes report files.

jdupes (and its slower variant, fdupes) produces a report showing which files on your disk are identical.

jda analyzes that report and provides a list of directories containing those identical files, sorted by the size of those identical files.

## How to Use

Run jdupes against the directories you're interested in, like this:

```console
$ jdupes -rS /srv/storage/ > /tmp/jdupes.report.txt
```

The `-S` `(--size)` option is important as it groups identical files by size, which is the output format that jda can parse.

Then, run jda:

```console
$ jda /tmp/jdupes.report.txt
```

jda will print out the directories with the largest size of identical files. It will prepend `meld` before the directories as meld is a preferred tool. You can use meld to investigate the contents of these directories.

You can also supply `--summary` option to jda. Instead of printing full report it will print summary instead:

```console
./jda.py --summary testData/jdupes.test_report.txt 
Duplicate sets: 11
Duplicate copies: 12
Wasted space: 352.0 MB
```

## Inspiration

jda is inspired by  [FdupesAnalyzer](https://github.com/codecliff/FdupesAnalyzer), which essentially does the same thing.

FdupesAnalyzer dives into each directory and produces a CSV file showing the number of files in each directory, the number of identical files, the percentages, and more. jda does not include this functionality, at least for now, as I don't need it :) 
