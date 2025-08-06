



from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import NoAlertPresentException, TimeoutException, NoSuchElementException, NoSuchWindowException, WebDriverException
from selenium.webdriver.support.ui import Select
from datetime import datetime
import time
import json
import traceback
from dotenv import load_dotenv
import os

# Load configuration from JSON
# with open(r'config.json') as f:
#     config = json.load(f)




# Initialize error tracking
patient_name = ""
error_log = {}
status = {
    "patient_name": "",
    "error": 0,
    "successfully_save": "no",
    "errors": {},
    "start_time": "",
    "end_time": "",
    "total_time_minutes": 0
}

def save_error_log():
    """Save error details to JSON file with user-friendly messages"""
    if error_log:
        filename = f"error_{patient_name.replace(' ', '_')}.json"
        
        # Create user-friendly error log
        user_friendly_log = {
            "patient": patient_name,
            "errors": {}
        }
        
        for context, message in error_log.items():
            # Simplify error messages
            if "Login" in context:
                user_friendly_log["errors"][context] = "Login failed: Check username/password in .env file"
            elif "click" in message.lower():
                user_friendly_log["errors"][context] = f"Couldn't press button: {context.split(':')[-1].strip()}"
            elif "enter text" in message.lower():
                user_friendly_log["errors"][context] = f"Problem entering info: {context.split(':')[-1].strip()}"
            elif "select" in message.lower():
                user_friendly_log["errors"][context] = f"Couldn't choose option: {context.split(':')[-1].strip()}"
            elif "switch" in message.lower():
                user_friendly_log["errors"][context] = f"Screen navigation issue: {context.split(':')[-1].strip()}"
            elif "adjust date" in message.lower():
                user_friendly_log["errors"][context] = "Date field problem - check date format"
            elif "insurance" in context.lower():
                user_friendly_log["errors"][context] = "Insurance setup failed - check policy info"
            elif "claim" in context.lower():
                user_friendly_log["errors"][context] = "Claim processing error - check CPT codes/dates"
            else:
                user_friendly_log["errors"][context] = f"Processing error: {message}"
        
        with open(filename, 'w') as f:
            json.dump(user_friendly_log, f, indent=4)
        print(f"⛔ Error report saved to {filename}")


def record_error(context, message):
    """Record error details into both error_log and status['errors']."""
    global error_log
    status["error"] = 1
    status["successfully_save"] = "no"

    status["errors"][context] = context
    error_log[context] = context
    print(f"⛔ ERROR in {context}")


def save_status():
    """Append status with time tracking to status.json"""
    logfile = "status.json"
    
    # Calculate total time if available
    if status["start_time"] and status["end_time"]:
        start = datetime.strptime(status["start_time"], "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(status["end_time"], "%Y-%m-%d %H:%M:%S")
        status["total_time_minutes"] = round((end - start).total_seconds() / 60, 1)
    
    try:
        with open(logfile, "r") as f:
            data = json.load(f)
            entries = data if isinstance(data, list) else [data]
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []

    # Create simplified status entry
    entry = {
        "patient": status["patient_name"],
        "status": "Success" if status["successfully_save"] == "yes" else "Failed",
        "start_time": status["start_time"],
        "end_time": status["end_time"],
        "total_minutes": status["total_time_minutes"],
        "issues": list(status["errors"].values()) if status["errors"] else ["None"]
    }

    entries.append(entry)
    with open(logfile, "w") as f:
        json.dump(entries, f, indent=2)

    print(f"✅ Saved status for {status['patient_name']}")


# Helper functions with user-friendly error handling
def click(driver, by, value, context="Unknown", box_name="", timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value)))
        element.click()
        print(f"✅ Pressed button: {box_name or value}")
    except Exception as e:
        record_error(context, f"Could not click button: {box_name or value}")
        raise

def double_click(driver, by, value, context="Unknown", box_name="", timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value)))
        ActionChains(driver).double_click(element).perform()
        print(f"✅ Double-clicked: {box_name or value}")
    except Exception as e:
        record_error(context, f"Could not double-click: {box_name or value}")
        raise

def enter_text(driver, by, value, text, context="Unknown", box_name="", timeout=10, press_enter=False):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value)))
        element.clear()
        element.send_keys(text)
        if press_enter:
            element.send_keys(Keys.ENTER)
        print(f"⌨️ Entered info in: {box_name or value}")
    except Exception as e:
        record_error(context, f"Could not enter text in: {box_name or value}")
        raise

