# MSU SSC tools

Various Python tools for the Morehead State University (MSU) Space Science Center (SSC). This repo is owned by [David Mayo](https://github.com/davidmayo).

## Usage

Tools are written and tested in Linux (Ubuntu) with Python 3.10. More details on all this forthcoming.

In particular, this uses the `src` layout, with all the code being in `./src/msu_ssc`, so `./src` will need to be added to $PYTHONPATH to use this at all.

## Provenance

These tools are largely written by [David Mayo](https://github.com/davidmayo), starting in January 2025.

Some of this code dates back many years ago, written by many different Space Science Center personnel over the years, with no git history to speak of.


## Release notes

### 0.1.0 - 2025-02-05
Initial release

### 0.1.1 - 2025-02-05
Add ssc_logging module

### 0.2.0 - 2025-02-05
Overhaul to ssc_log module (Many breaking changes)

### 0.2.1 - 2025-02-05
Fix bug in optional dependency spec for "logging"

### 0.2.2 - 2025-02-05
Remove extraneous log messages

### 0.3.0 - 2025-02-06
Allow compatibility with Python 3.7 through Python 3.13 

### 0.4.0 - 2025-02-11
Add `prompt_util` module

### 0.5.0 - 2025-03-27
Prep for PyPI release

### 0.6.0 - 2025-03-27
Use GitHub action to publish to TestPyPI

### 1.0.0 - 2025-03-27
First official release!

### 2.0.0 - 2026-01-29
Replace log console timestamp with more concise version

### 2.0.1 - 2026-01-29
Add release notes that were mistakenly not included