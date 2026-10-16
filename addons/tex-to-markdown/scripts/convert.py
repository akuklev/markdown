#!/usr/bin/env python3
"""Conservative LaTeX-body to native Markdown–TeX bootstrap (Python 3)."""
import argparse
import json
from pathlib import Path
import re
import textwrap


SYMBOLS = dict(Gamma='Γ', Delta='Δ', Pi='Π', lambda_='λ', beta='β',
               forall='∀', exists='∃', to='→', Rightarrow='⇒', vdash='⊢',
               Leftrightarrow='⇔', Longleftrightarrow='⟺', square='□',
               leadsto='↝', rrparenthesis='⦈', llparenthesis='⦇')
SYMBOLS['lambda'] = SYMBOLS.pop('lambda_')
ENVIRONMENTS = {'theorem', 'lemma', 'proposition', 'corollary', 'definition',
                'remark', 'proof', 'abstract'}
RAW_MATH = {'mathpar', 'align', 'align*', 'gather', 'gather*', 'multline',
            'multline*', 'equation', 'equation*', 'tikzcd', 'bnf'}


def argument(s, pos, opening='{', closing='}'):
    while pos < len(s) and s[pos].isspace():
        pos += 1
    if pos >= len(s) or s[pos] != opening:
        raise ValueError('Expected ' + opening + ' at offset ' + str(pos))
    start, depth = pos + 1, 1
    pos += 1
    while pos < len(s):
        if s[pos] == '\\':
            token = re.match(r'\\(?:[A-Za-z]+|.)', s[pos:])
            pos += len(token[0])
            continue
        if s[pos] == opening:
            depth += 1
        elif s[pos] == closing:
            depth -= 1
            if not depth:
                return s[start:pos], pos + 1
        pos += 1
    raise ValueError('Unclosed argument at offset ' + str(start - 1))


