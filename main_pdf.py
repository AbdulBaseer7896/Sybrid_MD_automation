


# import os
# import time
# from PIL import Image
# from io import BytesIO
# import json
# import re
# from utilits.Groq import  extract_medical_data
# from services.OCR_Service import extrict_Data_From_image_using_OCR
# from services.PromptServices import system_prompt_for_Superbill_Report
# from automation import run_automation
# from datetime import datetime
# from pdf2image import convert_from_path
# from dotenv import load_dotenv


# load_dotenv()
# # 📂 Set your image path here (must be local)
# LOCAL_IMAGE_PATH = "D:\Sybrid\OCR\DataSet\SuperBills.pdf"  # Change this if your image is somewhere else

# def clean_llm_json_response(response: str) -> dict:
#     # Remove ```json or ``` from start/end
#     cleaned = re.sub(r"^```json\s*|```$", "", response.strip(), flags=re.IGNORECASE).strip()
#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError as e:
#         print("❌ Failed to parse cleaned JSON:", e)
#         print("💬 Cleaned response was:", cleaned)
#         raise


# def extract_data_from_image(image_path):
#     """Extract medical data from a single image file"""
#     print(f"📂 Loading image from: {image_path}")
#     image = Image.open(image_path)

#     buffer = BytesIO()
#     image.save(buffer, format="PNG")
#     buffer.seek(0)

#     # OCR
#     print("🔍 Running OCR...")
#     # ocr_response = extrict_Data_From_image_using_OCR(image_path)
#     ocr_text, ocr_time = extrict_Data_From_image_using_OCR(image_path)
#     # document_text = ocr_response.pages[0].markdown
#     print("✅ OCR complete", ocr_text)
#     print(f"🕒 OCR took {ocr_time:.2f}s")

#     # LLM extraction
#     print("🧠 Running LLM...")

#     llm_timing_start = time.time()
#     raw = extract_medical_data(ocr_text , system_prompt_for_Superbill_Report)
#     llm_timing_end = time.time()

#     print(f"🕒 LLM extraction took {llm_timing_end - llm_timing_start:.2f}s")
#     data = clean_llm_json_response(raw)

#     print("✅ LLM extraction complete")
#     return data




# def run():
#     overall_start = time.time()
#     print("📸 Starting OCR + LLM extraction pipeline...\n")

#     # 1) Load PDF → PIL pages or single image
#     if LOCAL_IMAGE_PATH.lower().endswith(".pdf"):
#         pil_pages = convert_from_path(
#             LOCAL_IMAGE_PATH, dpi=300, first_page=1, last_page=2
#         )
#         print(f"📄 PDF loaded — converted pages: {len(pil_pages)}")
#     else:
#         pil_pages = [Image.open(LOCAL_IMAGE_PATH)]

#     all_results = []

#     for idx, img in enumerate(pil_pages, start=1):
#         tmp_path = f"_tmp_page{idx}.png"
#         try:
#             # write out the page so your OCR function can open it
#             buf = BytesIO()
#             img.save(buf, format="PNG")
#             buf.seek(0)
#             with open(tmp_path, "wb") as f:
#                 f.write(buf.read())

#             print(f"\n▶️ Processing page {idx}")
#             # 2) Run OCR + LLM
#             ocr_timming_start = time.time()
#             page_data = extract_data_from_image(tmp_path)
#             ocr_timming_end = time.time()

#             print(f"🕒 Page {idx} OCR + LLM took {ocr_timming_end - ocr_timming_start:.2f}s")
#             print(f"📊 Extracted data for page {idx}: {json.dumps(page_data, indent=2, ensure_ascii=False)}")

#             # 3) Immediately run your automation on that page
#             print(f"🔄 Running automation for page {idx}…")

#             time_run_automation_start = time.time()
#             run_automation(page_data)
#             time_run_automation_end = time.time()

#             print(f"🕒 Automation for page {idx} took {time_run_automation_end - time_run_automation_start:.2f}s")
#             print(f"✅ Page {idx} processed successfully!")

#             all_results.append({
#                 "page":    idx,
#                 "success": True,
#                 "data":    page_data
#             })

#         except Exception as e:
#             # catch ANY error (including vk::Queue errors)
#             err_msg = str(e).splitlines()[0]
#             print(f"❌ Error on page {idx}: {err_msg}")
#             all_results.append({
#                 "page":    idx,
#                 "success": False,
#                 "error":   err_msg
#             })