def select_dropdown(driver, by, value, visible_text, context="Unknown", box_name="", timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value)))
        Select(element).select_by_visible_text(visible_text)
        print(f"✅ Selected option: {box_name or value}")
    except Exception as e:
        record_error(context, f"Could not select dropdown: {box_name or value}")
        raise

def switch_frame(driver, frame_name, context="Unknown", box_name="", timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.frame_to_be_available_and_switch_to_it(frame_name))
        print(f"🖼️ Switched screen view: {box_name or frame_name}")
    except Exception as e:
        record_error(context, f"Could not switch screen: {box_name or frame_name}")
        raise

def switch_window(driver, index, context="Unknown", box_name=""):
    try:
        if len(driver.window_handles) > index:
            driver.switch_to.window(driver.window_handles[index])
            print(f"🔀 Switched to window {index} ({box_name})")
        else:
            raise IndexError(f"Window index {index} not available")
    except Exception as e:
        record_error(context, f"Could not switch window: {box_name or 'Unknown'}")
        raise

def accept_alert(driver, context="Unknown", timeout=2, box_name=""):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
        print(f"✅ Handled popup: {box_name or 'Alert'}")
    except (NoAlertPresentException, TimeoutException):
        print("✅ No popup present")
    except Exception as e:
        record_error(context, f"Could not handle popup: {box_name or 'Alert'}")
        raise

def calculate_date_diff(target_str):
    today = datetime.today()
    target = datetime.strptime(target_str, "%m/%d/%Y")
    days_up = (target - today).days
    months_up = target.month - today.month
    years_up = target.year - today.year
    return days_up, months_up, years_up

def custom_date_difference(input_date_str):
    input_date = datetime.strptime(input_date_str, "%m/%d/%Y")
    today = datetime.today()
    years = input_date.year - today.year
    months = input_date.month - today.month  
    days = input_date.day - today.day 
    return {
        "years": years,
        "months": months,
        "days": days
    }

def adjust_date_field(driver, date_input_id, target_date_str, context="Unknown"):
    try:
        diff = custom_date_difference(target_date_str)
        date_input = driver.find_element(By.ID, date_input_id)
        date_input.click()
        time.sleep(0.3)
        date_input.send_keys(Keys.LEFT * 3)
        time.sleep(0.1)
        for _ in range(abs(diff["months"])):
            date_input.send_keys(Keys.UP if diff["months"] > 0 else Keys.DOWN)
            time.sleep(0.05)
        date_input.send_keys(Keys.RIGHT)
        time.sleep(0.1)
        for _ in range(abs(diff["days"])):
            date_input.send_keys(Keys.UP if diff["days"] > 0 else Keys.DOWN)
            time.sleep(0.05)
        date_input.send_keys(Keys.RIGHT)
        time.sleep(0.1)
        for _ in range(abs(diff["years"])):
            date_input.send_keys(Keys.UP if diff["years"] > 0 else Keys.DOWN)
            time.sleep(0.05)
            date_input.send_keys(Keys.ENTER)
        print(f"📅 Set date: {target_date_str}")
    except Exception as e:
        record_error(context, f"Could not set date field")
        raise

def enter_zip_code(driver, zip_code, context="Unknown", element_id="txtZip"):
    try:
        field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, element_id)))
        field.click()
        time.sleep(0.1)
        for _ in range(10):
            field.send_keys(Keys.ARROW_LEFT)
            time.sleep(0.02)
        for digit in zip_code:
            field.send_keys(digit)
            time.sleep(0.05)
        field.send_keys(Keys.SHIFT)
        time.sleep(0.1)
        print(f"📍 Entered ZIP code: {zip_code}")
    except Exception as e:
        record_error(context, f"Could not enter ZIP code")
        raise




