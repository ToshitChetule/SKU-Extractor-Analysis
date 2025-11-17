



import os
import pandas as pd
import ollama
import re
from collections import defaultdict
from difflib import get_close_matches

model_name = "llama3"


def process_excel_row_with_llama(sku_text, domain_prompt=None):
    """
    Clean LLaMA extraction with dynamic attribute support.
    No fixed attribute list.
    Rejects explanations, none, n/a, assumptions, parentheses, etc.
    """

    import re
    import ollama

    if not sku_text or not sku_text.strip():
        return []

    # ---------------------------------------------
    # Load KG vocabulary
    # ---------------------------------------------
    neo = Neo4jBuilder()
    try:
        kg_words = neo.get_all_words()
    finally:
        neo.close()

    from models.word_filter import filter_relevant_words
    relevant_words = filter_relevant_words(kg_words, sku_text)

    vocab_block = ", ".join(sorted(set(relevant_words))) if relevant_words else "None"

    # ---------------------------------------------
    # Minimal, strict extraction prompt
    # ---------------------------------------------
    prompt = f"""

      You are a Senior Data Intelligence Assistant for Synexa, an enterprise software company.
Your task is to analyze Synexa’s software SKU descriptions and extract structured attribute–value pairs with strict normalization, logical inference, and zero hallucination.
The accuracy of your extraction directly impacts Synexa’s sales, finance, and product management systems.

CONTEXT

All SKUs belong to the Synexa product family.
Your goal is to interpret each SKU and output normalized attribute–value pairs that represent the product configuration, license type, and commercial motion.

TASK

From each SKU description, extract all relevant attributes and their corresponding values.
Each output must contain only one attribute–value pair per line in the format:

Attribute name: Value

No quotes, extra symbols, or blank lines should appear in the output.
Each attribute should appear only once.
Do not invent or guess attributes that are not present or clearly implied.



CASE STYLE RULES

Attribute names should have only the first word capitalized (for example, "Product name").
Values should be in title case unless they are acronyms (for example, SaaS, BYOC, vCPU).
Each line should strictly follow the pattern “Attribute name: Value”.

PRODUCT FAMILY AND PLATFORM

All SKUs belong to the Synexa family. Always start with:
Product family: Synexa

The main Synexa platform is called Synexa Fusion Platform.
The product name may include “Synexa Fusion”, “Synexa Cloud”, or “Synexa Nexus Data” depending on the SKU text.

If the SKU mentions “Synexa nexus”, “nexus.data”, “nexus.dt”, or “nexus”, normalize the product name to “Synexa Nexus Data”.

COMPONENTS AND ADD-ONS

If the SKU includes the term “X-Engine”, “Xengine”, “with X”, or “AI-Accelerated”, capture it as:
Component: X-Engine

If the SKU includes “Orchestrator”, “with Orch”, or “Orchestrator Module”, capture it as:
Add-on: Orchestrator

MONETIZATION MODEL

If the SKU includes “Perpetual”, “Perp”, or “Lic”, capture as:
Monetization model: Perpetual

If it includes “Subscription”, “Sub”, “Annual”, or terms such as “12 Mo” or “36 Mo”, capture as:
Monetization model: Subscription

Monetization model is distinct from deployment method.

DEPLOYMENT METHOD

If the SKU includes “SaaS”, “Cloud”, or “Cloud Edition”, capture as:
Deployment method: SaaS

If it includes “SW”, “On-Prem”, or “Customer Managed”, capture as:
Deployment method: On-premise

If it includes “BYOC”, capture as:
Deployment method: BYOC

If the SKU includes vCPU or Core and no SaaS reference, infer deployment method as On-premise.
If it includes User or Seat, infer deployment method as SaaS.
If BYOC is mentioned, it always overrides other deployment indicators.

RESOURCE UNITS AND METRIC QUANTITY

If the SKU mentions “vCPU”, “Core”, or “Virtual Processor Core”, capture as:
Resource unit: vCPU

If the SKU mentions “User” or “Seat”, capture as:
Resource unit: User

If the SKU mentions “Instance”, “Server”, or “Env”, capture as:
Resource unit: Instance

If the SKU mentions “VPC” or “vpc”, capture as:
Resource unit: VPC

The number preceding the unit (for example, 16 vCPU or 50 User) should be captured as:
Metric quantity: [number]

LICENSE TERM

Normalize all time durations as follows:
“1 Mo” or “Monthly” → License term: 1 Month
“12 Mo”, “12mo”, “12MO”, “1 Yr”, “Annual”, “Annum” → License term: 12 Months
“36 Mo”, “3 Yr” → License term: 36 Months

EDITION

If the SKU includes “Basic” or “Std”, capture as:
Edition: Standard

If it includes “Pro” or “Professional”, capture as:
Edition: Professional

If it includes “Enterprise”, “Advanced”, or “ENT”, capture as:
Edition: Enterprise

If multiple edition indicators are present, select the highest tier (Enterprise > Professional > Standard).

ENVIRONMENT TYPE AND SUPPORT TYPE

If the SKU includes “Production” or “PROD”, capture as:
Environment type: Production

If it includes “Non-Prod”, “Non-Production”, or “DEV”, capture as:
Environment type: Non-production

If it includes “Standard Support” or “Std Spt”, capture as:
Support type: Standard

If it includes “Advanced Support” or “Adv Spt”, capture as:
Support type: Advanced

PRODUCT TYPE

If the SKU mentions “SW S&S” or “Support and Subscription”, capture as:
Product type: Support And Subscription

If it mentions “License” or “Lic”, capture as:
Product type: License

SALES MOTION

If the SKU includes “New” or “New Customer”, capture as:
Sales motion: New

If it includes “Renewal” or “RNL”, capture as:
Sales motion: Renewal

If it includes “Upgrade” or “UPG”, capture as:
Sales motion: Upgrade

Only one sales motion should be captured per SKU.

HYPERSCALER

If the SKU includes “AWS”, “Azure”, or “GCP”, capture the corresponding value as:
Hyperscaler: AWS
Hyperscaler: Azure
Hyperscaler: GCP

INFERENCE RULES

If resource unit is vCPU or Core, infer deployment method as On-premise.
If resource unit is User or Seat, infer deployment method as SaaS.
If BYOC is mentioned, use BYOC even if SaaS or On-premise also appears.
If 12 Mo, Annual, or Annum appears, normalize license term to 12 Months.
If X-Engine or AI-Accelerated appears, normalize component to X-Engine.
If Orchestrator or with Orch appears, normalize add-on to Orchestrator.
If New Customer appears, normalize sales motion to New.
If Renewal or RNL appears, normalize sales motion to Renewal.

ERROR HANDLING

Do not hallucinate any attribute.
If an attribute cannot be confidently determined, omit it.
Do not output attributes with uncertain or conflicting information.

OUTPUT VALIDATION

All attribute names must match the ones listed above.
All values must follow the normalization and casing rules exactly.
All quantities must be numeric only.
No attribute should repeat.
Each output line must contain exactly one attribute–value pair.

EXAMPLES

Example 1
Input: Synexa Fusion Enterprise - 16 vCPU Perpetual License - New Customer
Output:
Product family: Synexa
Product name: Synexa Fusion
Edition: Enterprise
Metric quantity: 16
Resource unit: vCPU
Monetization model: Perpetual
Deployment method: On-premise
Sales motion: New

Example 2
Input: Synexa Cloud Pro SaaS w/ X-Engine - 50 User Subscription - 12 Mo Renewal
Output:
Product family: Synexa
Product name: Synexa Cloud
Edition: Professional
Component: X-Engine
Metric quantity: 50
Resource unit: User
Monetization model: Subscription
Deployment method: SaaS
License term: 12 Months
Sales motion: Renewal

FINAL INSTRUCTION

Analyze the given SKU description.
Apply all normalization and inference rules strictly.
Return only valid, normalized attribute–value pairs, one per line, in the correct order.
Do not add any commentary, explanation, or formatting other than the attribute–value pairs. 


STRICT RULES:
- Output ONLY attribute-value pairs.
- No explanations.
- No reasoning.
- No sentences.
- No parentheses.
- No "(assuming ...)" or "(implied ...)".
- No "none", "n/a", "not mentioned", or contextual notes.
- If a value is uncertain → SKIP the attribute.
- Format every line EXACTLY as: Attribute: Value

    
ERROR HANDLING

Do not hallucinate any attribute.
If an attribute cannot be confidently determined, omit it.
Do not output attributes with uncertain or conflicting information.

OUTPUT VALIDATION

All attribute names must match the ones listed above.
All values must follow the normalization and casing rules exactly.
All quantities must be numeric only.
No attribute should repeat.
Each output line must contain exactly one attribute–value pair.


Use these dataset vocabulary words when applicable:
{vocab_block}

CONTEXT:
{domain_prompt}

SKU:
{sku_text}

Return ONLY lines like:
Attribute: Value
"""

    # ---------------------------------------------
    # Call model
    # ---------------------------------------------
    try:
        resp = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )
        raw_output = resp["message"]["content"].strip()

    except Exception as e:
        print("LLM error:", e)
        return []

    # ---------------------------------------------
    # Clean & parse lines
    # ---------------------------------------------
    rows = []
    for line in raw_output.splitlines():

        line = line.strip()
        if not line:
            continue

        # Reject lines with parentheses (explanations)
        if "(" in line or ")" in line:
            continue

        # Reject known bad phrases
        bad_words = [
            "not mentioned", "none", "n/a", "na",
            "no mention", "implied", "assuming"
        ]
        if any(b in line.lower() for b in bad_words):
            continue

        # Accept only A: B pattern
        m = re.match(r"(.+?)\s*[:=]\s*(.+)", line)
        if not m:
            continue

        attr, val = m.groups()
        attr = attr.strip()
        val = val.strip()

        # Extra cleanup
        if val.lower() in ["none", "n/a", ""]:
            continue

        val = re.sub(r"[;.\-]+$", "", val).strip()

        # Final rejection of parentheses in value
        if "(" in val or ")" in val:
            continue

        rows.append([attr, val])

    return rows




