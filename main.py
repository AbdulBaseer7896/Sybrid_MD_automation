


import os
import time
from PIL import Image
from io import BytesIO
import json
import re
from utilits.Groq import  extract_medical_data
from services.OCR_Service import extrict_Data_From_image_using_OCR
from services.PromptServices import system_prompt_for_Superbill_Report
from automation import run_automation
from datetime import datetime

# 📂 Set your image path here (must be local)
LOCAL_IMAGE_PATH = "D:\Sybrid\OCR\DataSet\image.png"  # Change this if your image is somewhere else

def extract_data_from_image(image_path):
    """Extract medical data from a single image file"""
    print(f"📂 Loading image from: {image_path}")
    image = Image.open(image_path)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # OCR
    print("🔍 Running OCR...")
    # ocr_response = extrict_Data_From_image_using_OCR(image_path)
    ocr_text, ocr_time = extrict_Data_From_image_using_OCR(image_path)
    # document_text = ocr_response.pages[0].markdown
    print("✅ OCR complete", ocr_text)

    # LLM extraction
    print("🧠 Running LLM...")
    # llm = GroqLLM(api_key="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")
    data = extract_medical_data(ocr_text , system_prompt_for_Superbill_Report)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"output_{date_str}.json"

    # Save to JSON file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"📁 Data saved to: {filename}")
    print("✅ LLM extraction complete" , data) 

    if 'error' in data:
        raise Exception(f"LLM Extraction Error: {data['error']}")

    print("✅ LLM extraction complete")
    return data

def clean_llm_json_response(response: str) -> dict:
    # Remove ```json or ``` from start/end
    cleaned = re.sub(r"^```json\s*|```$", "", response.strip(), flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse cleaned JSON:", e)
        print("💬 Cleaned response was:", cleaned)
        raise


def run():
    overall_start = time.time()
    print("📸 Starting OCR + LLM extraction pipeline...\n")

    # 1️⃣ OCR + LLM Extraction
    start = time.time()
    response = extract_data_from_image(LOCAL_IMAGE_PATH)
    end = time.time()
    print("🧾 Raw LLM response:\n", response)
    print(f"⏱️ OCR + LLM extraction time: {end - start:.2f} seconds\n")

    # 2️⃣ JSON Cleaning + Saving
    try:
        start = time.time()
        data = clean_llm_json_response(response)
        output_file = "extracted_data.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        end = time.time()
        print(f"📁 JSON saved to: {os.path.abspath(output_file)}")
        print(f"⏱️ JSON cleaning & saving time: {end - start:.2f} seconds\n")
    except json.JSONDecodeError as e:
        print("❌ Failed to clean/parse LLM response.")
        print("🧾 Raw response was:", response)
        exit(1)

    # 3️⃣ Automation
    print("🔄 Starting automation...\n")
    start = time.time()
    run_automation(data)
    end = time.time()
    print(f"⏱️ Automation completed in: {end - start:.2f} seconds")

    # 4️⃣ Total time
    overall_end = time.time()
    total_time = overall_end - overall_start
    print(f"\n✅ All steps completed.")
    print(f"⏱️ Total pipeline time: {total_time:.2f} seconds")

if __name__ == "__main__":
    run()