#         finally:
#             # always clean up the temp file
#             if os.path.exists(tmp_path):
#                 os.remove(tmp_path)

#     # 4) (Optional) Save combined results for record-keeping
#     output_file = f"multistage_output_{datetime.now():%Y%m%d_%H%M%S}.json"
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(all_results, f, indent=2, ensure_ascii=False)
#     print(f"\n📁 Final combined output saved to: {output_file}")

#     overall_end = time.time()
#     print(f"\n✅ All steps completed in {overall_end - overall_start:.2f}s")




# if __name__ == "__main__":
#     run()














# import os
# import time
# import csv
# import threading
# import psutil
# from datetime import datetime
# from PIL import Image
# from io import BytesIO
# import json
# import re
# from utilits.Groq import extract_medical_data
# from services.OCR_Service import extrict_Data_From_image_using_OCR
# from services.PromptServices import system_prompt_for_Superbill_Report
# from automation import run_automation
# from pdf2image import convert_from_path
# from dotenv import load_dotenv

# try:
#     import pynvml
#     HAS_GPU = True
# except ImportError:
#     HAS_GPU = False

# load_dotenv()
# PERF_CSV = "performance_metrics.csv"
# LOCAL_IMAGE_PATH = "D:\\Sybrid\\OCR\\DataSet\\SuperBills.pdf"

# class ResourceMonitor:
#     def __init__(self):
#         self.samples = []
#         self.active = False
#         self.thread = None
#         self.start_time = None
#         self.end_time = None
#         self.gpu_available = HAS_GPU

#     def __enter__(self):
#         self.start_time = time.time()
#         self.active = True
#         self.samples = []
#         self.thread = threading.Thread(target=self._monitor)
#         self.thread.start()
#         return self

#     def _monitor(self):
#         while self.active:
#             cpu = psutil.cpu_percent(interval=0.1)
#             ram = psutil.virtual_memory().used / (1024 ** 2)  # MB
            
#             gpu_util = gpu_mem = None
#             if self.gpu_available and HAS_GPU:
#                 try:
#                     pynvml.nvmlInit()
#                     handle = pynvml.nvmlDeviceGetHandleByIndex(0)
#                     util = pynvml.nvmlDeviceGetUtilizationRates(handle)
#                     mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
#                     gpu_util = util.gpu
#                     gpu_mem = mem.used / (1024 ** 2)  # MB
#                 except pynvml.NVMLError:
#                     self.gpu_available = False
            
#             self.samples.append((cpu, ram, gpu_util, gpu_mem))

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.active = False
#         if self.thread and self.thread.is_alive():
#             self.thread.join(timeout=1.0)
#         self.end_time = time.time()
#         if HAS_GPU:
#             try:
#                 pynvml.nvmlShutdown()
#             except:
#                 pass
#         return False

#     def get_duration(self):
#         return self.end_time - self.start_time if self.end_time else 0

#     def get_avg_cpu(self):
#         return self._avg(0) if self.samples else 0

#     def get_avg_ram(self):
#         return self._avg(1) if self.samples else 0

#     def get_avg_gpu_util(self):
#         return self._avg(2, filter_none=True)

#     def get_avg_gpu_mem(self):
#         return self._avg(3, filter_none=True)

#     def _avg(self, idx, filter_none=False):
#         vals = [s[idx] for s in self.samples]
#         if filter_none:
#             vals = [v for v in vals if v is not None]
#         return sum(vals) / len(vals) if vals else 0

# def log_performance(stage_data):
#     headers = [
#         'run_timestamp', 'page', 'stage', 'start_time', 'end_time', 'duration',
#         'cpu_avg', 'ram_avg', 'gpu_util_avg', 'gpu_mem_avg'
#     ]
#     file_exists = os.path.isfile(PERF_CSV)
    
#     with open(PERF_CSV, 'a', newline='') as f:
#         writer = csv.DictWriter(f, fieldnames=headers)
#         if not file_exists:
#             writer.writeheader()
#         writer.writerow(stage_data)

# def run_ocr(image_path):
#     return extrict_Data_From_image_using_OCR(image_path)

# def run_llm(ocr_text):
#     raw = extract_medical_data(ocr_text, system_prompt_for_Superbill_Report)
#     return clean_llm_json_response(raw)

# def clean_llm_json_response(response: str) -> dict:
#     cleaned = re.sub(r"^```json\s*|```$", "", response.strip(), flags=re.IGNORECASE).strip()
#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError as e:
#         print(f"❌ JSON Error: {e}\n💬 Response: {cleaned}")
#         raise

