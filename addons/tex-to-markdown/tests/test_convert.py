import importlib.util
from pathlib import Path
import unittest
import subprocess
import sys
import tempfile

spec = importlib.util.spec_from_file_location('convert', Path(__file__).parents[1] / 'scripts/convert.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConversionTests(unittest.TestCase):
    def test_heading_and_reference(self):
        result = module.Converter().body(r'\section{Title}\label{s}See \ref{s}.')
        self.assertIn('# Title {#s}', result)
        self.assertIn('See <#s>.', result)

    def test_math_is_not_rewritten(self):
        s = r'$x_{a+b}=\lambda z.z$'
        self.assertEqual(module.Converter().body(s), s)

    def test_unicode_only_commands(self):
        self.assertEqual(module.Converter(True).body(r'$\Delta=\square$'), '$Δ=□$')

    def test_literal_listing(self):
        s = '\\begin{minted}{tex}\n\\section{Literal}\n```\n\\end{minted}'
        out = module.Converter().body(s)
        self.assertIn('````tex', out)
        self.assertIn('\\section{Literal}', out)

    def test_theorem_optional_title_and_label(self):
        s = r'\begin{theorem}[A \cite{x}]\label{t}Text.\end{theorem}'
        out = module.Converter().body(s)
        self.assertIn(r':::Theorem[A \cite{x}] {#t}', out)

    def test_nested_lists(self):
        s = r'\begin{itemize}\item One\begin{itemize}\item Nested\end{itemize}\item Two\end{itemize}'
        out = module.Converter().body(s)
        self.assertIn('  - Nested', out)
        self.assertIn('- Two', out)

    def test_citations_and_footnote(self):
        out = module.Converter().body(r'\cite{x,y}\footnote{A \emph{note}.}')
        self.assertEqual(out, '[@x; @y]^[A *note*.]')

    def test_macro_arguments_remain_literal(self):
        s = r'\badge{https://example.org/a_b#L2}'
        self.assertEqual(module.Converter().body(s), '%' + s[1:])

    def test_unknown_environment_reported(self):
        c = module.Converter()
        self.assertIn('%begin{custom}', c.body(r'\begin{custom}raw\end{custom}'))
        self.assertTrue(c.warnings)

    def test_malformed_input_fails(self):
        with self.assertRaises(ValueError):
            module.Converter().body(r'\emph{unfinished')

    def test_equation_label_not_stolen_by_theorem(self):
        s = r'\begin{theorem}Text $x=0\label{eq}$.\end{theorem}'
        out = module.Converter().body(s)
        self.assertNotIn('{#eq}', out)
        self.assertIn(r'\label{eq}', out)

    def test_cli_refuses_overwrite_and_strict_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'in.tex'
            output = Path(folder)/'out.tex'
            source.write_text(r'\section{One}')
            command = [sys.executable, str(Path(module.__file__)), str(source), '--output', str(output)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            saved = output.read_bytes()
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(output.read_bytes(), saved)
            source.write_text(r'\begin{custom}x\end{custom}')
            command[command.index(str(output))] = str(Path(folder)/'strict.tex')
            self.assertNotEqual(subprocess.run(command+['--strict'], capture_output=True).returncode, 0)
            self.assertFalse((Path(folder)/'strict.tex').exists())


if __name__ == '__main__':
    unittest.main()
