# import os
# import re
# import pandas as pd
# import pdfplumber
# from collections import defaultdict
# import ollama

# model_name = "mistral"
# MAX_CHARS_PER_CHUNK = 3000

# def process_pdf_with_mistral(filepath):
#     def extract_text_from_pdf(pdf_file):
#         text = ""
#         with pdfplumber.open(pdf_file) as pdf:
#             for page in pdf.pages:
#                 tables = page.extract_tables() or []
#                 for table in tables:
#                     for row in table:
#                         if row:
#                             text += " | ".join([str(cell).strip() for cell in row if cell]) + "\n"
#                 page_text = page.extract_text()
#                 if page_text:
#                     text += page_text + "\n"
#         cleaned_text = re.sub(r'\s+', ' ', text).strip()
#         return cleaned_text

#     def chunk_text(text, max_chars=MAX_CHARS_PER_CHUNK):
#         chunks = []
#         while len(text) > 0:
#             chunk = text[:max_chars]
#             split_pos = max(chunk.rfind("."), chunk.rfind("\n"))
#             if split_pos > 100:
#                 chunk = chunk[:split_pos + 1]
#             chunks.append(chunk.strip())
#             text = text[len(chunk):].strip()
#         return chunks

#     def extract_attributes(text_chunk):
#         if not text_chunk.strip():
#             return ""
#         prompt = f"""
#         You are an expert analyst. Extract attributes and their possible values:
#         {text_chunk}
#         """
#         try:
#             response = ollama.chat(
#                 model=model_name,
#                 messages=[{'role': 'user', 'content': prompt}]
#             )
#             return response["message"]["content"].strip()
#         except Exception as e:
#             return ""

#     def parse_attributes(text):
#         attr_dict = defaultdict(list)
#         lines = re.split(r'[\n;]', text)
#         for line in lines:
#             line = line.strip()
#             if not line:
#                 continue
#             parts = re.split(r'(?<!\w)=(?!\w)', line)
#             if len(parts) >= 2:
#                 attr = parts[0].strip()
#                 values = [v.strip() for v in re.split(r"[;,|]", parts[1]) if v.strip()]
#                 attr_dict[attr].extend(values)
#         return attr_dict

#     def merge_attributes(list_of_dicts):
#         merged = defaultdict(list)
#         for d in list_of_dicts:
#             for attr, vals in d.items():
#                 merged[attr].extend(vals)
#         for attr in merged:
#             merged[attr] = list(dict.fromkeys(merged[attr]))
#         return merged

#     pdf_text = extract_text_from_pdf(filepath)
#     chunks = chunk_text(pdf_text)
#     all_attrs = []
#     for chunk in chunks:
#         raw_output = extract_attributes(chunk)
#         attr_dict = parse_attributes(raw_output)
#         all_attrs.append(attr_dict)

#     merged_attr = merge_attributes(all_attrs)
#     if not merged_attr:
#         return {"columns": ["Attribute", "Value1"], "rows": []}

#     rows = []
#     max_values = max(len(vals) for vals in merged_attr.values())
#     columns = ["Attribute"] + [f"Value{i+1}" for i in range(max_values)]

#     for attr, vals in merged_attr.items():
#         row = [attr] + vals + [""] * (max_values - len(vals))
#         rows.append(row)

#     return {"columns": columns, "rows": rows}





import os
import re
import pandas as pd
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from collections import defaultdict
import ollama

# ----------------------------
# CONFIGURATION
# ----------------------------
pdf_path = "Invicto2.pdf"       # Change this to your PDF
output_path = "mistral_cleaned_attributes1.csv"
model_name = "mistral"
MAX_CHARS_PER_CHUNK = 3000
POPPLER_PATH = r"C:\Users\chetu\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"   # 🧠 Change this to your Poppler path (Windows only)