from models.word_filter import filter_relevant_words
from graph.neo4j_builder import Neo4jBuilder

def process_excel_row_with_llama(sku_text, domain_prompt=None):
    """
    Process a single SKU description using LLaMA + KG vocabulary.
    """

    if not sku_text or sku_text.strip() == "":
        return []

    # 📌 Load KG words
    neo = Neo4jBuilder()
    try:
        all_words = neo.get_all_words()
    finally:
        neo.close()

    # 🎯 Filter only relevant words for this SKU
    relevant_words = filter_relevant_words(all_words, sku_text)

    # 🧠 Inject vocabulary into prompt
    vocab_text = ", ".join(relevant_words) if relevant_words else "None"

    prompt = f"""
{domain_prompt}

### IMPORTANT — CONTROLLED VOCABULARY
The following normalized terms come from the Knowledge Graph, extracted from the dataset.
Use these words EXACTLY when applicable in the output:

{vocab_text}

### SKU Description
{sku_text}

Return only the attribute-value pairs, one per line.
"""

    try:
        import ollama
        import re

        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )
        text = response["message"]["content"].strip()

        rows = []
        for line in text.splitlines():
            match = re.match(r"(.+?)\s*[:=]\s*(.+)", line.strip())
            if match:
                attr, val = match.groups()
                rows.append([attr.strip(), val.strip()])

        return rows

    except Exception as e:
        print(f"❌ Row processing error with vocabulary: {e}")
        return []



