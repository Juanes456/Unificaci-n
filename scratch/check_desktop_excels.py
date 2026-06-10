import os
import glob

folder = r"C:\Users\3171131\Desktop\excels"
if os.path.exists(folder):
    print("Folder exists:", folder)
    files = glob.glob(os.path.join(folder, "*.xlsx"))
    print("Excel files in folder:")
    for f in files:
        print("  ", f)
else:
    print("Folder does not exist:", folder)
    # Search parent folder just in case
    parent = r"C:\Users\3171131\Desktop"
    print("Files matching 'WO y TASK' on Desktop:")
    for f in glob.glob(os.path.join(parent, "**/*WO y TASK*.xlsx"), recursive=True):
        print("  ", f)