# def run():
#     run_timestamp = datetime.now().isoformat()
#     print("📊 Starting performance monitoring...")
    
#     with ResourceMonitor() as overall_monitor:
#         print("📸 Starting OCR + LLM pipeline...\n")
#         start_time = time.time()

#         if LOCAL_IMAGE_PATH.lower().endswith(".pdf"):
#             pil_pages = convert_from_path(LOCAL_IMAGE_PATH, dpi=300, first_page=1, last_page=2)
#             print(f"📄 Converted PDF pages: {len(pil_pages)}")
#         else:
#             pil_pages = [Image.open(LOCAL_IMAGE_PATH)]

#         all_results = []
#         for idx, img in enumerate(pil_pages, start=1):
#             tmp_path = f"_tmp_page{idx}.png"
#             try:
#                 img.save(tmp_path, "PNG")
#                 print(f"\n▶️ Processing Page {idx}")

#                 # OCR Stage
#                 with ResourceMonitor() as monitor:
#                     ocr_text, _ = run_ocr(tmp_path)
#                 log_performance({
#                     'run_timestamp': run_timestamp,
#                     'page': idx,
#                     'stage': 'OCR',
#                     'start_time': datetime.fromtimestamp(monitor.start_time).isoformat(),
#                     'end_time': datetime.fromtimestamp(monitor.end_time).isoformat(),
#                     'duration': monitor.get_duration(),
#                     'cpu_avg': monitor.get_avg_cpu(),
#                     'ram_avg': monitor.get_avg_ram(),
#                     'gpu_util_avg': monitor.get_avg_gpu_util(),
#                     'gpu_mem_avg': monitor.get_avg_gpu_mem()
#                 })

#                 # LLM Stage
#                 with ResourceMonitor() as monitor:
#                     page_data = run_llm(ocr_text)
#                 log_performance({
#                     'run_timestamp': run_timestamp,
#                     'page': idx,
#                     'stage': 'LLM',
#                     'start_time': datetime.fromtimestamp(monitor.start_time).isoformat(),
#                     'end_time': datetime.fromtimestamp(monitor.end_time).isoformat(),
#                     'duration': monitor.get_duration(),
#                     'cpu_avg': monitor.get_avg_cpu(),
#                     'ram_avg': monitor.get_avg_ram(),
#                     'gpu_util_avg': monitor.get_avg_gpu_util(),
#                     'gpu_mem_avg': monitor.get_avg_gpu_mem()
#                 })

#                 # Automation Stage
#                 with ResourceMonitor() as monitor:
#                     run_automation(page_data)
#                 log_performance({
#                     'run_timestamp': run_timestamp,
#                     'page': idx,
#                     'stage': 'Automation',
#                     'start_time': datetime.fromtimestamp(monitor.start_time).isoformat(),
#                     'end_time': datetime.fromtimestamp(monitor.end_time).isoformat(),
#                     'duration': monitor.get_duration(),
#                     'cpu_avg': monitor.get_avg_cpu(),
#                     'ram_avg': monitor.get_avg_ram(),
#                     'gpu_util_avg': monitor.get_avg_gpu_util(),
#                     'gpu_mem_avg': monitor.get_avg_gpu_mem()
#                 })

#                 all_results.append({'page': idx, 'success': True, 'data': page_data})
#                 print(f"✅ Page {idx} processed")

#             except Exception as e:
#                 all_results.append({'page': idx, 'success': False, 'error': str(e)})
#                 print(f"❌ Page {idx} error: {str(e)}")
#             finally:
#                 if os.path.exists(tmp_path):
#                     os.remove(tmp_path)

#         # Save results
#         output_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
#         with open(output_file, 'w') as f:
#             json.dump(all_results, f, indent=2)
#         print(f"💾 Results saved to {output_file}")

#         # Log overall performance
#         log_performance({
#             'run_timestamp': run_timestamp,
#             'page': 'All',
#             'stage': 'TOTAL',
#             'start_time': datetime.fromtimestamp(overall_monitor.start_time).isoformat(),
#             'end_time': datetime.fromtimestamp(overall_monitor.end_time).isoformat(),
#             'duration': overall_monitor.get_duration(),
#             'cpu_avg': overall_monitor.get_avg_cpu(),
#             'ram_avg': overall_monitor.get_avg_ram(),
#             'gpu_util_avg': overall_monitor.get_avg_gpu_util(),
#             'gpu_mem_avg': overall_monitor.get_avg_gpu_mem()
#         })