def refine_with_llama(selected_rows, chat_history, full_table):
    import ollama
    import json

    prompt = (
        f"You are refining a table of attributes and values. "
        f"Here are the rows the user selected: {selected_rows}. "
        f"The user instruction is: {chat_history[-1]['content']}. "
        f"Return ONLY the corrected attribute name and value pairs "
        f"in plain JSON array format."
    )

    response = ollama.chat(model=model_name, messages=[{"role": "user", "content": prompt}])
    output_text = response["message"]["content"]

    try:
        refined_rows = json.loads(output_text)
    except json.JSONDecodeError:
        lines = [line for line in output_text.split("\n") if "=" in line]
        refined_rows = []
        for line in lines:
            parts = line.split("=")
            if len(parts) >= 2:
                refined_rows.append([parts[0].strip(), "=".join(parts[1:]).strip()])

    for i, row in enumerate(selected_rows):
        if row in full_table:
            idx = full_table.index(row)
            if i < len(refined_rows):
                full_table[idx] = refined_rows[i]

    return full_table





















# backend/models/llama_excel.py
import os
import re
from collections import defaultdict

import ollama

model_name = "llama3"

from graph.neo4j_builder import Neo4jBuilder
from models.word_filter import filter_relevant_words
from models.kg_normalizer import normalize_attr_values, best_match


