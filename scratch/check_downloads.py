import os
import glob

print("Files in Downloads folder:")
files = glob.glob("c:/Users/3171131/Downloads/**/*.xlsx", recursive=True)
for f in files[:20]:
    print("  ", f)
