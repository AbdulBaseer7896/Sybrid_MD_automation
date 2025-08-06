

import requests
from typing import List, Dict
import time

def extract_medical_data(
    ocr_text,
    system_prompt: str = "You are a helpful assistant.",
    # model: str = "google/gemma-3-12b",
    # model: str = "google/gemma-3-1b",
    model: str = "bartowski/google_gemma-3-4b-it-GGUF",
    temperature: float = 0.7,
    endpoint: str = "http://localhost:1234/v1/chat/completions"
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": ocr_text},
        # {"role": "user", "content": prompt},
    ]
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    resp = requests.post(endpoint, json=payload)

    if resp.status_code == 200:
        content = resp.json()["choices"][0]["message"]["content"]
        print("🧠 Raw model output:\n", content)
        return content
    else:
        raise RuntimeError(f"Error {resp.status_code}: {resp.text}")



# # Example usage:
# if __name__ == "__main__":
#     system_prompt = "You are an AI assistant that cleans and summarizes OCR output."
#     ocr_text = "Raw OCR text here..."
#     question = "Please correct errors and summarize key points."
#     start = time.time()
#     answer = extract_medical_data(ocr_text, question, system_prompt)
#     end = time.time()
#     print("AI:", answer)
#     print(f"⏱ Elapsed time: {end - start:.2f} seconds")