# ----------------------------
# 1️⃣ SAFE PDF TEXT EXTRACTION (with OCR fallback)
# ----------------------------
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    tables = page.extract_tables() or []
                    for table in tables:
                        for row in table:
                            if row:
                                text += " | ".join([str(cell).strip() for cell in row if cell]) + "\n"

                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        print(f"⚠️ No text found on page {page_num}")
                except Exception as e:
                    print(f"⚠️ Error reading page {page_num}: {e}")
    except Exception as e:
        print(f"❌ Failed to open PDF with pdfplumber: {e}")

    cleaned_text = re.sub(r'\s+', ' ', text).strip()

    # 🧠 OCR fallback if no text extracted
    if not cleaned_text:
        print("🧾 Running OCR (scanned or image-based PDF detected)...")
        try:
            images = convert_from_path(pdf_file, poppler_path=POPPLER_PATH)
            ocr_text = ""
            for i, image in enumerate(images):
                print(f"🖼️ Processing page {i+1}/{len(images)} for OCR...")

                # Enhance image for better OCR
                img = image.convert("L")  # grayscale
                img = img.filter(ImageFilter.MedianFilter())
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2)
                img = img.point(lambda x: 0 if x < 140 else 255, '1')  # thresholding

                # Perform OCR
                ocr_page_text = pytesseract.image_to_string(img, lang='eng')
                ocr_text += ocr_page_text + "\n"

            cleaned_text = re.sub(r'\s+', ' ', ocr_text).strip()

            if cleaned_text:
                print("✅ OCR extraction successful.")
            else:
                print("⚠️ OCR could not extract readable text.")
        except Exception as e:
            print(f"❌ OCR error: {e}")

    if not cleaned_text:
        print("⚠️ No extractable text found in this PDF after OCR.")
    return cleaned_text


# ----------------------------
# 2️⃣ SPLIT TEXT INTO CHUNKS
# ----------------------------
def chunk_text(text, max_chars=MAX_CHARS_PER_CHUNK):
    if not text:
        return []
    chunks = []
    while len(text) > 0:
        chunk = text[:max_chars]
        split_pos = max(chunk.rfind("."), chunk.rfind("\n"))
        if split_pos > 100:
            chunk = chunk[:split_pos + 1]
        chunks.append(chunk.strip())
        text = text[len(chunk):].strip()
    return chunks


# ----------------------------
# 3️⃣ MISTRAL ATTRIBUTE EXTRACTION
# ----------------------------
def extract_attributes(text_chunk):
    if not text_chunk.strip():
        return ""
    prompt = f"""
You are a senior automotive product intelligence analyst. Your task is to analyze the following brochure text and extract all meaningful, structured product attributes and their possible values.

The text may contain descriptive marketing content, variant details, specifications, and feature highlights. Ignore all marketing or aesthetic language, and focus only on factual, technical, or categorical information that defines the product.

Your objective is to produce a clean, structured list of attributes and their corresponding values that describe the vehicle comprehensively.

Follow these detailed instructions:

1. **Output format (strictly follow this):**
   Attribute = Value1, Value2, Value3

   Example:
   Fuel Type = Petrol, Diesel, CNG, Hybrid
   Transmission = Manual, Automatic, e-CVT
   Color Options = Silver, White, Black, Blue

2. **Include only meaningful product attributes** related to:
   - **Engine & Performance:** Engine Type, Displacement, Power, Torque, Transmission Type, Drivetrain, Fuel Type, Hybrid System Type, Driving Modes, Battery Capacity, Motor Power, Mileage, Emission Standard.
   - **Dimensions & Weight:** Length, Width, Height, Wheelbase, Ground Clearance, Boot Space, Turning Radius, Kerb Weight.
   - **Exterior Features:** Headlamp Type, DRLs, Fog Lamps, Roof Rails, Alloy Wheel Size, Tyre Size, Tail Lamp Type, Door Handles, Paint Options.
   - **Interior & Comfort:** Seat Material, Upholstery Color, Seat Configuration (e.g., 6-seater / 7-seater), Infotainment Screen Size, Ambient Lighting, Steering Controls, Climate Control Type, Cruise Control, Keyless Entry, Start/Stop Button, AC Type, Sunroof Type.
   - **Safety & Driver Assistance:** Airbags, ABS, EBD, ESP, Hill Hold Assist, ADAS, Traction Control, ISOFIX, Parking Sensors, Camera Type, Speed Alert System, Immobilizer.
   - **Connectivity & Infotainment:** Touchscreen Display Size, Speaker Count, Audio System Brand, Android Auto / Apple CarPlay Support, USB Ports, Wireless Charging, Connected Car Features.
   - **Variants & Trims:** Variant Names, Edition, Transmission Options, Seating Layouts, Trim Levels, Special Editions.
   - **Electrical / Hybrid Attributes (for HEV/EV models):** Motor Type, Hybrid Type (Mild / Strong / Plug-in), Battery Capacity, Battery Type, Regenerative Braking, Drive Modes, EV Range, Charging Type, Charging Time.
   - **Warranty & Maintenance:** Standard Warranty, Extended Warranty, Service Interval, Roadside Assistance.
   - **Price & Launch:** Launch Year, Ex-Showroom Price, On-Road Price, Booking Amount (if mentioned).

3. **Normalization Rules:**
   - Expand abbreviations (e.g., MT → Manual Transmission, AT → Automatic Transmission, CVT → Continuously Variable Transmission).
   - Normalize unit expressions (e.g., “2L” → “2.0L”, “bhp” → “BHP”).
   - Combine all unique values of the same attribute across variants into one line.
   - Remove duplicates, special characters, or promotional phrases.
   - Do not include sentences, bullet points, or marketing slogans.
   - Focus only on measurable or categorical specifications.

4. **Your output should be clear and concise.**  
   Each attribute must appear only once with all its possible values.

5. **If multiple trims or variants are mentioned, combine their differing values.**  
   Example:
   Transmission = Manual, Automatic, e-CVT
   Seat Configuration = 6-seater, 7-seater

6. **If some attribute values are unclear or partially stated, infer meaning from nearby text context (e.g., “Smart Hybrid Technology” → Hybrid Type = Strong Hybrid).**

Now, analyze the following extracted brochure text carefully and output the structured attributes in the required format.




Output format:
Attribute = Value1, Value2, Value3

Example:
Fuel Type = Petrol, Diesel, CNG, Electric
Transmission = Manual, Automatic
Color = Red, Blue, White 

Text:
{text_chunk}
"""
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ Mistral error: {e}")
        return ""


