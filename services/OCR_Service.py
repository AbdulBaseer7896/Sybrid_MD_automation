


import time
from paddleocr import PaddleOCR

# You can initialize this once and reuse if you call the function many times
ocr_engine = PaddleOCR(lang="en")

def extrict_Data_From_image_using_OCR(image_path: str) -> tuple[str, float]:
    """
    Run OCR on a given image and measure elapsed time.

    Args:
        image_path (str): Path to the input image.

    Returns:
        raw_text (str): The concatenated OCR result.
        elapsed_seconds (float): Total time from start to finish.
    """
    start = time.time()
    result = ocr_engine.predict(image_path)
    end = time.time()

    # Extract plain text
    texts = result[0]['rec_texts']
    raw_text = "\n".join(texts)

    return raw_text, end - start

# # Example usage:
# if __name__ == "__main__":
#     img = r"D:\Sybrid\OCR\DataSet\image.png"
#     text, secs = extrict_Data_From_image_using_OCR(img)
#     print("📝 OCR Result:\n", text)
#     print(f"⏱️ Time taken: {secs:.2f} seconds")
