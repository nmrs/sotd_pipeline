# sotd/utils/text.py

import html
import re
import unicodedata


def preprocess_body(body: str) -> str:
    body = re.sub(r"[\u200B\u200C\u200D\u2060\uFEFF]", "", body)
    body = unicodedata.normalize("NFKC", body)
    body = unicodedata.normalize("NFC", body)
    body = html.unescape(body)
    body = body.replace("’", "'").replace("‘", "'")
    body = body.replace("“", '"').replace("”", '"')
    body = body.replace("–", "-").replace("—", "-")
    body = re.sub(r"\\([*_`\\])", r"\1", body)  # remove escapes from *, _, `, \

    # Normalize whitespace per line (preserve newlines)
    lines = body.splitlines()
    lines = [re.sub(r"\s+", " ", line).strip() for line in lines]
    return "\n".join(lines)
