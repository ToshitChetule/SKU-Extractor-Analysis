



import pandas as pd
import re

def preprocess_file(filepath):
    """
    Reads Excel file, cleans description text, extracts WORD tokens only,
    and returns a SET of unique words.
    """

    df = pd.read_excel(filepath)

    if "SKU_Description" not in df.columns:
        raise Exception("Excel must contain 'SKU_Description' column")

    vocab = set()

    for desc in df["SKU_Description"].astype(str):
        # lower case
        text = desc.lower()

        # remove punctuation except hyphens
        text = re.sub(r"[^a-zA-Z0-9\- ]+", " ", text)

        # split into tokens
        words = text.split()

        # filter out very small garbage tokens
        words = [w.strip() for w in words if len(w.strip()) > 1]

        vocab.update(words)

    return sorted(vocab)
