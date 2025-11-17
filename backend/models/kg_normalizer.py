# models/kg_normalizer.py
from difflib import SequenceMatcher, get_close_matches
import re

def _clean_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = re.sub(r"\s+", " ", s)
    return s

def best_match(candidate: str, choices: list[str], min_ratio: float = 0.72) -> str | None:
    """
    Return the best matching choice from choices for candidate.
    If an exact case-insensitive match exists -> return it.
    If fuzzy match above min_ratio exists -> return it.
    Otherwise return None.
    """
    if not candidate or not choices:
        return None

    cand = _clean_text(candidate).lower()

    # exact case-insensitive match first
    for c in choices:
        if _clean_text(c).lower() == cand:
            return c

    # try get_close_matches on raw candidate against choices (case-sensitive),
    # but adapt choices to plain strings for get_close_matches.
    # We'll use cutoff = min_ratio
    try:
        matches = get_close_matches(candidate, choices, n=1, cutoff=min_ratio)
        if matches:
            return matches[0]
    except Exception:
        pass

    # fallback: compute best ratio using SequenceMatcher
    best = None
    best_r = 0.0
    for c in choices:
        r = SequenceMatcher(None, cand, _clean_text(c).lower()).ratio()
        if r > best_r:
            best_r = r
            best = c

    if best_r >= min_ratio:
        return best

    return None

def normalize_attr_values(attr_map: dict, neo4j_builder, min_ratio: float = 0.72, debug: bool = False):
    """
    attr_map: { attribute_name (str) : set(values) }
    neo4j_builder: instance of Neo4jBuilder (used to fetch KG values)
    Returns: new_map where each value is replaced by the KG canonical value if a match is found,
             otherwise keeps the original cleaned value.
    """
    # fetch the canonical values from KG (global)
    kg_values = neo4j_builder.get_all_values() or []
    kg_values = [str(v) for v in kg_values if v is not None]

    normalized_map = {}
    for attr, vals in attr_map.items():
        normalized_set = set()
        for v in vals:
            v_str = str(v).strip()
            if not v_str:
                continue

            # try to match to KG
            match = best_match(v_str, kg_values, min_ratio=min_ratio)
            if match:
                normalized_set.add(match)  # use the canonical KG value
                if debug:
                    print(f"[KG MATCH] '{v_str}' -> '{match}'")
            else:
                # fallback: keep cleaned LLM value (no parentheses, no "not mentioned")
                clean = re.sub(r"\(.*?\)", "", v_str).strip()
                # drop obviously bad tokens
                if clean.lower() in ("none", "n/a", "na", "-"):
                    continue
                if clean:
                    normalized_set.add(clean)
                    if debug:
                        print(f"[KG NONE] keep '{v_str}' -> '{clean}'")
        if normalized_set:
            normalized_map[attr] = normalized_set
    return normalized_map
