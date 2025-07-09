import re
from pathlib import Path

yaml_files = list(Path("data").glob("*.yaml"))


def decode_file(path):
    bak = path.with_suffix(path.suffix + ".bak")
    bak.write_bytes(path.read_bytes())
    text = path.read_text(encoding="utf-8")
    unicode_escape_re = re.compile(r"(\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2})")
    replacements = [0]

    def decode_escapes_in_line(line):
        def repl(match):
            esc = match.group(0)
            try:
                decoded = esc.encode("utf-8").decode("unicode_escape")
                replacements[0] += 1
                return decoded
            except Exception:
                return esc

        return unicode_escape_re.sub(repl, line)

    new_lines = [decode_escapes_in_line(line) for line in text.splitlines()]
    path.write_text("\n".join(new_lines), encoding="utf-8")
    print(f"{path}: {replacements[0]} unicode escape(s) replaced. Backup: {bak}")


for f in yaml_files:
    decode_file(f)