#     print(f"\n✅ All processes completed in {time.time() - start_time:.2f}s")
#     print(f"📈 Performance metrics saved to {PERF_CSV}")

# if __name__ == "__main__":
#     run()












import os
import time
import csv
import threading
import psutil
from datetime import datetime
from PIL import Image
from io import BytesIO
import json
import re
from utilits.Groq import extract_medical_data
from services.OCR_Service import extrict_Data_From_image_using_OCR
from services.PromptServices import system_prompt_for_Superbill_Report
from automation import run_automation
from pdf2image import convert_from_path
from dotenv import load_dotenv

try:
    import pynvml
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

load_dotenv()
PERF_CSV = "performance_metrics.csv"
LOCAL_IMAGE_PATH = "D:\\Sybrid\\OCR\\DataSet\\SuperBills.pdf"

class ResourceMonitor:
    def __init__(self):
        self.samples = []
        self.active = False
        self.thread = None
        self.start_time = None
        self.end_time = None
        self.gpu_available = HAS_GPU

    def __enter__(self):
        self.start_time = time.time()
        self.active = True
        self.samples = []
        self.thread = threading.Thread(target=self._monitor)
        self.thread.start()
        return self

    def _monitor(self):
        while self.active:
            cpu = psutil.cpu_percent(interval=0.1)
            ram_mb = psutil.virtual_memory().used / (1024 ** 2)  # MB
            
            gpu_util = gpu_mem_mb = None
            if self.gpu_available and HAS_GPU:
                try:
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_util = util.gpu
                    gpu_mem_mb = mem.used / (1024 ** 2)  # MB
                except pynvml.NVMLError:
                    self.gpu_available = False
            
            self.samples.append((cpu, ram_mb, gpu_util, gpu_mem_mb))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.active = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.end_time = time.time()
        if HAS_GPU:
            try:
                pynvml.nvmlShutdown()
            except:
                pass
        return False

    def get_duration(self):
        return self.end_time - self.start_time if self.end_time else 0

    def get_avg_cpu(self):
        return self._avg(0) if self.samples else 0

    def get_avg_ram_mb(self):
        return self._avg(1) if self.samples else 0

    def get_avg_gpu_util(self):
        return self._avg(2, filter_none=True)

    def get_avg_gpu_mem_mb(self):
        return self._avg(3, filter_none=True)

    def _avg(self, idx, filter_none=False):
        vals = [s[idx] for s in self.samples]
        if filter_none:
            vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else 0

def log_performance(stage_data):
    headers = [
        'run_timestamp', 'page', 'stage', 'start_time', 'end_time', 'duration',
        'cpu_avg', 'ram_avg', 'ram_avg_GB', 'gpu_util_avg', 'gpu_mem_avg'
    ]
    
    # Add calculated fields
    stage_data['ram_avg_GB'] = round(stage_data.get('ram_avg', 0) / 1024, 2)
    stage_data['gpu_mem_avg'] = stage_data.get('gpu_mem_avg_mb', 0)
    
    # Ensure all required fields exist
    for field in headers:
        if field not in stage_data:
            stage_data[field] = 0
    
    file_exists = os.path.isfile(PERF_CSV)
    with open(PERF_CSV, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: v for k, v in stage_data.items() if k in headers})

def clean_llm_json_response(response: str) -> dict:
    cleaned = re.sub(r"^```json\s*|```$", "", response.strip(), flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}\n💬 Response: {cleaned}")
        raise

