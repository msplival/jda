# jda

jdupes report analyzer

## What is?

jda will help ju analyse fdupes/jdupes report file. 

jdupes (and it's much slower 'variant', fdupes) will produce a report showing you which files on your disk are identical. 

jda analyzes that report and gives you list of directories containing those identical files, sorted by the size those identical files take. 

## How to use

Run jdupes against directories you're intested in like this:

```console
$ jupes -rS /srv/storage/ > /tmp/jdupes.report.txt
```

The `-S` (`--size`) is important as it will group identical files by size, and it's the output format that jda can parse. 

Run jda:

```console
$ jda /tmp/jdupes.report.txt
```

jda will print out the directories with the most (size-wise) identical files. It will 'prepend' `meld` before the directories as I love meld. You can use meld to investigate the contents of the directories.

## Inspiration

jda is inspired by [FdupesAnalyzer](https://github.com/codecliff/FdupesAnalyzer), which, basically, does the same thing. 

FdupesAnalyzer will 'dive' into each directory and produce an output (as an CSV file) showing you the number of files in each directory, the number of identical files, the percentages, and so on. 
jda will not do that mainly because I don't need that functionality :) 

