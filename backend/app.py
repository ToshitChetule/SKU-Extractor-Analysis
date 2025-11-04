

# from flask import Flask, request, jsonify
# import os
# from flask_cors import CORS
# from models.llama_excel import process_excel_with_llama
# from models.mistral_pdf import process_pdf_with_mistral
# from graph.neo4j_builder import Neo4jBuilder  # 🧠 NEW IMPORT
# import pandas as pd

# app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# # 🧠 Domain-specific prompt generator
# def get_domain_prompt(industry, product_type):
#     base_prompt = f"""
#     # Instructions for the Model

#     You are processing SKU descriptions at scale. Extract attributes and values that are clearly stated or strongly implied.
#     Normalize abbreviations, shorthand, and codes into human-readable attributes and values.
#     Merge duplicate attributes (textual variants or semantic duplicates) into a single attribute using a consistent Title Case name.
#     Prioritize commercial, monetization, and marketing attributes when present.

#     ### CONTEXT
#     Industry: {industry if industry else "general"}
#     Product Type: {product_type if product_type else "unspecified"}
#     """

#     domain_prompts = {
#         "automotive": """
#         Focus on vehicle specifications:
#         - Make, Model, Trim, Year
#         - Engine details, Power (HP), Torque (Nm), Transmission
#         - Fuel type, Tank capacity, Mileage
#         - Dimensions, Weight, Ground clearance
#         - Compatibility and Part number
#         """,
#         "pharmaceuticals": """
#         Focus on:
#         - Brand and Generic Name
#         - Strength (mg/ml)
#         - Dosage Form (Tablet, Capsule, Syrup)
#         - Ingredients, Packaging type, Quantity
#         - Manufacturer, Expiry date, Batch/Lot, Therapeutic category
#         """,
#         "electronics": """
#         Focus on:
#         - Brand, Model number, Series
#         - Power, Voltage, Frequency, Capacity (GB/TB)
#         - Battery, Display size, Resolution
#         - Connectivity (Wi-Fi, Bluetooth, HDMI)
#         - Warranty, Material, Weight, Dimensions
#         """,
#         "food_beverages": """
#         Focus on:
#         - Product name, Brand
#         - Ingredients, Nutritional values
#         - Net weight/volume, Flavor
#         - Packaging type/material, Shelf life
#         - Manufacturer, Country of origin
#         """,
#         "chemical": """
#         Focus on:
#         - Chemical name, Formula, Purity, CAS number
#         - Physical form, Molecular weight, Boiling/Melting point
#         - Applications, Packaging, Safety classification
#         """
#     }

#     if industry and industry.lower() in domain_prompts:
#         base_prompt += domain_prompts[industry.lower()]
#     else:
#         base_prompt += "\nExtract all relevant descriptive and technical attributes clearly."

#     return base_prompt


# # 🧾 File processing route
# @app.route("/process", methods=["POST"])
# def process_file():
#     """
#     Handles Excel upload and processes each SKU row individually.
#     Supports multiple values per attribute and dynamically expands columns.
#     """
#     if "file" not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400

#     file = request.files["file"]
#     filename = file.filename
#     if not filename:
#         return jsonify({"error": "Invalid filename"}), 400

#     # 🧠 Extract user context
#     industry = request.form.get("industry", "general")
#     product_type = request.form.get("productType", "")
#     domain_prompt = get_domain_prompt(industry, product_type)

#     filepath = os.path.join(UPLOAD_FOLDER, filename)
#     file.save(filepath)

#     ext = os.path.splitext(filename)[1].lower()
#     print(f"\n📂 Received file: {filename} ({ext})")

#     try:
#         # ✅ Handle Excel
#         if ext in [".xlsx", ".xls"]:
#             import time
#             from models.llama_excel import process_excel_row_with_llama

#             df = pd.read_excel(filepath)
#             if "SKU_Description" not in df.columns:
#                 return jsonify({"error": "Missing 'SKU_Description' column in Excel."}), 400

#             total_rows = len(df)
#             print(f"🚀 Processing {total_rows} SKU rows using LLaMA...\n")

#             # Collect attributes (multi-value per attribute)
#             attribute_map = {}

#             for i, row in df.iterrows():
#                 sku_text = str(row["SKU_Description"]).strip()
#                 if not sku_text:
#                     continue

#                 print(f"🧠 Processing row {i + 1}/{total_rows}: {sku_text[:100]}...")
#                 extracted_pairs = process_excel_row_with_llama(sku_text, domain_prompt)

#                 # Merge multi-values per attribute
#                 for attr, val in extracted_pairs:
#                     if attr not in attribute_map:
#                         attribute_map[attr] = set()
#                     for v in str(val).split(","):
#                         clean_val = v.strip()
#                         if clean_val:
#                             attribute_map[attr].add(clean_val)

