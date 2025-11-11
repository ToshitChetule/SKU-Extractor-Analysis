from flask import Flask, request, jsonify, send_file
import os
from flask_cors import CORS
import pandas as pd
from variant_analysis import run_variant_analysis

# 🧠 Imports
from models.llama_excel import process_excel_row_with_llama
from models.mistral_pdf import process_pdf_with_mistral_normalizer
from graph.neo4j_builder import Neo4jBuilder  # optional but kept for your KG logic
from models.refine_graph import refine_with_graph_context



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🧠 Domain-specific prompt generator
def get_domain_prompt(industry, product_type):
    base_prompt = f"""
    # Instructions for the Model

    You are processing SKU descriptions at scale. Extract attributes and values that are clearly stated or strongly implied.
    Normalize abbreviations, shorthand, and codes into human-readable attributes and values.
    Merge duplicate attributes (textual variants or semantic duplicates) into a single attribute using a consistent Title Case name.
    Prioritize commercial, monetization, and marketing attributes when present.
    

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

ATTRIBUTE ORDER

Always follow this order if applicable:

Product family
Product name
Edition
Component
Add-on
Metric quantity
Resource unit
Monetization model
Deployment method
License term
Product type
Environment type
Support type
Hyperscaler
Sales motion

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



    ### CONTEXT
    Industry: {industry if industry else "general"}
    Product Type: {product_type if product_type else "unspecified"}
    """

    domain_prompts = {
        "automotive": """
        Focus on vehicle specifications:
        - Make, Model, Trim, Year
        - Engine details, Power (HP), Torque (Nm), Transmission
        - Fuel type, Tank capacity, Mileage
        - Dimensions, Weight, Ground clearance
        - Compatibility and Part number
        """,
        "pharmaceuticals": """
        Focus on:
        - Brand and Generic Name
        - Strength (mg/ml)
        - Dosage Form (Tablet, Capsule, Syrup)
        - Ingredients, Packaging type, Quantity
        - Manufacturer, Expiry date, Batch/Lot, Therapeutic category
        """,
        "electronics": """
        Focus on:
        - Brand, Model number, Series
        - Power, Voltage, Frequency, Capacity (GB/TB)
        - Battery, Display size, Resolution
        - Connectivity (Wi-Fi, Bluetooth, HDMI)
        - Warranty, Material, Weight, Dimensions
        """,
        "food_beverages": """
        Focus on:
        - Product name, Brand
        - Ingredients, Nutritional values
        - Net weight/volume, Flavor
        - Packaging type/material, Shelf life
        - Manufacturer, Country of origin
        """,
        "chemical": """
        Focus on:
        - Chemical name, Formula, Purity, CAS number
        - Physical form, Molecular weight, Boiling/Melting point
        - Applications, Packaging, Safety classification
        """
    }

    if industry and industry.lower() in domain_prompts:
        base_prompt += domain_prompts[industry.lower()]
    else:
        base_prompt += "\nExtract all relevant descriptive and technical attributes clearly."

    return base_prompt


