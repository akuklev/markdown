# AGENTS.md

## Project Overview

This repository contains the Markdown package for TeX. The package converts
CommonMark markup to TeX commands and provides Lua, plain TeX, LaTeX, and
ConTeXt interfaces.

The main maintained source is `markdown.dtx`. Generated installable files such
as `markdown.lua`, `markdown-parser.lua`, `markdown.tex`, `markdown.sty`,
`t-markdown.tex`, theme files, man pages, and generated manual files are
extracted from `markdown.dtx` by running the installer/build targets. Prefer
editing `markdown.dtx`, tests, templates, and documentation sources rather than
editing generated outputs directly.

## Important Paths

- `markdown.dtx`: primary documented source and technical documentation input.
- `markdown.ins` and `docstrip.cfg`: docstrip installer configuration.
- `Makefile`: root build, packaging, documentation, cleanup, and check targets.
- `tests/testfiles/`: `.test` fixtures for parser and package behavior.
- `tests/templates/`: m4 templates used to generate TeX test documents.
- `tests/support/`: TeX support files copied into temporary test directories.
- `tests/test.py`: Python test runner.
- `tests/test.sh`: wrapper that creates/uses `tests/test-virtualenv`.
- `examples/`: example TeX documents and example data.

## Build Commands

Use GNU make from the repository root unless noted otherwise.

- `make base`: extract package sources and generated assets from
  `markdown.dtx`.
- `make`: build documentation, examples, and extracted package files, then
  clean auxiliary files.
- `make clean`: remove auxiliary build files.
- `make implode`: remove generated makeable files and distribution archives.
- `make dist`: build distribution archives and run CTAN/package checks when
  documentation is enabled.
- `make preview`: continuously typeset `markdown.dtx` with `latexmk -pvc`.

Many build targets require a full TeX installation, LuaTeX, LaTeXMK, m4, GNU
coreutils-style tools, and other TeX tooling. The Dockerfile and GitHub Actions
workflow are useful references for the CI environment.

See `SKILLS.md` for practical local build/debug recipes, including partial
workflows for macOS/BSD userlands where the Makefile's GNU-tool assumptions do
not all hold.

## Local Build Notes

- Use the local GNU toolchain and a valid UTF-8 locale for TeX commands:

  ``` sh
  export PATH="/usr/local/bin:/usr/local/opt/gnu-sed/libexec/gnubin:/usr/local/opt/grep/libexec/gnubin:/usr/local/opt/gawk/libexec/gnubin:/usr/local/opt/coreutils/libexec/gnubin:$PATH"
  export LC_ALL=en_US.UTF-8
  export LANG=en_US.UTF-8
  ```

  On this macOS host, `C.UTF-8` is not installed and causes LuaTeX to exit
  before processing files.
- `make base` now succeeds with the GNU PATH above. It extracts files, then
  runs `make clean`, so direct targets are better when you need generated
  documentation inputs to remain present:

  ``` sh
  make DEPENDS-raw.txt markdown-figure-block-diagram.tex markdown.bib \
    markdownthemewitiko_markdown_techdoc.sty markdown.md \
    markdown-interfaces.md markdown-options.md markdown-tokens.md VERSION
  ```

- The Unicode data files `UnicodeData.txt`, `CaseFolding.txt`,
  `DerivedNormalizationProps.txt`, and `HangulSyllableType.txt` are generated
  build inputs downloaded from `https://www.unicode.org/Public/17.0.0/ucd/`.
  If `wget` fails TLS negotiation, `curl -fL -o <file> <url>` works.
- Do not test the generated LaTeX wrapper from a flat checkout path alone.
  `markdown.sty` inputs `markdown/markdown`, so a flat `TEXINPUTS` can mix the
  local `markdown.sty` with an installed system `markdown.tex`. Use a temporary
  TDS-style tree or another path layout that provides `markdown/markdown.tex`.
- Installed local tools include `context`, `pandoc`, `pkgcheck`, `chronic`,
  `sponge`, `luacheck`, `flake8`, `pytype`, `rename`, and `md5sum`.
  `pytype` must resolve to the Python 3.11-compatible install; pytype does not
  support Python 3.13.