def _parse_llm_output(text):
    """
    Parse LLM output lines into list of [attr, val].
    Strict: accepts only "Attr: Value" or "Attr = Value"
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # reject parentheses / obvious explanatory lines
        if "(" in line or ")" in line:
            continue
        if any(b in line.lower() for b in ["not mentioned", "n/a", "none", "implied", "assuming"]):
            continue
        m = re.match(r"(.+?)\s*[:=]\s*(.+)", line)
        if not m:
            continue
        attr, val = m.groups()
        attr = attr.strip()
        val = val.strip()
        # clean trailing punctuation
        val = re.sub(r"[;.\-]+$", "", val).strip()
        if val.lower() in ["", "none", "n/a", "na", "-"]:
            continue
        # avoid parentheses in final value
        if "(" in val or ")" in val:
            continue
        rows.append([attr, val])
    return rows


def process_excel_row_with_llama(sku_text, domain_prompt=None):
    """
    Process a single SKU description using LLaMA + KG vocabulary + value->attribute inference.
    Returns list of [attribute, value] pairs.
    """

    if not sku_text or not sku_text.strip():
        return []

    neo = Neo4jBuilder()
    try:
        kg_words = neo.get_all_words() or []
        value_attr_map = neo.get_value_attribute_map() or {}
        kg_values = list(value_attr_map.keys())  # list of canonical values in KG
    finally:
        neo.close()

    # filter only relevant words for this SKU to keep prompt small
    relevant_words = filter_relevant_words(kg_words, sku_text)
    vocab_block = ", ".join(sorted(set(relevant_words))) if relevant_words else "None"

    # Build a compact and strict value->attribute block for the prompt
    # Limit length to avoid extremely long prompts; include top matches + unique mapping
    value_lines = []
    # include only values that are short (avoid long sentence values), and limit to first 300 entries
    for v, attrs in list(value_attr_map.items())[:300]:
        if not v or len(v) > 120:
            continue
        # join attributes as comma-separated
        value_lines.append(f"- {v}: {', '.join(attrs)}")
    value_map_block = "\n".join(value_lines) if value_lines else "None"

    prompt = f"""


      You are a Senior Data Intelligence Assistant for Synexa, an enterprise software company.
Your task is to analyze Synexa’s software SKU descriptions and extract structured attribute–value pairs with strict normalization, logical inference, and zero hallucination.
The accuracy of your extraction directly impacts Synexa’s sales, finance, and product management systems.

CONTEXT

All SKUs belong to the Synexa product family.
Your goal is to interpret each SKU and output normalized attribute–value pairs that represent the product configuration, license type, and commercial motion.

TASK

From each SKU description, extract all relevant attributes and their corresponding values.
Each output must contain only one attribute–value pair per line in the format:

Attribute name: Value

No quotes, extra symbols, or blank lines should appear in the output.
Each attribute should appear only once.
Do not invent or guess attributes that are not present or clearly implied.



CASE STYLE RULES

Attribute names should have only the first word capitalized (for example, "Product name").
Values should be in title case unless they are acronyms (for example, SaaS, BYOC, vCPU).
Each line should strictly follow the pattern “Attribute name: Value”.

PRODUCT FAMILY AND PLATFORM

All SKUs belong to the Synexa family. Always start with:
Product family: Synexa

The main Synexa platform is called Synexa Fusion Platform.
The product name may include “Synexa Fusion”, “Synexa Cloud”, or “Synexa Nexus Data” depending on the SKU text.

If the SKU mentions “Synexa nexus”, “nexus.data”, “nexus.dt”, or “nexus”, normalize the product name to “Synexa Nexus Data”.

COMPONENTS AND ADD-ONS

If the SKU includes the term “X-Engine”, “Xengine”, “with X”, or “AI-Accelerated”, capture it as:
Component: X-Engine

If the SKU includes “Orchestrator”, “with Orch”, or “Orchestrator Module”, capture it as:
Add-on: Orchestrator

MONETIZATION MODEL

If the SKU includes “Perpetual”, “Perp”, or “Lic”, capture as:
Monetization model: Perpetual

If it includes “Subscription”, “Sub”, “Annual”, or terms such as “12 Mo” or “36 Mo”, capture as:
Monetization model: Subscription

Monetization model is distinct from deployment method.

DEPLOYMENT METHOD

If the SKU includes “SaaS”, “Cloud”, or “Cloud Edition”, capture as:
Deployment method: SaaS

If it includes “SW”, “On-Prem”, or “Customer Managed”, capture as:
Deployment method: On-premise

If it includes “BYOC”, capture as:
Deployment method: BYOC

If the SKU includes vCPU or Core and no SaaS reference, infer deployment method as On-premise.
If it includes User or Seat, infer deployment method as SaaS.
If BYOC is mentioned, it always overrides other deployment indicators.