# 🧾 Main File Processing Endpoint
@app.route("/process", methods=["POST"])
def process_file():
    """Handles Excel or PDF upload and returns both SKU-level and aggregated data."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    # Extract user context
    industry = request.form.get("industry", "general")
    product_type = request.form.get("productType", "")
    domain_prompt = get_domain_prompt(industry, product_type)

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    ext = os.path.splitext(filename)[1].lower()
    print(f"\n📂 Received file: {filename} ({ext})")

    try:
        # ✅ Excel Processing
        if ext in [".xlsx", ".xls"]:
            df = pd.read_excel(filepath)

            if "SKU_Description" not in df.columns:
                return jsonify({"error": "Missing 'SKU_Description' column in Excel."}), 400

            total_rows = len(df)
            print(f"🚀 Processing {total_rows} SKU rows using LLaMA...\n")

            attribute_map = {}
            sku_matrix = []  # 🆕 For SKU-level matrix

            for i, row in df.iterrows():
                sku_text = str(row["SKU_Description"]).strip()
                if not sku_text:
                    continue

                print(f"🧠 Processing row {i + 1}/{total_rows}: {sku_text[:100]}...")
                extracted_pairs = process_excel_row_with_llama(sku_text, domain_prompt)

                # 🧩 Store SKU-level data
                sku_matrix.append({
                    "sku": sku_text,
                    "attributes": extracted_pairs
                })

                # 🧩 Build aggregated attribute map
                for attr, val in extracted_pairs:
                    if attr not in attribute_map:
                        attribute_map[attr] = set()
                    for v in str(val).split(","):
                        clean_val = v.strip()
                        if clean_val:
                            attribute_map[attr].add(clean_val)

            # 🧮 Build Aggregated Matrix
            max_values = max(len(vals) for vals in attribute_map.values()) if attribute_map else 0
            columns = ["Attribute"] + [f"Value{i + 1}" for i in range(max_values)]

            rows = []
            for attr, vals in attribute_map.items():
                val_list = list(vals)
                val_list += [""] * (max_values - len(val_list))
                rows.append([attr] + val_list)

            print("\n✅ Row-by-row Excel processing complete with multi-value support.\n")

            # 🕸️ Push extracted attributes to Neo4j Knowledge Graph (optional)
           # 🕸️ Push extracted attributes to Neo4j Knowledge Graph (optional)
            try:
                print("📡 Connecting to Neo4j for Knowledge Graph update...")
                neo = Neo4jBuilder()

                 # 🧹 Clear any previous data before inserting the new session
                neo.clear_database()
                print("🧹 Cleared old data from Neo4j (session-only mode).")
                neo.add_attribute_value_pairs(attribute_map)
                neo.close()
                print("✅ Knowledge Graph successfully updated.\n")
            except Exception as graph_error:
                print(f"⚠️ Neo4j update skipped due to error: {graph_error}")

            # ✅ Return both data types to frontend
            return jsonify({
                "sku_matrix": sku_matrix,  # Per-SKU extracted data
                "aggregated_matrix": {     # Unique attribute-value pairs
                    "columns": columns,
                    "rows": rows
                },
                "model_used": "llama3",
                "industry": industry,
                "product_type": product_type
            })


        elif ext == ".pdf":
            print("🚀 Running Mistral + Normalizer extraction...\n")
            result = process_pdf_with_mistral_normalizer(filepath, domain_prompt)

            return jsonify({
                "sku_matrix": [],
                "aggregated_matrix": {
                    "columns": result.get("columns", []),
                    "rows": result.get("rows", [])
                },
                "model_used": "Mistral + Normalizer",
                "industry": industry,
                "product_type": product_type
            })



        # else:
        #     return jsonify({"error": f"Unsupported file type: {ext}"}), 400

    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        return jsonify({"error": str(e)}), 500


# # ✅ Attribute & Value Refinement via Knowledge Graph
# @app.route("/refine_graph", methods=["POST", "OPTIONS"])
# def refine_graph():
#     if request.method == "OPTIONS":
#         return jsonify({"status": "OK"}), 200

#     from graph.neo4j_builder import Neo4jBuilder
#     from models.refine_graph import refine_with_graph_context

#     try:
#         data = request.get_json()
#         attribute = data.get("attribute")
#         prompt = data.get("prompt")

#         if not attribute or not prompt:
#             return jsonify({"error": "Missing attribute or prompt"}), 400

#         neo = Neo4jBuilder()

#         # 🧩 Step 1: Get current graph context
#         current_values = neo.get_values(attribute)
#         graph_context = {"attribute": attribute, "values": current_values}

#         print(f"🔍 Graph context for refinement: {graph_context}")

#         # 🧠 Step 2: Get LLM-generated refinement plan
#         plan = refine_with_graph_context(graph_context, prompt)
#         print(f"🧩 Model refinement plan: {plan}")

#         if not plan:
#             neo.close()
#             return jsonify({"error": "Model returned empty or invalid refinement plan."}), 400

#         # 🧩 Step 3: Apply refinements in Neo4j
#         new_attr_name = attribute
#         if "rename_attribute_to" in plan:
#             new_attr_name = plan["rename_attribute_to"]
#             neo.rename_attribute(attribute, new_attr_name)

#         if "add_values" in plan:
#             for v in plan["add_values"]:
#                 neo.add_value(new_attr_name, v)

#         if "remove_values" in plan:
#             for v in plan["remove_values"]:
#                 neo.remove_value(new_attr_name, v)

#         # Future: handle merging or selective "keep_values" if needed
#         # For now, we'll assume LLM instructs which to keep/remove explicitly

#         # 🧩 Step 4: Fetch updated data for UI
#         updated_values = neo.get_values(new_attr_name)
#         neo.close()

#         return jsonify({
#             "updated_context": {
#                 "attribute": new_attr_name,
#                 "values": updated_values,
#                 "related_attributes": plan.get("merge_with_attributes", [])
#             }
#         })

#     except Exception as e:
#         print(f"❌ Error in refine_graph: {e}")
#         return jsonify({"error": str(e)}), 500

def detect_refinement_intent(user_prompt: str):
    """
    Detects whether the user wants to rename an attribute or a value.
    Returns one of: 'attribute', 'value', or 'unknown'.
    """
    if not user_prompt:
        return "unknown"

    p = user_prompt.lower()

    # Clear rules
    if "rename" in p and "attribute" in p:
        return "attribute"
    if "rename" in p and "value" in p:
        return "value"

    # Heuristics (for less explicit prompts)
    if "under" in p or "in " in p or "inside" in p:
        return "value"

    return "attribute"




# @app.route("/refine_graph", methods=["POST", "OPTIONS"])
# def refine_graph():
#     if request.method == "OPTIONS":
#         return jsonify({"status": "OK"}), 200

#     from models.refine_graph import refine_with_graph_context
#     from graph.neo4j_builder import Neo4jBuilder

#     try:
#         data = request.get_json()
#         attribute = data.get("attribute")
#         user_prompt = data.get("prompt")

#         if not attribute or not user_prompt:
#             return jsonify({"error": "Missing 'attribute' or 'prompt'."}), 400

#         neo = Neo4jBuilder()

#         # 🧠 Fetch current graph context
#         graph_context = {
#             "attribute": attribute,
#             "values": neo.get_values(attribute)
#         }
#         print("🔍 Graph context for refinement:", graph_context)

#         # 🧩 Ask model for structured refinement plan
#         plan = refine_with_graph_context(graph_context, user_prompt)
#         print("🧩 Model refinement plan:", plan)

#         updated_attribute = attribute
#         updated_values = graph_context["values"]

#         # ------------------------------------------------------------------
#         # 🔧 Execute refinement actions based on model plan
#         # ------------------------------------------------------------------
#         if "remove_attribute" in plan:
#             neo.delete_attribute(plan["remove_attribute"])
#             print(f"🗑️ Deleted attribute '{plan['remove_attribute']}' from Neo4j.")
#             updated_attribute = None
#             updated_values = []

#         elif "rename_attribute_to" in plan:
#             new_name = plan["rename_attribute_to"]
#             neo.rename_attribute(attribute, new_name)
#             updated_attribute = new_name

#         if "merge_with_attributes" in plan:
#             merge_list = plan["merge_with_attributes"]
#             if updated_attribute not in merge_list:
#                 merge_list.append(updated_attribute)
#             neo.merge_attributes(merge_list, updated_attribute)

#         if "add_values" in plan:
#             for val in plan["add_values"]:
#                 neo.add_value(updated_attribute, val)
#                 updated_values.append(val)

#         if "remove_values" in plan:
#             for val in plan["remove_values"]:
#                 neo.remove_value(updated_attribute, val)
#                 updated_values = [v for v in updated_values if v.lower() != val.lower()]

#         if "keep_values" in plan:
#             updated_values = [v for v in updated_values if v in plan["keep_values"]]

#         # ------------------------------------------------------------------
#         # 🧱 Build response + update UI
#         # ------------------------------------------------------------------
#         updated_context = {
#             "attribute": updated_attribute,
#             "values": sorted(set(updated_values)),
#             "related_attributes": plan.get("merge_with_attributes", [])
#         }

#         neo.close()

#         print("✅ Refinement applied successfully:", updated_context)
#         return jsonify({"updated_context": updated_context}), 200

#     except Exception as e:
#         print(f"❌ Error in refine_graph: {e}")
#         return jsonify({"error": str(e)}), 500

@app.route("/refine_graph", methods=["POST", "OPTIONS"])
def refine_graph():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        data = request.get_json()
        attribute = data.get("attribute")
        prompt = data.get("prompt")

        from models.refine_graph import refine_with_graph_context
        from graph.neo4j_builder import Neo4jBuilder

        neo = Neo4jBuilder()

        # 1️⃣ Get graph context
        values = neo.get_values(attribute)
        graph_context = {"attribute": attribute, "values": values}
        print("🔍 Graph context for refinement:", graph_context)

        # 2️⃣ Send to model
        plan = refine_with_graph_context(graph_context, prompt)
        print("🧩 Model refinement plan:", plan)

        # 3️⃣ Detect user intent before acting
        intent = detect_refinement_intent(prompt)

        # 4️⃣ Execute corresponding Neo4j operation
        if intent == "attribute" and "rename_attribute_to" in plan:
            new_name = plan["rename_attribute_to"]
            neo.rename_attribute(attribute, new_name)
            updated_attr = new_name
            updated_values = neo.get_values(new_name)

        elif intent == "value":
            # Rename value logic — detect from prompt if possible
            import re
            match = re.search(r"rename value\s+(.*?)\s+to\s+(.*?)($|\s|under|in)", prompt.lower())
            if match:
                old_val, new_val = match.groups()[:2]
                neo.rename_value(attribute, old_val.strip(), new_val.strip())
                updated_attr = attribute
                updated_values = neo.get_values(attribute)
            else:
                updated_attr = attribute
                updated_values = neo.get_values(attribute)

        elif "add_values" in plan:
            for val in plan["add_values"]:
                neo.add_value(attribute, val)
            updated_attr = attribute
            updated_values = neo.get_values(attribute)

        elif "remove_values" in plan:
            for val in plan["remove_values"]:
                neo.remove_value(attribute, val)
            updated_attr = attribute
            updated_values = neo.get_values(attribute)

        elif "merge_with_attributes" in plan and "rename_attribute_to" in plan:
            merge_list = plan["merge_with_attributes"]
            new_name = plan["rename_attribute_to"]
            neo.merge_attributes(merge_list, new_name)
            updated_attr = new_name
            updated_values = neo.get_values(new_name)

        else:
            updated_attr = attribute
            updated_values = neo.get_values(attribute)

        neo.close()

        # 5️⃣ Return updated info to frontend
        return jsonify({
            "status": "success",
            "updated_context": {
                "attribute": updated_attr,
                "values": updated_values
            }
        }), 200

    except Exception as e:
        print(f"❌ Error in refine_graph: {e}")
        return jsonify({"error": str(e)}), 500




@app.route("/process_variant", methods=["POST"])
def process_variant():
    try:
        # 1️⃣ Receive uploaded Excel file
        file = request.files.get("file")
        if not file:
            return jsonify({"success": False, "error": "No file uploaded."}), 400

        # 2️⃣ Save uploaded file
        input_path = os.path.join(UPLOAD_DIR, file.filename)
        file.save(input_path)

        # 3️⃣ Run your variant analysis function
        output_path = run_variant_analysis(input_path, OUTPUT_DIR)

        # 4️⃣ Return success + filename
        return jsonify({
            "success": True,
            "filename": os.path.basename(output_path)
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True)

# ✅ New Route: Compare attributes between UI and Neo4j
@app.route("/compare/ui_vs_graph", methods=["POST"])
def compare_ui_vs_graph():
    """
    Input JSON: { "attributes": ["Billing", "License Type", "Region", ...] }
    Output JSON: which attributes are missing or extra in the Neo4j graph.
    """
    try:
        from graph.neo4j_builder import Neo4jBuilder

        ui_attrs = set(request.json.get("attributes", []))
        neo = Neo4jBuilder()

        with neo.driver.session() as session:
            res = session.run("MATCH (a:Attribute) RETURN a.name AS attr")
            graph_attrs = {r["attr"] for r in res}

        neo.close()

        missing_in_graph = sorted(ui_attrs - graph_attrs)
        extra_in_graph = sorted(graph_attrs - ui_attrs)

        return jsonify({
            "ui_count": len(ui_attrs),
            "graph_count": len(graph_attrs),
            "missing_in_graph": missing_in_graph,
            "extra_in_graph": extra_in_graph
        })

    except Exception as e:
        print(f"❌ Comparison error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/graph/aggregated", methods=["GET"])
def get_aggregated_from_graph():
    """Fetch the latest Attribute–Value table from Neo4j."""
    try:
        from graph.neo4j_builder import Neo4jBuilder
        neo = Neo4jBuilder()

        with neo.driver.session() as session:
            result = session.run("""
                MATCH (a:Attribute)-[:HAS_VALUE]->(v:Value)
                RETURN a.name AS attribute, collect(v.value) AS values
            """)

            rows = []
            attribute_map = {}
            for record in result:
                attribute = record["attribute"]
                values = record["values"]
                attribute_map[attribute] = values
                rows.append([attribute] + values)

            # Dynamically create column headers
            max_len = max((len(v) for v in attribute_map.values()), default=0)
            columns = ["Attribute"] + [f"Value{i+1}" for i in range(max_len)]

        neo.close()
        return jsonify({"columns": columns, "rows": rows}), 200

    except Exception as e:
        print(f"❌ Error fetching graph data: {e}")
        return jsonify({"error": str(e)}), 500





if __name__ == "__main__":
    app.run(debug=True, port=5000)