def enter_diag_code(driver, diag_code):
    try:
        input_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "txtDiagSearch"))
        )

        input_field.clear()
        
        # Type first character and press Enter
        input_field.send_keys(diag_code[0])
        input_field.send_keys(Keys.ENTER)
        time.sleep(1.5)

        # Type remaining characters
        for char in diag_code[1:]:
            input_field.send_keys(char)
        time.sleep(2)

        print("✅ Diagnosis code entered. Checking if divDiag is open...")

        # Check if div is visible
        div = driver.find_element(By.ID, "divDiag")
        style = div.get_attribute("style")

        if "display: none" in style:
            print("❌ divDiag is hidden. Diagnosis code might be invalid.")
            record_error(
                f"Diagnosis Code Error: Unable to open search results for diagnosis code [{diag_code}]",
                "Failed to open Diagnosis Search section.",
            )
            return

        print("✅ divDiag is visible. Proceeding to select first result...")

        # Wait for first row to be present
        row = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//tr[@id='trDiag_0']"))
        )

        # Perform double-click using Actions
        from selenium.webdriver import ActionChains
        actions = ActionChains(driver)
        actions.double_click(row).perform()
        print("✅ Double-clicked on first diagnosis result.")

    except Exception as e:
        print(f"❌ Exception in enter_diag_code: {str(e)}")
        record_error(
            f"Diagnosis Code Error: Exception while entering or selecting diagnosis code [{diag_code}]: {str(e)}",
            "Error entering Diagnosis code."
        )
        raise




