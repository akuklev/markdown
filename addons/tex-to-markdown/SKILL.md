---
name: tex-to-markdown
description: Convert LaTeX articles to this fork's native Markdown–TeX dialect while preserving mathematics, references and authorial content.
---

Use `scripts/convert.py INPUT.tex --output OUTPUT.tex` for a conservative
body conversion. It emits a review report beside the output and refuses to
overwrite files. The script is a bootstrap, not a general TeX interpreter.
Read the report before treating output as finished.

Preserve the author's actual editorial version, including deleted caveats
and references. Do not infer permission to restore material from history.
Do not rewrite mathematical conventions to match formal code silently.

The output uses native headings/labels, fenced environments, citations,
references, offside math blocks and `%macro` prose calls. Unknown environments
remain literal TeX with review warnings; unknown macro arguments are preserved.
Use `--strict` when unsupported constructs must stop conversion instead.
Use `--unicode` only with matching Unicode declarations in the preamble.
`--preamble-output FILE` also extracts the original preamble without changing
it; adapt its class/title/author setup manually for the target metadata class.
Without that adaptation, the script's output is a body fragment, not a
standalone document. No external files, packages or metadata are invented.

For a full article, retain the project's preamble, bibliography and assets;
introduce YAML metadata and the local `markdown` class separately. Keep custom
theorem names/counters and optional titles intact. In optional theorem titles,
retain TeX spelling for citations and badges. For diagrams, prefer standalone
offside `%tikzcd`; use `%align*`, not a nested `aligned` display. The fork's
parser requires care with list-nested raw displays: retain explicit math
delimiters if an offside block would swallow following list prose.

Keep URLs, macro arguments, math, labels, citations and literal listings
indivisible when wrapping prose. Keep a badge on its prose line. Do not pad
the inside edges of fenced blocks. Unicode and notation aliases must preserve
the original glyphs and formulas; keep scripts attached to their operators.

Verify both sources, not just rendered prose: compare ordered mathematics,
labels/citation targets, code listings, and unknown/raw-TeX review entries.
Compile in a fresh directory with the project's actual bibliography tool;
check missing glyphs and unresolved references and visually inspect title,
floats, footnotes and representative formulas. A successful conversion script
or build is not proof of content equivalence. Do not publish without a request.

Run add-on regression tests with:

```
python3 -m unittest discover -s addons/tex-to-markdown/tests
```
