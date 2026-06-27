# Building and Debugging the Markdown Package

This file records practical local workflows for building, trying, and
debugging this package. It complements `AGENTS.md` with concrete commands and
host-specific findings.

## Environment Baseline

Use GNU userland tools first in PATH and a valid UTF-8 locale:

``` sh
export PATH="/usr/local/bin:/usr/local/opt/gnu-sed/libexec/gnubin:/usr/local/opt/grep/libexec/gnubin:/usr/local/opt/gawk/libexec/gnubin:/usr/local/opt/coreutils/libexec/gnubin:$PATH"
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

On this host, `C.UTF-8` is not installed and LuaTeX exits with a locale error.
The default macOS `sed`, `grep`, and `awk` are not enough for the Makefile's
GNU assumptions.

Installed verification tools include `context`, `pandoc`, `pkgcheck`,
`chronic`, `sponge`, `luacheck`, `explcheck`, `flake8`, `pytype`, `rename`,
and `md5sum`. `pytype` must run from the Python 3.11-compatible install.

## Intended Build Path

The normal extraction target is:

``` sh
make base
```

This target downloads Unicode data if needed, runs `luatex markdown.ins`, adds
CLI shebangs, generates `markdown-unicode-data.lua`, replaces version
placeholders, and cleans auxiliaries. It succeeds with the baseline PATH above,
but it removes generated documentation inputs at the end through `make clean`.

When those generated inputs need to remain present, build them directly:

``` sh
make DEPENDS-raw.txt markdown-figure-block-diagram.tex markdown.bib \
  markdownthemewitiko_markdown_techdoc.sty markdown.md \
  markdown-interfaces.md markdown-options.md markdown-tokens.md VERSION
```

The full build is:

``` sh
make
```

That additionally builds documentation and examples, then cleans auxiliary
files. In the latest local run, the technical manual reached PDF output, then
the full build failed at `examples/context-mkiv.pdf`; see "Current Full-Build
Blocker" below.

## Unicode Data Inputs

`make base` needs these Unicode Character Database files:

``` text
UnicodeData.txt
CaseFolding.txt
DerivedNormalizationProps.txt
HangulSyllableType.txt
```

They come from:

``` text
https://www.unicode.org/Public/17.0.0/ucd/
```

If `wget` fails, fetch them with `curl`:

``` sh
curl -fL -o UnicodeData.txt \
  https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt
curl -fL -o CaseFolding.txt \
  https://www.unicode.org/Public/17.0.0/ucd/CaseFolding.txt
curl -fL -o DerivedNormalizationProps.txt \
  https://www.unicode.org/Public/17.0.0/ucd/DerivedNormalizationProps.txt
curl -fL -o HangulSyllableType.txt \
  https://www.unicode.org/Public/17.0.0/ucd/HangulSyllableType.txt
```

## ConTeXt Standalone Setup

The installed ConTeXt LMTX tree is under `/Users/akuklev/context-lmtx`. Direct
`/usr/local/bin/context` and `/usr/local/bin/mtxrun` symlinks are unreliable
here. For build verification, use wrappers that run the bundled runner through
the bundled `luatex`:

``` sh
mkdir -p /tmp/markdown-context-bin

cat > /tmp/markdown-context-bin/context <<'EOF'
#!/bin/sh
export TEXMFCNF=/Users/akuklev/context-lmtx/tex/texmf/web2c
export LC_ALL=${LC_ALL:-en_US.UTF-8}
export LANG=${LANG:-en_US.UTF-8}
export LUA_PATH="/usr/local/texlive/2026/texmf-dist/tex/luatex/lua-uni-algos/?.lua;${LUA_PATH}"
exec /Users/akuklev/context-lmtx/tex/texmf-osx-arm64/bin/luatex \
  --luaonly /Users/akuklev/context-lmtx/tex/texmf-osx-arm64/bin/mtxrun.lua \
  --script context "$@"
EOF