class Converter:
    def __init__(self, unicode=False):
        self.unicode = unicode
        self.warnings = []

    def math(self, s):
        if not self.unicode:
            return s
        return re.sub(r'\\([A-Za-z]+)([ \t]*)',
                      lambda m: SYMBOLS.get(m[1], '\\' + m[1])
                      + ('' if m[1] in SYMBOLS else m[2]), s)

    def environment(self, name, body, options):
        if name in {'minted', 'verbatim', 'lstlisting'}:
            language = ''
            if name == 'minted':
                language, stop = argument(body, 0)
                body = body[stop:]
            # Choose a fence longer than any literal backtick run.
            fence = '`' * max(3, 1 + max((len(x) for x in
                             re.findall(r'`+', body)), default=0))
            return '\n\n' + fence + language + '\n' + body.strip('\n') + '\n' + fence + '\n\n'
        if name in RAW_MATH:
            if options:
                self.warnings.append('Raw environment options require review: ' + name)
                return '\n\n%' + 'begin{' + name + '}' + options + body + '%end{' + name + '}\n\n'
            return '\n\n%' + name + '\n' + textwrap.indent(self.math(textwrap.dedent(body).strip()), '  ') + '\n\n'
        if name.rstrip('*') in ENVIRONMENTS:
            label = re.match(r'\s*\\label\{([^}]+)\}', body)
            suffix = ' {#' + label[1] + '}' if label else ''
            if label:
                body = body[:label.start()] + body[label.end():]
            title = name[0].upper() + name[1:]
            return '\n\n:::' + title + options + suffix + '\n' + self.body(body).strip() + '\n:::\n\n'
        if name in {'itemize', 'enumerate'}:
            # Split only top-level items, not items of nested environments.
            pieces, last, depth = [], 0, 0
            for m in re.finditer(r'\\(?:begin\{[^}]+\}|end\{[^}]+\}|item\b)', body):
                if m[0].startswith('\\begin'):
                    depth += 1
                elif m[0].startswith('\\end'):
                    depth -= 1
                elif depth == 0:
                    pieces.append(body[last:m.start()]); last = m.end()
            pieces.append(body[last:])
            if pieces[0].strip():
                self.warnings.append('Text before first list item requires review')
            rows = []
            for i, piece in enumerate(pieces[1:], 1):
                marker = '- ' if name == 'itemize' else str(i) + '. '
                value = self.body(piece).strip().splitlines()
                rows.append(marker + value[0] + '\n' + textwrap.indent('\n'.join(value[1:]), ' ' * len(marker)))
            return '\n\n' + '\n\n'.join(rows) + '\n\n'
        if name == 'figure':
            caption = re.search(r'\\caption\b', body)
            label = re.search(r'\\label\{([^}]+)\}', body)
            title = ''
            if caption:
                title, stop = argument(body, caption.end())
                body = body[:caption.start()] + body[stop:]
            if label:
                body = re.sub(r'\\label\{' + re.escape(label[1]) + r'\}', '', body)
            return '\n\n:::Figure' + options + ' ' + self.body(title).strip() + (' {#' + label[1] + '}' if label else '') + '\n' + self.body(body).strip() + '\n:::\n\n'
        self.warnings.append('Preserved unsupported environment: ' + name)
        return '\n\n%begin{' + name + '}' + options + body + '%end{' + name + '}\n\n'

    def body(self, s):
        out, i = [], 0
        while i < len(s):
            if s[i] == '%' and (i == 0 or s[i-1] != '\\'):
                end = s.find('\n', i)
                self.warnings.append('TeX comment preserved as Markdown HTML comment')
                end = len(s) if end < 0 else end
                # Preserve TeX's comment-newline suppression.
                out.append('<!--' + s[i+1:end].replace('--', '—') + '-->')
                i = min(len(s), end + 1); continue
            if s[i] == '$' or s.startswith('\\[', i) or s.startswith('\\(', i):
                opener = '$$' if s.startswith('$$', i) else s[i:i+2] if s[i] == '\\' else '$'
                closer = {'\\[':'\\]', '\\(':'\\)'}.get(opener, opener)
                start = i + len(opener)
                m = re.search(r'(?<!\\)' + re.escape(closer), s[start:])
                if not m:
                    raise ValueError('Unclosed math at offset ' + str(i))
                end = start + m.start()
                value = self.math(s[start:end])
                out.append('\n\n%mathpar\n' + textwrap.indent(value.strip(), '  ') + '\n\n' if opener in {'$$', '\\['} else '$' + value + '$')
                i = end + len(closer); continue
            if s[i] != '\\':
                out.append(s[i]); i += 1; continue
            m = re.match(r'\\([A-Za-z]+\*?|.)', s[i:])
            name = m[1]; i += len(m[0])
            if name == 'begin':
                env, i = argument(s, i)
                options = ''
                if s[i:].lstrip().startswith('['):
                    opt, i = argument(s, i, '[', ']'); options = '[' + opt + ']'
                start, depth = i, 1
                pattern = re.compile(r'\\(begin|end)\{' + re.escape(env) + r'\}')
                for mark in pattern.finditer(s, i):
                    depth += 1 if mark[1] == 'begin' else -1
                    if depth == 0:
                        out.append(self.environment(env, s[start:mark.start()], options))
                        i = mark.end(); break
                else:
                    raise ValueError('Unclosed environment ' + env)
            elif name in {'section', 'subsection', 'subsubsection', 'paragraph', 'section*', 'subsection*', 'subsubsection*'}:
                title, i = argument(s, i)
                level = {'section':1, 'subsection':2, 'subsubsection':3, 'paragraph':4}[name.rstrip('*')]
                label = re.match(r'\s*\\label\{([^}]+)\}', s[i:])
                if label:
                    i += label.end()
                if name.endswith('*'):
                    self.warnings.append('Unnumbered heading requires class-specific review')
                out.append('\n\n' + '#' * level + ' ' + self.body(title) + (' {#' + label[1] + '}' if label else '') + '\n\n')
            elif name in {'emph', 'textit', 'textbf'}:
                value, i = argument(s, i); marker = '**' if name == 'textbf' else '*'
                out.append(marker + self.body(value) + marker)
            elif name in {'ref', 'eqref'}:
                value, i = argument(s, i)
                out.append(('<#' + value + '>') if name == 'ref' else '(<#' + value + '>)')
            elif name == 'cite':
                note = ''
                if s[i:].lstrip().startswith('['):
                    note, i = argument(s, i, '[', ']')
                value, i = argument(s, i)
                keys = [x.strip() for x in value.split(',')]
                if note and len(keys) != 1:
                    self.warnings.append('Multi-key citation with postnote requires review')
                out.append('[' + '; '.join('@' + key for key in keys) + (', ' + note if note else '') + ']')
            elif name == 'footnote':
                value, i = argument(s, i); out.append('^[' + self.body(value).strip() + ']')
            elif name == 'url':
                value, i = argument(s, i); out.append('<' + value + '>')
            elif name == 'href':
                url, i = argument(s, i); title, i = argument(s, i)
                out.append('[' + self.body(title) + '](' + url + ')')
            else:
                # Preserve complete arguments as literal TeX, not Markdown.
                literal = '%' + name
                while i < len(s) and s[i] in '[{':
                    opening = s[i]; closing = ']' if opening == '[' else '}'
                    _, stop = argument(s, i, opening, closing)
                    literal += s[i:stop]; i = stop
                out.append(literal)
        return re.sub(r'\n{3,}', '\n\n', ''.join(out))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--preamble-output', type=Path)
    parser.add_argument('--unicode', action='store_true')
    parser.add_argument('--strict', action='store_true')
    args = parser.parse_args()
    source = args.input.read_text()
    parts = re.split(r'\\begin\{document\}', source, maxsplit=1)
    preamble, body = (parts[0], parts[1]) if len(parts) == 2 else ('', source)
    body = re.sub(r'\\end\{document\}\s*$', '', body)
    converter = Converter(args.unicode)
    result = converter.body(body).strip() + '\n'
    report = args.output.with_suffix(args.output.suffix + '.review.json')
    paths = [args.output, report] + ([args.preamble_output] if args.preamble_output else [])
    if len({p.resolve() for p in paths}) != len(paths) or any(p.exists() for p in paths):
        parser.error('Output/report/preamble paths must be distinct and must not exist')
    if args.strict and converter.warnings:
        parser.error('; '.join(converter.warnings))
    args.output.write_text(result)
    report.write_text(json.dumps({'input': str(args.input), 'warnings': converter.warnings,
                                 'standalone': False}, indent=2) + '\n')
    if args.preamble_output:
        args.preamble_output.write_text(preamble)
    print('Converted body; review ' + str(report))


if __name__ == '__main__':
    main()
