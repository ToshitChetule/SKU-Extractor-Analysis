import re

def filter_relevant_words(all_words, sku_text):
    """
    Extract only relevant KG words for this SKU.
    Removes long phrases, numbers, noise, etc.
    """
    sku_lower = sku_text.lower()

    relevant = []

    for w in all_words:
        if not w:
            continue

        w_clean = w.strip().lower()

        # skip very long multi-word phrases (they come from bad splits)
        if len(w_clean.split()) > 3:
            continue

        # skip numeric-only tokens unless meaningful
        if re.fullmatch(r"\d+", w_clean):
            continue

        # pick only KG words that appear inside SKU text
        if w_clean in sku_lower:
            relevant.append(w_clean)

    # Keep unique
    return list(sorted(set(relevant)))
