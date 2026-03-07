#!/usr/bin/env python3
"""
Generate data/soaps_proposed.yaml with entries for (maker, scent) pairs
found in data/correct_matches/soap.yaml but missing from data/soaps.yaml.
"""

import re
import unicodedata
import yaml

# ---------------------------------------------------------------------------
# Accent substitution map — applied char-by-char to produce literal bracket
# classes stored as real Unicode in the YAML file.
# ---------------------------------------------------------------------------
ACCENT_MAP = {
    'é': '[eé]', 'è': '[eè]', 'ê': '[eê]', 'ë': '[eë]',
    'ü': '[uü]', 'û': '[uû]', 'ù': '[uù]', 'ú': '[uú]',
    'ä': '[aä]', 'â': '[aâ]', 'à': '[aà]', 'á': '[aá]', 'ā': '[aā]',
    'ï': '[iï]', 'î': '[iî]', 'ì': '[iì]', 'í': '[ií]',
    'ö': '[oö]', 'ô': '[oô]', 'ò': '[oò]', 'ó': '[oó]',
    'ñ': '[nñ]', 'ç': '[cç]', 'ø': '[oø]', 'ß': 'ss?',
}

# Regex specials we escape in plain text (outside of bracket classes we generate).
REGEX_SPECIALS = r'\.()+-?*^$[]'

# Words that are so generic that even if the scent name is long, we still
# want a maker guard to avoid false matches.
ALWAYS_GUARD_WORDS = frozenset({
    'tobacco', 'lime', 'rose', 'mint', 'cedar', 'musk', 'pine', 'amber',
    'lemon', 'bergamot', 'citrus', 'vanilla', 'sandalwood', 'lavender',
    'leather', 'smoke', 'wood', 'honey', 'tea', 'coffee', 'spice',
    'havana', 'shake', 'shaken', 'reflection', 'convergence', 'bandwagon',
    'nightman', 'dayman', 'persephone', 'semicolon',
})

# Stop words for guard token filtering — too generic to be useful as guards
GUARD_STOP = frozenset({
    'soap', 'soaps', 'shave', 'shaving', 'the', 'and', 'for', 'grooming',
    'company', 'works', 'factory', 'labs', 'lab', 'craft', 'crafts',
    'artisan', 'products', 'product',
})


def build_scent_pattern(scent_name: str) -> str:
    """
    Turn a scent name into a regex core (no maker guard):
      1. Lowercase
      2. Build char-by-char: accent → bracket class, specials → escaped, rest → literal
      3. Split on whitespace, join tokens with .*
    """
    lowered = scent_name.lower()
    parts = []
    for ch in lowered:
        if ch in ACCENT_MAP:
            parts.append(ACCENT_MAP[ch])
        elif ch in REGEX_SPECIALS:
            parts.append('\\' + ch)
        else:
            parts.append(ch)
    raw = ''.join(parts)
    tokens = raw.split()
    return '.*'.join(tokens) if len(tokens) > 1 else (tokens[0] if tokens else '')


def ascii_lower(s: str) -> str:
    """Strip diacritics and lowercase a string."""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


def extract_guard_tokens(patterns: list[str]) -> list[str]:
    """
    Extract plain-text identifying tokens from maker patterns using targeted
    heuristics for the specific regex constructs used in soaps.yaml:

    1. \\bWORD\\b  → exact word (like \\bdg\\b → 'dg')
    2. Plain literal prefix before any regex special char
    3. Skip tokens shorter than 3 chars or in GUARD_STOP
    4. Skip patterns that are effectively just anchors/wildcards

    Returns deduplicated list sorted longest-first.
    """
    seen: set[str] = set()
    candidates: list[str] = []

    def add(tok: str) -> None:
        tok = tok.strip().lower()
        if tok and tok not in seen and len(tok) >= 3 and tok not in GUARD_STOP:
            seen.add(tok)
            candidates.append(tok)

    for pat in patterns:
        # Strategy 1: extract \\bWORD\\b tokens (YAML-loaded string has literal \b)
        for m in re.finditer(r'\\b([a-zA-Z][a-zA-Z0-9&.+\s]*?)\\b', pat):
            word = m.group(1).strip()
            # Only accept simple word/abbreviation, not a sub-expression
            if re.match(r'^[a-zA-Z][a-zA-Z0-9&+.\s]{0,20}$', word):
                first = word.split()[0]  # take first word only
                add(first)

        # Strategy 2: find the leading literal run (before any regex metachar)
        # Strip leading ^ and \\W* anchors
        stripped = re.sub(r'^\^(?:\\W\*)?', '', pat)
        # Match leading alphanumeric literal (allowing spaces, apostrophe, period, dash)
        m2 = re.match(r'^([a-zA-Z][a-zA-Z0-9\s._\'-]*?)(?=[(\[?+*{\\|]|$)', stripped)
        if m2:
            literal = m2.group(1).strip(" .'-_")
            words = literal.split()
            for w in words:
                w_clean = w.strip(" .'-_")
                if w_clean.isalpha() and len(w_clean) >= 3 and w_clean.lower() not in GUARD_STOP:
                    add(w_clean)
                    break  # only first word per pattern

    # Sort: longer first (more distinctive), then alphabetical
    candidates.sort(key=lambda x: (-len(x), x))
    return candidates