RESOURCE UNITS AND METRIC QUANTITY

If the SKU mentions “vCPU”, “Core”, or “Virtual Processor Core”, capture as:
Resource unit: vCPU

If the SKU mentions “User” or “Seat”, capture as:
Resource unit: User

If the SKU mentions “Instance”, “Server”, or “Env”, capture as:
Resource unit: Instance

If the SKU mentions “VPC” or “vpc”, capture as:
Resource unit: VPC

The number preceding the unit (for example, 16 vCPU or 50 User) should be captured as:
Metric quantity: [number]

LICENSE TERM

Normalize all time durations as follows:
“1 Mo” or “Monthly” → License term: 1 Month
“12 Mo”, “12mo”, “12MO”, “1 Yr”, “Annual”, “Annum” → License term: 12 Months
“36 Mo”, “3 Yr” → License term: 36 Months

EDITION

If the SKU includes “Basic” or “Std”, capture as:
Edition: Standard

If it includes “Pro” or “Professional”, capture as:
Edition: Professional

If it includes “Enterprise”, “Advanced”, or “ENT”, capture as:
Edition: Enterprise

If multiple edition indicators are present, select the highest tier (Enterprise > Professional > Standard).

ENVIRONMENT TYPE AND SUPPORT TYPE

If the SKU includes “Production” or “PROD”, capture as:
Environment type: Production

If it includes “Non-Prod”, “Non-Production”, or “DEV”, capture as:
Environment type: Non-production

If it includes “Standard Support” or “Std Spt”, capture as:
Support type: Standard

If it includes “Advanced Support” or “Adv Spt”, capture as:
Support type: Advanced

PRODUCT TYPE

If the SKU mentions “SW S&S” or “Support and Subscription”, capture as:
Product type: Support And Subscription

If it mentions “License” or “Lic”, capture as:
Product type: License

SALES MOTION

If the SKU includes “New” or “New Customer”, capture as:
Sales motion: New

If it includes “Renewal” or “RNL”, capture as:
Sales motion: Renewal

If it includes “Upgrade” or “UPG”, capture as:
Sales motion: Upgrade

Only one sales motion should be captured per SKU.

HYPERSCALER

If the SKU includes “AWS”, “Azure”, or “GCP”, capture the corresponding value as:
Hyperscaler: AWS
Hyperscaler: Azure
Hyperscaler: GCP

INFERENCE RULES

If resource unit is vCPU or Core, infer deployment method as On-premise.
If resource unit is User or Seat, infer deployment method as SaaS.
If BYOC is mentioned, use BYOC even if SaaS or On-premise also appears.
If 12 Mo, Annual, or Annum appears, normalize license term to 12 Months.
If X-Engine or AI-Accelerated appears, normalize component to X-Engine.
If Orchestrator or with Orch appears, normalize add-on to Orchestrator.
If New Customer appears, normalize sales motion to New.
If Renewal or RNL appears, normalize sales motion to Renewal.

ERROR HANDLING

Do not hallucinate any attribute.
If an attribute cannot be confidently determined, omit it.
Do not output attributes with uncertain or conflicting information.

OUTPUT VALIDATION

All attribute names must match the ones listed above.
All values must follow the normalization and casing rules exactly.
All quantities must be numeric only.
No attribute should repeat.
Each output line must contain exactly one attribute–value pair.

EXAMPLES

Example 1
Input: Synexa Fusion Enterprise - 16 vCPU Perpetual License - New Customer
Output:
Product family: Synexa
Product name: Synexa Fusion
Edition: Enterprise
Metric quantity: 16
Resource unit: vCPU
Monetization model: Perpetual
Deployment method: On-premise
Sales motion: New

Example 2
Input: Synexa Cloud Pro SaaS w/ X-Engine - 50 User Subscription - 12 Mo Renewal
Output:
Product family: Synexa
Product name: Synexa Cloud
Edition: Professional
Component: X-Engine
Metric quantity: 50
Resource unit: User
Monetization model: Subscription
Deployment method: SaaS
License term: 12 Months
Sales motion: Renewal

FINAL INSTRUCTION

Analyze the given SKU description.
Apply all normalization and inference rules strictly.
Return only valid, normalized attribute–value pairs, one per line, in the correct order.
Do not add any commentary, explanation, or formatting other than the attribute–value pairs. 


