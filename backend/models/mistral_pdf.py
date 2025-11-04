import os
import re
import pandas as pd
import pdfplumber
from collections import defaultdict
import ollama

model_name = "mistral"
MAX_CHARS_PER_CHUNK = 3000

def process_pdf_with_mistral(filepath):
    def extract_text_from_pdf(pdf_file):
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables() or []
                for table in tables:
                    for row in table:
                        if row:
                            text += " | ".join([str(cell).strip() for cell in row if cell]) + "\n"
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        return cleaned_text

    def chunk_text(text, max_chars=MAX_CHARS_PER_CHUNK):
        chunks = []
        while len(text) > 0:
            chunk = text[:max_chars]
            split_pos = max(chunk.rfind("."), chunk.rfind("\n"))
            if split_pos > 100:
                chunk = chunk[:split_pos + 1]
            chunks.append(chunk.strip())
            text = text[len(chunk):].strip()
        return chunks

    def extract_attributes(text_chunk):
        if not text_chunk.strip():
            return ""
        prompt = f"""
        You are an expert analyst. Extract attributes and their possible values:
        {text_chunk}
        """
        try:
            response = ollama.chat(
                model=model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return ""

    def parse_attributes(text):
        attr_dict = defaultdict(list)
        lines = re.split(r'[\n;]', text)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = re.split(r'(?<!\w)=(?!\w)', line)
            if len(parts) >= 2:
                attr = parts[0].strip()
                values = [v.strip() for v in re.split(r"[;,|]", parts[1]) if v.strip()]
                attr_dict[attr].extend(values)
        return attr_dict

    def merge_attributes(list_of_dicts):
        merged = defaultdict(list)
        for d in list_of_dicts:
            for attr, vals in d.items():
                merged[attr].extend(vals)
        for attr in merged:
            merged[attr] = list(dict.fromkeys(merged[attr]))
        return merged

    pdf_text = extract_text_from_pdf(filepath)
    chunks = chunk_text(pdf_text)
    all_attrs = []
    for chunk in chunks:
        raw_output = extract_attributes(chunk)
        attr_dict = parse_attributes(raw_output)
        all_attrs.append(attr_dict)

    merged_attr = merge_attributes(all_attrs)
    if not merged_attr:
        return {"columns": ["Attribute", "Value1"], "rows": []}

    rows = []
    max_values = max(len(vals) for vals in merged_attr.values())
    columns = ["Attribute"] + [f"Value{i+1}" for i in range(max_values)]

    for attr, vals in merged_attr.items():
        row = [attr] + vals + [""] * (max_values - len(vals))
        rows.append(row)

    return {"columns": columns, "rows": rows}
