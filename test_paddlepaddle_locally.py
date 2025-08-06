

import time
from paddleocr import PaddleOCR

# Start timer
start_time = time.time()
ocr = PaddleOCR(lang="en")
result = ocr.predict(r"D:\Sybrid\OCR\DataSet\image.png")
# End timer
end_time = time.time()
elapsed_time = end_time - start_time

# Extract and display text only
texts = result[0]['rec_texts']
raw_text = "\n".join(texts)

# Output
print("\n📝 Raw OCR Text:\n", raw_text)
print(f"\n⏱️ Time taken: {elapsed_time:.2f} seconds")