# ----------------------------
# 4️⃣ PARSE ATTRIBUTES CLEANLY
# ----------------------------
def parse_attributes(text):
    attr_dict = defaultdict(list)
    if not text:
        return attr_dict
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


# ----------------------------
# 5️⃣ MERGE MULTIPLE CHUNKS
# ----------------------------
def merge_attributes(list_of_dicts):
    merged = defaultdict(list)
    for d in list_of_dicts:
        for attr, vals in d.items():
            merged[attr].extend(vals)
    for attr in merged:
        merged[attr] = list(dict.fromkeys(merged[attr]))  # Remove duplicates
    return merged


# ----------------------------
# 6️⃣ MAIN EXECUTION
# ----------------------------
print("📘 Extracting text from PDF...")
pdf_text = extract_text_from_pdf(pdf_path)

if not pdf_text:
    print("❌ No readable content found in PDF. Please use a text-based or OCR-readable PDF.")
    exit()

print("📝 Splitting text into chunks...")
chunks = chunk_text(pdf_text)

print(f"🔍 Extracting attributes using Mistral... ({len(chunks)} chunks found)")
all_attrs = []
for i, chunk in enumerate(chunks, 1):
    print(f"→ Processing chunk {i}/{len(chunks)}...")
    raw_output = extract_attributes(chunk)
    attr_dict = parse_attributes(raw_output)
    all_attrs.append(attr_dict)

merged_attr = merge_attributes(all_attrs)

# ----------------------------
# 7️⃣ STRUCTURED CSV OUTPUT
# ----------------------------
if not merged_attr:
    print("⚠️ No attributes found. Try a PDF with more structured data.")
else:
    rows = []
    max_values = max(len(vals) for vals in merged_attr.values())
    columns = ["Attribute"] + [f"Value{i+1}" for i in range(max_values)]

    for attr, vals in merged_attr.items():
        row = [attr] + vals + [""] * (max_values - len(vals))
        rows.append(row)

    output_df = pd.DataFrame(rows, columns=columns)
    output_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ Extraction complete! Saved to: {output_path}")