STRICT RULES:
- Output ONLY attribute-value pairs.
- No explanations.
- No reasoning.
- No sentences.
- No parentheses.
- No "(assuming ...)" or "(implied ...)".
- No "none", "n/a", "not mentioned", or contextual notes.
- If a value is uncertain → SKIP the attribute.
- Format every line EXACTLY as: Attribute: Value


ERROR HANDLING

Do not hallucinate any attribute.
If an attribute cannot be confidently determined, omit it.
Do not output attributes with uncertain or conflicting information.

OUTPUT VALIDATION

All attribute names must match the ones listed above.
All values must follow the normalization and casing rules exactly.
All quantities must be numeric only.
No attribute should repeat.
Each output line must contain exactly one attribute–value pair.



{domain_prompt}

### CONTROLLED VOCABULARY (words extracted from the dataset)
Use these tokens as-is when they appear in the SKU:
{vocab_block}

### KNOWLEDGE GRAPH VALUE → ATTRIBUTE MAP
If a SKU value exactly or closely matches any of these values, the LLM must use the ATTRIBUTE listed.
Use attribute names exactly as shown (case sensitive).
{value_map_block}

### SKU DESCRIPTION
{sku_text}

INSTRUCTIONS:
- Return ONLY attribute:value lines (one per line).
- Use the KG values/attributes when they apply.
- Do NOT output explanations, lists, or other text.
- Use Title Case for values and Attribute names with first word capitalized (e.g., "Product name: Synexa Cloud").
- If uncertain about an attribute, omit it.

Return only the lines.
"""

    try:
        resp = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        raw_output = resp["message"]["content"].strip()
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return []

    # parse LLM output into pairs
    parsed_rows = _parse_llm_output(raw_output)

    # Post-processing: smart normalization with KG
    # 1) Build dict attr -> set(values)
    extracted_map = defaultdict(set)
    for a, v in parsed_rows:
        extracted_map[a].add(v)

    # 2) Use kg_normalizer to canonicalize values where possible
    #    normalize_attr_values expects (attr_map, neo4j_builder) — but it fetches KG values itself
    neo = Neo4jBuilder()
    try:
        # normalize values using KG (best-match)
        try:
            normalized = normalize_attr_values(extracted_map, neo, min_ratio=0.78)
        except Exception:
            # fallback: keep extracted_map as-is converted to sets
            normalized = {k: set(vs) for k, vs in extracted_map.items()}

        # 3) If a normalized value matches a KG value, and KG says that value belongs to a (one) attribute,
        #    prefer KG's attribute name (attribute inference).
        value_attr_map = neo.get_value_attribute_map()
    finally:
        neo.close()

    final_pairs = []
    for llm_attr, vals in normalized.items():
        for val in vals:
            # try exact case-insensitive match first
            matched_key = None
            for kv in value_attr_map.keys():
                if kv and str(kv).strip().lower() == str(val).strip().lower():
                    matched_key = kv
                    break

            # if exact not found, try fuzzy best_match (from kg_normalizer.best_match)
            if matched_key is None:
                try:
                    fuzzy = best_match(val, list(value_attr_map.keys()), min_ratio=0.78)
                    if fuzzy:
                        matched_key = fuzzy
                except Exception:
                    matched_key = None

            if matched_key:
                # KG tells which attributes that value belongs to
                attrs_for_value = value_attr_map.get(matched_key, [])
                # If KG maps the value to exactly one attribute, use that attribute name
                if isinstance(attrs_for_value, (list, tuple, set)) and len(attrs_for_value) == 1:
                    chosen_attr = attrs_for_value[0]
                elif isinstance(attrs_for_value, (list, tuple, set)) and len(attrs_for_value) > 1:
                    # if multiple, prefer LLM attribute if it matches one (case-insensitive), else choose first
                    chosen_attr = None
                    for a in attrs_for_value:
                        if a.strip().lower() == llm_attr.strip().lower():
                            chosen_attr = a
                            break
                    if not chosen_attr:
                        chosen_attr = attrs_for_value[0]
                else:
                    chosen_attr = llm_attr
                final_pairs.append([chosen_attr, matched_key])
            else:
                # no KG match — keep LLM attribute and LLM value
                final_pairs.append([llm_attr, val])

    # deduplicate while preserving order-ish
    seen = set()
    deduped = []
    for a, v in final_pairs:
        key = (a.strip(), v.strip())
        if key not in seen:
            seen.add(key)
            deduped.append([a.strip(), v.strip()])

    return deduped