#                 time.sleep(0.5)  # simulate model latency per SKU

#             # Build final table
#             max_values = max(len(vals) for vals in attribute_map.values()) if attribute_map else 0
#             columns = ["Attribute"] + [f"Value{i + 1}" for i in range(max_values)]

#             rows = []
#             for attr, vals in attribute_map.items():
#                 val_list = list(vals)
#                 val_list += [""] * (max_values - len(val_list))
#                 rows.append([attr] + val_list)

#             print("\n✅ Row-by-row Excel processing complete with multi-value support.\n")

#             # 🕸️ STEP: Push extracted attributes into Neo4j Knowledge Graph
#             try:
#                 print("📡 Connecting to Neo4j for Knowledge Graph update...")
#                 neo = Neo4jBuilder()
#                 neo.add_attribute_value_pairs(attribute_map)
#                 neo.close()
#                 print("✅ Knowledge Graph successfully updated with extracted data.\n")
#             except Exception as graph_error:
#                 print(f"⚠️ Neo4j update skipped due to error: {graph_error}")

#             return jsonify({
#                 "columns": columns,
#                 "rows": rows,
#                 "model_used": "LLaMA",
#                 "industry": industry,
#                 "product_type": product_type
#             })

#         # ✅ Handle PDF
#         elif ext == ".pdf":
#             print("🚀 Running PDF extraction using Mistral model...\n")
#             result = process_pdf_with_mistral(filepath, domain_prompt)

#             return jsonify({
#                 "columns": result.get("columns", []),
#                 "rows": result.get("rows", []),
#                 "model_used": "Mistral",
#                 "industry": industry,
#                 "product_type": product_type
#             })

#         else:
#             return jsonify({"error": f"Unsupported file type: {ext}"}), 400

#     except Exception as e:
#         print(f"❌ Error during processing: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# # 🧠 Refinement route (UI exists but not functional yet)
# @app.route("/refine", methods=["POST", "OPTIONS"])
# def refine_attributes():
#     if request.method == "OPTIONS":
#         return jsonify({"status": "OK"}), 200

#     try:
#         data = request.get_json()
#         selected_rows = data.get("selectedRows")
#         full_table = data.get("fullTable")
#         chat_history = data.get("chatHistory")

#         if not selected_rows or not chat_history:
#             return jsonify({"error": "Missing selectedRows or chatHistory"}), 400

#         from models.llama_excel import refine_with_llama
#         refined_rows = refine_with_llama(selected_rows, chat_history, full_table)
#         return jsonify({"rows": refined_rows}), 200

#     except Exception as e:
#         print(f"❌ Refinement error: {e}")
#         return jsonify({"error": str(e)}), 500


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)



from flask import Flask, request, jsonify, send_file
import os
from flask_cors import CORS
import pandas as pd
from variant_analysis import run_variant_analysis

# 🧠 Imports
from models.llama_excel import process_excel_row_with_llama
from models.mistral_pdf import process_pdf_with_mistral
from graph.neo4j_builder import Neo4jBuilder  # optional but kept for your KG logic

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
            try:
                print("📡 Connecting to Neo4j for Knowledge Graph update...")
                neo = Neo4jBuilder()
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
                "model_used": "LLaMA",
                "industry": industry,
                "product_type": product_type
            })

        # ✅ PDF Processing
        elif ext == ".pdf":
            print("🚀 Running PDF extraction using Mistral model...\n")
            result = process_pdf_with_mistral(filepath, domain_prompt)

            return jsonify({
                "sku_matrix": [],
                "aggregated_matrix": {
                    "columns": result.get("columns", []),
                    "rows": result.get("rows", [])
                },
                "model_used": "Mistral",
                "industry": industry,
                "product_type": product_type
            })

        else:
            return jsonify({"error": f"Unsupported file type: {ext}"}), 400

    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        return jsonify({"error": str(e)}), 500


# 🧠 Attribute Refinement Endpoint (future use)
@app.route("/refine", methods=["POST", "OPTIONS"])
def refine_attributes():
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    try:
        data = request.get_json()
        selected_rows = data.get("selectedRows")
        full_table = data.get("fullTable")
        chat_history = data.get("chatHistory")

        if not selected_rows or not chat_history:
            return jsonify({"error": "Missing selectedRows or chatHistory"}), 400

        from models.llama_excel import refine_with_llama
        refined_rows = refine_with_llama(selected_rows, chat_history, full_table)
        return jsonify({"rows": refined_rows}), 200

    except Exception as e:
        print(f"❌ Refinement error: {e}")
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