def run():
    run_timestamp = datetime.now().isoformat()
    print(f"🏁 Run started at: {run_timestamp}")
    
    # Create overall monitor first
    overall_monitor = ResourceMonitor()
    
    with overall_monitor:
        print("📊 Starting resource monitoring...")
        print("📸 Starting OCR + LLM pipeline...\n")
        start_time = time.time()

        # Convert PDF to images
        if LOCAL_IMAGE_PATH.lower().endswith(".pdf"):
            print(f"📄 Converting PDF: {LOCAL_IMAGE_PATH}")
            pil_pages = convert_from_path(LOCAL_IMAGE_PATH, dpi=300, first_page=3, last_page=6)
            print(f"🔄 Converted {len(pil_pages)} pages")
        else:
            pil_pages = [Image.open(LOCAL_IMAGE_PATH)]
            print(f"🖼️ Processing single image")

        all_results = []
        for idx, img in enumerate(pil_pages, start=1):
            tmp_path = f"_tmp_page{idx}.png"
            try:
                # Save temporary image
                img.save(tmp_path, "PNG")
                print(f"\n▶️ Starting Page {idx} processing")

                # OCR Stage
                print(f"🔍 Page {idx}: Starting OCR...")
                with ResourceMonitor() as monitor:
                    ocr_text, _ = extrict_Data_From_image_using_OCR(tmp_path)
                print(f"✅ Page {idx}: OCR completed in {monitor.get_duration():.2f}s")
                
                log_performance({
                    'run_timestamp': run_timestamp,
                    'page': idx,
                    'stage': 'OCR',
                    'start_time': datetime.fromtimestamp(monitor.start_time).isoformat(),
                    'end_time': datetime.fromtimestamp(monitor.end_time).isoformat(),
                    'duration': monitor.get_duration(),
                    'cpu_avg': monitor.get_avg_cpu(),
                    'ram_avg': monitor.get_avg_ram_mb(),
                    'gpu_util_avg': monitor.get_avg_gpu_util(),
                    'gpu_mem_avg_mb': monitor.get_avg_gpu_mem_mb()
                })

                # LLM Stage
                print(f"🧠 Page {idx}: Starting LLM processing...")
                with ResourceMonitor() as monitor:
                    raw = extract_medical_data(ocr_text, system_prompt_for_Superbill_Report)
                    page_data = clean_llm_json_response(raw)
                print(f"✅ Page {idx}: LLM completed in {monitor.get_duration():.2f}s")
                
                log_performance({
                    'run_timestamp': run_timestamp,
                    'page': idx,
                    'stage': 'LLM',
                    'start_time': datetime.fromtimestamp(monitor.start_time).isoformat(),
                    'end_time': datetime.fromtimestamp(monitor.end_time).isoformat(),
                    'duration': monitor.get_duration(),
                    'cpu_avg': monitor.get_avg_cpu(),
                    'ram_avg': monitor.get_avg_ram_mb(),
                    'gpu_util_avg': monitor.get_avg_gpu_util(),
                    'gpu_mem_avg_mb': monitor.get_avg_gpu_mem_mb()
                })

                # Automation Stage
                print(f"🤖 Page {idx}: Starting automation...")
                with ResourceMonitor() as monitor:
                    run_automation(page_data)
                print(f"✅ Page {idx}: Automation completed in {monitor.get_duration():.2f}s")
                
                log_performance({
                    'run_timestamp': run_timestamp,
                    'page': idx,
                    'stage': 'Automation',
                    'start_time': datetime.fromtimestamp(monitor.start_time).isoformat(),
                    'end_time': datetime.fromtimestamp(monitor.end_time).isoformat(),
                    'duration': monitor.get_duration(),
                    'cpu_avg': monitor.get_avg_cpu(),
                    'ram_avg': monitor.get_avg_ram_mb(),
                    'gpu_util_avg': monitor.get_avg_gpu_util(),
                    'gpu_mem_avg_mb': monitor.get_avg_gpu_mem_mb()
                })

                all_results.append({'page': idx, 'success': True, 'data': page_data})
                print(f"🎉 Page {idx} processed successfully!")

            except Exception as e:
                all_results.append({'page': idx, 'success': False, 'error': str(e)})
                print(f"❌ Page {idx} error: {str(e)}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        # Save results
        output_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"💾 Results saved to {output_file}")

    # Log overall performance AFTER exiting the context manager
    print("📊 Logging overall performance metrics...")
    log_performance({
        'run_timestamp': run_timestamp,
        'page': 'All',
        'stage': 'TOTAL',
        'start_time': datetime.fromtimestamp(overall_monitor.start_time).isoformat(),
        'end_time': datetime.fromtimestamp(overall_monitor.end_time).isoformat(),
        'duration': overall_monitor.get_duration(),
        'cpu_avg': overall_monitor.get_avg_cpu(),
        'ram_avg': overall_monitor.get_avg_ram_mb(),
        'gpu_util_avg': overall_monitor.get_avg_gpu_util(),
        'gpu_mem_avg_mb': overall_monitor.get_avg_gpu_mem_mb()
    })

    # Add summary row
    total_minutes = overall_monitor.get_duration() / 60
    with open(PERF_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            '', '', '', '', '', 
            f'Total Time in mins,{total_minutes:.1f}',
            '', '', '', ''
        ])

    print(f"\n✅ All processes completed in {overall_monitor.get_duration():.2f}s ({total_minutes:.1f} mins)")
    print(f"📈 Performance metrics saved to {PERF_CSV}")

if __name__ == "__main__":
    run()