cat > /tmp/markdown-context-bin/mtxrun <<'EOF'
#!/bin/sh
export TEXMFCNF=/Users/akuklev/context-lmtx/tex/texmf/web2c
export LC_ALL=${LC_ALL:-en_US.UTF-8}
export LANG=${LANG:-en_US.UTF-8}
exec /Users/akuklev/context-lmtx/tex/texmf-osx-arm64/bin/luatex \
  --luaonly /Users/akuklev/context-lmtx/tex/texmf-osx-arm64/bin/mtxrun.lua "$@"
EOF

chmod +x /tmp/markdown-context-bin/context /tmp/markdown-context-bin/mtxrun
export PATH="/tmp/markdown-context-bin:$PATH"
```

The ConTeXt standalone tree also needed local resolver entries for LaTeX3,
Unicode data, and generated package files:

``` sh
mkdir -p /Users/akuklev/context-lmtx/tex/texmf-local/tex/generic
mkdir -p /Users/akuklev/context-lmtx/tex/texmf-local/tex/generic/unicode-data
mkdir -p /Users/akuklev/context-lmtx/tex/texmf-local/tex/luatex/markdown
mkdir -p /Users/akuklev/context-lmtx/tex/texmf-local/tex/context/third/markdown
```

Symlink these inputs into that tree:

``` sh
ln -sfn /usr/local/texlive/2026/texmf-dist/tex/latex/l3kernel \
  /Users/akuklev/context-lmtx/tex/texmf-local/tex/generic/l3kernel
ln -sfn /usr/local/texlive/2026/texmf-dist/tex/latex/l3backend \
  /Users/akuklev/context-lmtx/tex/texmf-local/tex/generic/l3backend
ln -sfn /usr/local/texlive/2026/texmf-dist/tex/generic/lt3luabridge \
  /Users/akuklev/context-lmtx/tex/texmf-local/tex/generic/lt3luabridge
```

For Unicode data, link the TeX Live files `UnicodeData.txt`,
`CaseFolding.txt`, `GraphemeBreakProperty.txt`, `WordBreakProperty.txt`,
`emoji-data.txt`, and `SpecialCasing.txt`, plus the repo-generated
`DerivedNormalizationProps.txt` and `HangulSyllableType.txt`.

For the generated markdown package, link:

``` text
markdown.tex
markdownthemewitiko_markdown_defaults.tex
markdown.lua
markdown-parser.lua
markdown-unicode-data.lua
t-markdown.tex
t-markdownthemewitiko_markdown_defaults.tex
```

Refresh both ConTeXt resolver caches after changing symlinks:

``` sh
/Users/akuklev/context-lmtx/tex/texmf-osx-arm64/bin/luatex \
  --luaonly /Users/akuklev/context-lmtx/tex/texmf-osx-arm64/bin/mtxrun.lua \
  --generate
/Users/akuklev/context-lmtx/tex/texmf-osx-arm64/bin/mtxrun --generate
```

## Current Full-Build Blocker

With the setup above, `make -C examples context-mkiv.pdf` loads the local
ConTeXt module and generated generic package, then fails while parsing the YAML
block in `examples/context-mkiv.tex`:

``` text
Package markdown Error: Parser `parse_blocks` failed to process the input text.
Here are the first 20 characters of the remaining unprocessed text: `
title:  An Example `.
```

The full test suite fails first at
`tests/testfiles/regression/github/issue-218.test`. The expected output is
`jekyllData`, but the ConTeXt MKIV actual output treats the YAML as a thematic
break and heading.

This is the current blocker for:

``` sh
make
make test
```

During the technical documentation build, `latexmk` also reported missing
optional diagram/rendering tools: `dot`, `inkscape`, `mmdc`, and `plantuml`.
Those warnings were not the final blocker reached in this run.

## Smoke Test the Generated LaTeX Package

Do not compile against a flat checkout path only. `markdown.sty` contains
`\input markdown/markdown`, so TeX may load a local `markdown.sty` and a system
`markdown.tex`, which can produce mismatched renderer errors.

Use a temporary TDS-style tree:

``` sh
tmpdir=$(mktemp -d /tmp/markdown-tds.XXXXXX)
mkdir -p "$tmpdir/texmf/tex/generic/markdown"
mkdir -p "$tmpdir/texmf/tex/latex/markdown"
mkdir -p "$tmpdir/texmf/tex/luatex/markdown"
mkdir -p "$tmpdir/work"