- The current full `make` blocker is ConTeXt MKIV example generation. After
  adding the ConTeXt standalone resolver dependencies described in
  `SKILLS.md`, `examples/context-mkiv.pdf` loads the local package but fails
  while parsing YAML/Jekyll data:

  ``` text
  Package markdown Error: Parser `parse_blocks` failed to process the input text.
  ```

  The first full-suite `make test` failure is similarly ConTeXt-specific:
  `tests/testfiles/regression/github/issue-218.test` renders the YAML block as
  normal markdown instead of `jekyllData`.
- The technical documentation build emitted `command not found` warnings for
  optional diagram/rendering tools `dot`, `inkscape`, `mmdc`, and `plantuml`.
  These warnings were not the final build blocker observed in this run.

## Test Commands

- Full test suite from the root: `make test`.
- Full test suite from `tests/`: `make`.
- One or more specific fixtures from `tests/`:
  `./test.sh testfiles/unit/lunamark-markdown/fenced-code.test`.
- Update expected outputs from `tests/`: `./test.sh --update-tests <testfile>`.
- Continue after failures from `tests/`: `./test.sh --no-fail-fast <testfile>`.
- Via Makefile: `make UPDATE_TESTS=true test` or
  `make FAIL_FAST=false test`.

The test runner expects test file paths relative to the `tests/` directory when
run through `tests/test.sh`. It creates `tests/test-virtualenv` on first use and
installs `tests/requirements.txt`.

If `chronic` is unavailable, create the venv manually:

``` sh
python3 -m venv tests/test-virtualenv
tests/test-virtualenv/bin/pip install -U pip wheel setuptools
tests/test-virtualenv/bin/pip install -r tests/requirements.txt
```

## Checks

- `make check-tabs-and-spaces`: reject tabs and trailing spaces in
  `markdown.dtx`.
- `make check-line-length`: extract generated files, then reject source lines
  longer than 72 characters, excluding `markdown-unicode-data.lua`.
- `luacheck *.lua`: CI runs this after extraction.
- `explcheck *.tex *.sty tests/support/*.tex tests/support/*.sty`: CI runs this
  after extraction.
- `flake8 tests/test.py`: Python style check; `setup.cfg` sets
  `max-line-length = 140`.
- `pytype tests/test.py`: Python type check after installing
  `tests/requirements.txt`.
- Markdown linting uses `.markdownlint.yaml`.

Verified on this host with the GNU PATH and locale above:

- `make NO_DOCUMENTATION=true`
- `make check-tabs-and-spaces`
- `make check-line-length`
- `luacheck *.lua`
- `explcheck *.tex *.sty tests/support/*.tex tests/support/*.sty`
- `flake8 tests/test.py`
- `pytype tests/test.py`

Known failing targets from the same verification run:

- `make`: fails at `examples/context-mkiv.pdf`.
- `make test`: fails first at
  `tests/testfiles/regression/github/issue-218.test`.

Run the narrowest relevant test or check before finishing a change. For changes
to parser behavior, add or update `.test` fixtures and run those fixtures first.
Run `make test` when the change affects shared parsing, templates, or TeX
interfaces.

## Fixture Format Notes

Test files contain optional YAML metadata, setup TeX, Markdown input, and
expected output separated by marker lines:

- `---` after metadata.
- `<<<` before Markdown input.
- `>>>` before expected output.

Metadata can restrict a fixture to formats/templates with an `if` expression.
When updating expected outputs, prefer the runner's `--update-tests` option so
the fixture is rewritten consistently.

## Editing Guidance

- Keep generated files out of hand edits unless the task is explicitly about
  generated release artifacts.
- Keep source lines short enough for the repository checks where practical.
- Avoid changing large generated Unicode data or distribution archives unless
  the build target is intentionally regenerating them.
- Preserve existing test fixture structure and template conventions.
- Do not remove unrelated generated files or local virtual environments unless
  asked.
