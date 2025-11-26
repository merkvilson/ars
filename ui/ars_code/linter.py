import ast
import re
from pyflakes import checker, messages

class UnusedLinter:
    def __init__(self):
        pass

    def get_unused_ranges(self, code):
        """
        Analyze code using pyflakes and return list of (line_idx, start_col, length)
        for unused variables and imports.
        """
        ranges = set()
        lines = code.split('\n')

        # 1. Run on original code
        self._run_checker(code, lines, ranges, is_wrapped=False)

        # 2. Run on wrapped code (to detect unused globals)
        try:
            indented_code = "\n".join("    " + line for line in lines)
            wrapped_code = f"def __wrapper__():\n{indented_code}"
            self._run_checker(wrapped_code, lines, ranges, is_wrapped=True)
        except Exception:
            pass

        return list(ranges)

    def _run_checker(self, code, original_lines, ranges, is_wrapped):
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return
        except Exception:
            return

        w = checker.Checker(tree, filename="<string>")
        
        for message in w.messages:
            # Adjust line number
            if is_wrapped:
                # Wrapped code starts at line 2 (1-based)
                # So line_idx = message.lineno - 2
                line_idx = message.lineno - 2
            else:
                line_idx = message.lineno - 1

            if line_idx < 0 or line_idx >= len(original_lines):
                continue
            
            line_text = original_lines[line_idx]
            
            if isinstance(message, messages.UnusedImport):
                name = message.message_args[0]
                try:
                    escaped_name = re.escape(name)
                    for match in re.finditer(r'\b' + escaped_name + r'\b', line_text):
                        ranges.add((line_idx, match.start(), len(name)))
                except Exception:
                    pass
                    
            elif isinstance(message, messages.UnusedVariable):
                name = message.message_args[0]
                col = message.col
                
                if is_wrapped:
                    # Adjust column (remove 4 spaces indent)
                    col -= 4
                
                if col >= 0:
                    ranges.add((line_idx, col, len(name)))