def maker_name_tokens(maker: str) -> list[str]:
    """
    Derive tokens from the maker name itself (used as fallback).
    Strips diacritics, splits on non-alpha, keeps words >= 3 chars not in stop list.
    Returns lowercased tokens, longest first.
    """
    ascii_name = ascii_lower(maker)
    words = re.split(r'[^a-z]+', ascii_name)
    tokens = [w for w in words if len(w) >= 3 and w not in GUARD_STOP]
    tokens.sort(key=lambda x: (-len(x), x))
    return tokens


def build_guard(guard_tokens: list[str]) -> str | None:
    """
    Build a regex alternation guard like '(barri|dg)' from the token list.
    Caps at 3 alternatives.
    Returns None if no suitable tokens found.
    """
    if not guard_tokens:
        return None
    selected = guard_tokens[:3]
    if len(selected) == 1:
        return selected[0]
    return '(' + '|'.join(selected) + ')'


def needs_guard(scent_name: str) -> bool:
    """
    Return True if the scent name is generic enough to warrant a maker-prefix guard.

    Conditions (any triggers a guard):
    - 1-2 words, each <= 6 chars
    - Scent name (lowercased) is in ALWAYS_GUARD_WORDS
    - Scent name lowercased consists entirely of ALWAYS_GUARD_WORDS tokens
    """
    lower = scent_name.lower()
    words = lower.split()

    # Short-word heuristic
    if len(words) <= 2 and all(len(w) <= 6 for w in words):
        return True

    # Any word in the scent is a known generic term
    if any(w in ALWAYS_GUARD_WORDS for w in words):
        return True

    return False


def main() -> None:
    soaps_path = '/Users/jmoore/Documents/Projects/sotd_pipeline/data/soaps.yaml'
    correct_path = '/Users/jmoore/Documents/Projects/sotd_pipeline/data/correct_matches/soap.yaml'
    output_path = '/Users/jmoore/Documents/Projects/sotd_pipeline/data/soaps_proposed.yaml'

    with open(soaps_path, encoding='utf-8') as f:
        soaps: dict = yaml.safe_load(f)

    with open(correct_path, encoding='utf-8') as f:
        correct: dict = yaml.safe_load(f)

    # ------------------------------------------------------------------
    # Find missing (maker, scent) pairs
    # ------------------------------------------------------------------
    proposed: dict[str, dict[str, dict]] = {}

    for maker, scents in sorted(correct.items()):
        maker_data = soaps.get(maker, {})
        existing_scents: dict = (maker_data.get('scents') or {}) if maker_data else {}

        # Collect maker patterns for guard token extraction
        maker_patterns: list[str] = (maker_data.get('patterns') or []) if maker_data else []
        guard_tokens = extract_guard_tokens(maker_patterns)

        # Fall back to maker name words if pattern extraction yields nothing useful
        if not guard_tokens:
            guard_tokens = maker_name_tokens(maker)

        guard = build_guard(guard_tokens)

        for scent in sorted(scents.keys()):
            if scent in existing_scents:
                continue  # already catalogued

            # Generate scent pattern core
            scent_core = build_scent_pattern(scent)

            # Decide whether to prepend maker guard
            use_guard = guard if needs_guard(scent) else None
            pattern = f'{use_guard}.*{scent_core}' if use_guard else scent_core

            if maker not in proposed:
                proposed[maker] = {}
            proposed[maker][scent] = {'patterns': [pattern]}

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            proposed,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=True,
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total_scents = sum(len(s) for s in proposed.values())
    print(f'Makers with new scents : {len(proposed)}')
    print(f'Total new scents       : {total_scents}')
    print()
    for maker, scents in sorted(proposed.items()):
        print(f'  {maker} ({len(scents)}):')
        for scent, data in sorted(scents.items()):
            print(f'    {scent!r:40s}  -> {data["patterns"][0]}')


if __name__ == '__main__':
    main()