cp markdown.tex markdownthemewitiko_markdown_defaults.tex \
  "$tmpdir/texmf/tex/generic/markdown/"
cp markdown.sty markdownthemewitiko_markdown_defaults.sty \
  "$tmpdir/texmf/tex/latex/markdown/"
cp markdown.lua markdown-parser.lua markdown-unicode-data.lua \
  "$tmpdir/texmf/tex/luatex/markdown/"
```

Create `"$tmpdir/work/smoke.tex"`:

``` tex
\documentclass{article}
\usepackage{markdown}
\markdownSetup{fencedCode,pipeTables,tableCaptions,smartEllipses}
\begin{document}
\begin{markdown}
# Smoke Test

Hello *Markdown* and **TeX**.

- one
- two

| A | B |
|---|---|
| 1 | 2 |

: Table
\end{markdown}
\end{document}
```

Compile it:

``` sh
TEXINPUTS="$tmpdir/texmf/tex/latex//:$tmpdir/texmf/tex/generic//:" \
LUAINPUTS="$tmpdir/texmf/tex/luatex/markdown//:" \
lualatex -interaction=nonstopmode -halt-on-error \
  -output-directory="$tmpdir/work" "$tmpdir/work/smoke.tex"
```

A successful run produces `"$tmpdir/work/smoke.pdf"`.

## Smoke Test the Lua CLI

After extraction, test `markdown2tex.lua` directly:

``` sh
tmpdir=$(mktemp -d /tmp/markdown-cli.XXXXXX)
printf '%s\n' '# CLI Smoke' '' 'Hello *Markdown*.' > "$tmpdir/input.md"

LUAINPUTS="$PWD//:" \
texlua "$PWD/markdown2tex.lua" fencedCode=true -- \
  "$tmpdir/input.md" "$tmpdir/output.tex"

sed -n '1,80p' "$tmpdir/output.tex"
```

Expected output contains renderer calls such as
`\markdownRendererHeadingOne` and `\markdownRendererEmphasis`.

## Focused Test Runner Workflow

The project test harness lives in `tests/test.py`; `tests/test.sh` creates
`tests/test-virtualenv` but expects `chronic`. If `chronic` is missing:

``` sh
python3 -m venv tests/test-virtualenv
tests/test-virtualenv/bin/pip install -U pip wheel setuptools
tests/test-virtualenv/bin/pip install -r tests/requirements.txt
```

Run a normal fixture from inside `tests/`:

``` sh
cd tests
./test.sh testfiles/unit/lunamark-markdown/fenced-code.test
```

The runner has no command-line option to exclude a TeX format. It evaluates
fixture metadata against `format` and `template`. For local LaTeX-only
debugging, use a temporary fixture with metadata:

``` yaml
if: format == 'latex'
---
```

Then append the fixture body and run:

``` sh
cd tests
TEXINPUTS="$tmpdir/texmf/tex/latex//:$tmpdir/texmf/tex/generic//:" \
LUAINPUTS="$tmpdir/texmf/tex/luatex/markdown//:" \
test-virtualenv/bin/python3 test.py /tmp/your-latex-only-fixture.test
```

## Useful Checks

These passed on this host with the baseline PATH and locale:

``` sh
make NO_DOCUMENTATION=true
make check-tabs-and-spaces
make check-line-length
luacheck *.lua
explcheck *.tex *.sty tests/support/*.tex tests/support/*.sty
flake8 tests/test.py
pytype tests/test.py
```

## Debugging Tips

- If a LaTeX smoke test reports undefined renderer prototypes, first check for
  mixed local/system package loading in the log.
- If LuaTeX exits before reading `markdown.ins`, check locale settings.
- If CLI conversion works but LaTeX fails, inspect `TEXINPUTS` and `LUAINPUTS`.
- If ConTeXt cannot find `expl3-generic`, `lt3luabridge`, or Unicode data,
  refresh the relevant `texmf-local` symlinks and rerun both resolver cache
  commands from the ConTeXt setup section.