# Initialize driver
def run_automation(config:dict):
    load_dotenv()
    global patient_name, status, error_log
    
    print("\n" + "="*50)
    print("STARTING AUTOMATION PROCESS")
    print("="*50)

    # Reset status for new run
    status = {
        "patient_name": "",
        "error": 0,
        "successfully_save": "no",
        "errors": {},
        "start_time": "",
        "end_time": "",
        "total_time_minutes": 0
    }
    error_log = {}
    
    driver = None
    try:
        # Setup patient info
        required_fields = ['first_name', 'last_name']
        for field in required_fields:
            if not config['patient'].get(field):
                record_error("Error: Some thing is missing from First Name or Last Name Kindly verified you Input Data", f"Missing patient information: {field.replace('_', ' ')}")
                raise ValueError(f"Missing required patient field: {field}")

        patient_name = f"{config['patient']['last_name']}, {config['patient']['first_name']}"
        status["patient_name"] = patient_name
        status["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n=== Processing Patient: {patient_name} at {status['start_time']} ===")
        
        # Validate required fields
        # Initialize browser
        options = Options()
        driver = webdriver.Chrome(options=options)
        
        # Login process
        try:
            USER_NAME = os.getenv("USER_NAME")
            PASSWORD  = os.getenv("PASSWORD")
            if not USER_NAME or not PASSWORD:
                record_error("Login", "Login Failed: Username/password not found in .env file")
                raise RuntimeError("Please set USER_NAME and PASSWORD in your .env file")
                
            driver.get("https://ehr3.myehr123.com/Sybrid3/Default.aspx")
            enter_text(driver, By.ID, "txtUserID", USER_NAME, f"Login Failed, In User Name your System try to Enter that value [{USER_NAME}]", "Username Field")
            time.sleep(2)
            enter_text(driver, By.ID, "txtPassword", PASSWORD, f"Login Failed, In Password your System try to Enter that value [{PASSWORD}]", "Password Field")
            time.sleep(2)
            click(driver, By.ID, "button1", "Login Failed: Checked you userName and password our System try to Enter that values User_Name = '{USER_NAME}' , Password = '{PASSWORD}'.", "Login Button")
            time.sleep(10)
        except Exception as e:
            record_error("Login", "Failed login: Check username/password")
            raise
        
        # Handle window switching
        try:
            if len(driver.window_handles) > 1:
                switch_window(driver, 1, "Login Error: Kindly Run it again or contact with your Software Developer.Login: Switch to new window", "Main Window")
            time.sleep(2)
        except Exception as e:
            record_error("Window Switching", "Could not switch to main window")
            raise
        
        # Navigate to patient search
        try:
            switch_frame(driver, "topframe", "Login Failed: Navigation: Switch to top frame", "Top Menu")
            time.sleep(2)
            click(driver, By.ID, "li_S", "Navigation: Click Search tab", "Search Tab")
            time.sleep(2)
            driver.switch_to.default_content()
            time.sleep(2)
            switch_frame(driver, "displayframe", "Navigation: Switch to display frame", "Search Area")
            time.sleep(2)
        except Exception as e:
            record_error("Navigation", "Could not navigate to patient search")
            raise
        
        # Patient search
        try:
            enter_text(driver, By.ID, "txtSearch", patient_name, 
                        f"Patient Search Error: Kindly check the patient's last name. Your system tried to enter the value [{config['patient']['last_name']}].", "Last Name Field", press_enter=True)
            time.sleep(2)
        except Exception as e:
            record_error("Patient Search", f"Problem searching for patient: {patient_name}")
            raise
        
        driver.switch_to.default_content()
        time.sleep(2)
        switch_frame(driver, "displayframe", "Navigation: Switch back to display frame", "Results Area")
        time.sleep(2)
        
        # Patient handling
        new_patient = False
        try:
            double_click(driver, By.XPATH, "//body[1]/form[1]/table[1]/tbody[1]/tr[1]/td[1]/table[1]/tbody[1]/tr[4]/td[1]/table[1]/tbody[1]/tr[1]/td[1]/div[1]/table[1]/tbody[1]/tr[1]/td[1]/div[3]/table[1]/tbody[1]/tr[1]", 
                            "Patient Selection: Double-click patient row", "Patient Row")
            time.sleep(2)
        except Exception:
            try:
                click(driver, By.XPATH, "//a[normalize-space()='Add Patient']", 
                            "Patient Creation: Click Add Patient", "Add Patient Button")
                time.sleep(2)
                new_patient = True
            except Exception as e:
                # record_error("Patient Selection", "Could not find or add patient")
                raise
        
        # New patient creation
        if new_patient:
            patient_data = config["patient"]
            try:
                required_fields = ['first_name', 'last_name', 'dob', 'zipcode', 'sex']
                for field in required_fields:
                    if not config['patient'].get(field):
                        record_error("Error: Some thing is missing from First Name, Last Name , Gender,  Date of Birth or ZipCode. Kindly verified you Input Data", f"Missing patient information: {field.replace('_', ' ')}")
                        raise ValueError(f"Missing required patient field: {field}")
                
                enter_text(driver, By.ID, "txtLastName", patient_data["last_name"], 
                                f"Error Creating New Patinet: Not able to Enter Patient Last Name. Kindly check the Patient Last Name value our system try to put that value  [ {patient_data['last_name']} ]", "Last Name")
                time.sleep(2)
                enter_text(driver, By.ID, "txtFirstName", patient_data["first_name"], 
                                f"Error Creating New Patinet: Not able to Enter Patient First Name. Kindly check the Patient First Name value our system try to put that value  [ {patient_data['first_name']} ]", "First Name")
                time.sleep(2) 
                enter_text(driver, By.ID, "txtAddress", patient_data["address"], 
                                f"Error Creating New Patinet: Not able to Enter Patient Address. Kindly check the Patient Address value our system try to put that value  [ {patient_data['address']} ]", "Address")
                time.sleep(2)
                enter_text(driver, By.ID, "txtEMail", patient_data["email"], 
                                f"Error Creating New Patinet: Not able to Enter Patient Email Address. Kindly check the Patient Email Address value our system try to put that value  [ {patient_data['email']} ]" "Email")
                time.sleep(2)
                select_dropdown(driver, By.ID, "selSex", patient_data["sex"], 
                                    f"Error Creating New Patinet: Not able to Select Patient Gender. Kindly check the Patient Gender value our system try to put that value  [ {patient_data['sex']} ]", "Gender")
                time.sleep(2)
                
                # Set DOB
                dob_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "txtDOB")))
                time.sleep(2)
                driver.execute_script(f"arguments[0].value = '{patient_data['dob']}';", dob_field)
                time.sleep(2)
                accept_alert(driver, "Patient Creation: Handle DOB alert", box_name="DOB Alert")
                time.sleep(2)
                
                # ZIP code handling
                enter_zip_code(driver, patient_data["zipcode"],  f"Error Creating New Patinet: Not able to Enter Patient ZIP Code. Kindly check the Patient ZIP Code value our system try to put that value  [ {patient_data['zipcode']} ]")
                time.sleep(2)
                accept_alert(driver, "Patient Creation: Handle ZIP alert", box_name="ZIP Alert")
                time.sleep(2)
                
                click(driver, By.XPATH, "//a[normalize-space()='Save']", 
                            f"Error Creating New Patinet: Not able to Click Save Button. Kindly check the Patient Data.", "Save Button")
                time.sleep(2)
                accept_alert(driver, "Patient Creation: Handle save alert", box_name="Save Alert")
                time.sleep(2)
                print("✅ New patient added successfully.")
            except Exception as e:
                record_error("Patient Creation", "Failed to create patient - check required fields")
                raise
        
        # Insurance process
    # try:
        if not new_patient:
            click(driver, By.XPATH, "//body[1]/form[1]/table[1]/tbody[1]/tr[2]/td[1]/div[1]/table[1]/tbody[1]/tr[1]/td[4]", 
                    "Error in Insurance section: Not able to Navigate to insurance tab", "Insurance Tab")
            time.sleep(2)
            
        if not driver.find_element(By.ID, "txtPOLICYNUM0").get_attribute("value"):
            insurance_data = config["insurance"]
            # try:
            required_fields = ['carrier_initial', 'policy_number']
            for field in insurance_data:
                if not config['insurance'].get(field):
                    record_error("Error: Some thing is missing from Insurace Name or Policy Number. Kindly verified you Input Data", f"Missing patient information: {field.replace('_', ' ')}")
                    raise ValueError(f"Missing required patient field: {field}")

            click(driver, By.XPATH, "//a[normalize-space()='Edit Insurance']", 
                    "Error in Insurance: Not able to Click Edit Insurance Button", "Edit Insurance Button")
            time.sleep(2)
            switch_window(driver, 2, "Error in Insurance: Not able to Switch to insurance window", "Insurance Window")
            time.sleep(2)
            enter_text(driver, By.ID, "txtCarrierName", config["insurance"]["carrier_initial"], 
                        f"Error in Insurance section: Now able to Enter carrier Name. Kindly check the Patient Insurance value our system try to put that value  [ {config['insurance']['carrier_initial']} ]", "Carrier Initials", press_enter=True)
            time.sleep(2)
            double_click(driver, By.ID, "trInsList0", 
                            f"Error in Insurance section: Now able to Double-click insurance option. Kindly check the Patient Insurance value our system try to put that value  [ {config['insurance']['carrier_initial']} ]", "Insurance Option")
            time.sleep(2)
            switch_window(driver, 1, "Erron in Insurance: Switch back to main window", "Main Window")
            time.sleep(2)
            driver.switch_to.default_content()
            time.sleep(2)
            switch_frame(driver, "displayframe", "Erron in Insurance: Switch to display frame", "Insurance Details")
            time.sleep(2)
            enter_text(driver, By.XPATH, "//input[@id='txtPOLICYNUM0']", config["insurance"]["policy_number"], 
                        f"Error in Insurance section: Now able to Enter Policy Number. Kindly check the Patient Policy Number value our system try to put that value  [ {config['insurance']['policy_number']} ]", "Policy Number")
            time.sleep(2)
            click(driver, By.XPATH, "//a[normalize-space()='Save']", 
                    "Error in Insurance Section: Now able to Click Save Button kindly check your Insurance Related data", "Save Button")
            time.sleep(5)

        click(driver, By.XPATH, "//label[@class='PO_PCLicon']", 
                "Claims section Error: Kindly Run it again or contact with your Software Developer. ", "Claims Tab")
        time.sleep(2)

        driver.switch_to.default_content()
        time.sleep(2)
        switch_frame(driver, "displayframe", "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. Claims: Switch to display frame", "Claims Area")
        time.sleep(2)
        click(driver, By.XPATH, "//body[1]/form[1]/table[1]/tbody[1]/tr[3]/td[1]/table[1]/tbody[1]/tr[1]/td[1]/table[1]/tbody[1]/tr[1]/td[1]", 
                "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. Claims: Start new claim", "New Claim Button")
        time.sleep(5)

        
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        time.sleep(2)
        new_tab = [h for h in driver.window_handles if h != driver.current_window_handle][1]
        time.sleep(2)
        driver.switch_to.window(new_tab)
        switch_window(driver, 3, "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. Claims: Switch back", "Claims Window")

        
        # Claims entry process
        print("now its try to put value in input box")
        enter_text(driver, By.XPATH, "//input[@id='txtSearch']", config["claims"]["physician_initial"], 
                    f"Master Physician Error In claims Section: Not able to Enter Master Physician. Kindly check the Master Physician value our system try to put that value  [ {config['claims']['physician_initial']} ]", "Physician Initials", press_enter=True)
        time.sleep(2)
        print("Now its try to click on the first row")
        double_click(driver, By.XPATH, "/html[1]/body[1]/form[1]/div[3]/div[3]/div[1]/div[1]/div[2]/div[1]/div[1]", 
                        f"Master Physician Error In claims Section: Not able to Select Master Physician. Kindly check the Master Physician value our system try to put that value  [ {config['claims']['physician_initial']} ]", "Physician Result")
        time.sleep(2)
        print("now its not giving as error")
        
        # Switch back to claims window
        switch_window(driver, 2, "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. Claims: Switch back", "Claims Window")
        time.sleep(2)

        click(driver, By.XPATH, "//input[@id='btnRefSearch']", 
                f"Referring Doctor Error In claims Section: Not able to Click on Facility search button. Kindly check the Referring Doctor value our system try to put that value  [ {config['claims']['referring_initial']} ]", "Referring Physician Button")
        time.sleep(5)


            
        # Switch to new window for referring physician
        switch_window(driver, 3, "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. Claims: Referring physician", "Referring Physician Window")
        time.sleep(2)
        
        enter_text(driver, By.ID, "txtRefPhysician", config["claims"]["referring_initial"], 
                    f"Referring Doctor Error In claims Section: Not able to Enter value for Referring Doctor. Kindly check the Referring Doctor value our system try to put that value  [ {config['claims']['referring_initial']} ]", "Referring Initials", press_enter=True)
        time.sleep(2)
        double_click(driver, By.XPATH, "/html[1]/body[1]/form[1]/table[1]/tbody[1]/tr[4]/td[1]/div[1]/table[1]/tbody[1]/tr[1]", 
                        f"Referring Doctor Error In claims Section: Not able to Select Referring Doctor. Kindly check the Referring Doctor value our system try to put that value  [ {config['claims']['referring_initial']} ]", "Referring Result")
        time.sleep(2)
        
        # Switch back to claims window
        switch_window(driver, 2, "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. Claims: Switch back", "Claims Window")
        time.sleep(2)
        
        click(driver, By.XPATH, "//input[@id='btnFacSearch']", 
                f"Facility/Hospita Error In claims Section: Not able to Click on Facility/Hospita search button. Kindly check the Facility/Hospita value our system try to put that value  [ {config['claims']['facility_initial']} ]", "Facility Button")
        time.sleep(2)
        
        # Switch to new window for facility
        switch_window(driver, 3, "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. Claims: Facility search", "Facility Window")
        time.sleep(2)
        
        enter_text(driver, By.XPATH, "/html[1]/body[1]/form[1]/table[1]/tbody[1]/tr[2]/td[1]/table[1]/tbody[1]/tr[1]/td[2]/input[1]", 
                    config["claims"]["facility_initial"], "Facility/Hospital Error In claims Section: Not able to Click on the Facility/Hospital Search button. Kindly Run it again or contact with your Software Developer.", "Facility Initials", press_enter=True)
        time.sleep(2)
        double_click(driver, By.ID, "TrData0", f"Facility/Hospital Error In claims Section: Not able to Select Facility. Kindly check the Facility value our system try to put that value  [ {config['claims']['facility_initial']} ]", "Facility Result")
        time.sleep(2)
        
        # Switch back to claims window
        switch_window(driver, 2, "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. ", "Claims Window")
        time.sleep(2)
        
        try:
            claim_data = config["claims"]
            adjust_date_field(driver, "txtFromDate", claim_data["from_date"], 
                                f"From Data set Error In claims Section: Not able to Set on From Date. Kindly check the From Date value our system try to put that value  [ {claim_data['from_date']} ]")
            time.sleep(2)
            adjust_date_field(driver, "txtToDate", claim_data["to_date"], 
                                "To Data set Error In claims Section: Not able to Set on To Date. Kindly check the To Date value our system try to put that value  [ {claim_data['to_date']} ]")
            # Try to switch to the alert
            alert = driver.switch_to.alert
            alert_text = alert.text
            print("🔔 Alert found with text:", alert_text)

            if "To date must be later than the from date" in alert_text:  # Case-insensitive check for "xyz"
                # print("⚠️ 'xyz' found in alert text. Raising error...")
                record_error(f"Your input date has a problem. To date must be later than the from date. our system try to put that value [{claim_data['from_date']} to {claim_data['to_date']}]" , "")
                raise Exception("Your input date has a problem")

            # Optionally accept the alert if needed
            alert.accept()

        except NoAlertPresentException:
            print("✅ No alert present.")
        # Date adjustments

        time.sleep(2)
        
        # Enter codes
        # enter_text(driver, By.ID, "txt__CPT4", claim_data["cpt_code"], 
        cpt_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "txt__CPT4")))
        cpt_input.clear()
        cpt_input.send_keys(claim_data["cpt_code"])
        cpt_input.send_keys(Keys.ENTER)
        time.sleep(2)
        
        accept_alert(driver, "Claims Error: Handle CPT4 code alert", box_name="CPT4 Alert")

        #             "Claims: Enter CPT code", "CPT Code", press_enter=True)

        time.sleep(5)
        print("now i press the enter")
        div = driver.find_element(By.ID, "divSearch")
        print("This si the div")
        # Check if div is displayed (visible)

        style = div.get_attribute("style")

        if "display: none" in style:
            print("❌ The divSearch is hidden based on style.")
        else:
            print("✅ The divSearch is visible based on style.")

        if div.is_displayed():
            print("✅ The divSearch is visible.")
            record_error(f"CPT4 Code Error in Claims Section:  Not able to Enter CPT4 Code. Kindly check the CPT4 value our system try to put that value  [ {claim_data['cpt_code']} ]", "Failed to enter CPT code properly.")
            raise

        time.sleep(5)
        # print("This is the len =0" , len(driver.window_handles))
        accept_alert(driver, "Claims: Handle CPT alert", box_name="CPT Alert")
        time.sleep(2)

        # Diagnoses
        diagnoses_data = config["diagnoses"]
        for i in range(1, 13):
            key = f"txt__DIAG{i}"
            if key in diagnoses_data and diagnoses_data[key]:
                diag_value = diagnoses_data[key]
                print(f"Setting diagnosis {i}: {diag_value}")
                # enter_text(driver, By.ID, key, diag_value, 
                #             f"Diagnosis Error in Claims Section: Kindly check the Diagnosis value your system try to enter that value =  Enter [{diag_value}]", press_enter=True)
                input_field = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, key))
                )

                input_field.clear()
                
                # Type first character and press Enter
                input_field.send_keys(diag_value)
                input_field.send_keys(Keys.ENTER)
                time.sleep(5)
                div = driver.find_element(By.ID, "divDiag")
                style = div.get_attribute("style")
                if "display: none" in style:
                    print("The div is closed")
                else:
                    print("❌ divDiag is hidden. Diagnosis code might be invalid.")
                    record_error(
                        f"Diagnosis Code Error: Unable to open search results for diagnosis code [{diag_value}]",
                        "Failed to open Diagnosis Search section.",
                    )
                    return

                # enter_diag_code(driver , diag_value)
                time.sleep(1)
                accept_alert(driver, f"Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. Claims: Handle diagnosis {i} alert")
        
        # Save claim
        click(driver, By.ID, "but_AddSer", " Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer. Claims: Click Add Service", "Add Service Button")
        time.sleep(2)
        accept_alert(driver, "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer.  Claims: Handle add service alert", box_name="Service Alert")
        time.sleep(2)
        click(driver, By.XPATH, "//button[contains(@onclick, 'SaveClaims')]", 
                "Claims section Error In claims Section: Kindly Run it again or contact with your Software Developer.  Claims: Click Save Claim", "Save Claim Button")
        time.sleep(2)
        driver.quit()
        # If we reached here, mark as successful
        status["successfully_save"] = "yes"
        status["error"] = 0
        print("✅ Claim added successfully.")
        
    except Exception as e:
        # Catch-all for unhandled exceptions
        print("this si  hte error = " , e)
        if not error_log:
            record_error("System Error", "Unexpected system failure")
        print(f"⛔ Processing stopped for {patient_name}")

    finally:
        # Record end time
        status["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save results and clean up
        save_status()
        if error_log:
            save_error_log()
        
        try:
            if driver:
                driver.quit()
                print("✅ Browser closed")
        except Exception:
            print("⚠️ Error closing browser")




# run_automation(config)