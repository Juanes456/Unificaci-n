import os
import glob
import time

print("Recently modified Excel files (last 2 hours):")
now = time.time()
for f in glob.glob("c:/Users/3171131/Desktop/**/*.xlsx", recursive=True):
    try:
        mtime = os.path.getmtime(f)
        if now - mtime < 7200: # 2 hours
            print(f"  {f} | Mod: {time.ctime(mtime)} | Size: {os.path.getsize(f)} bytes")
    except Exception:
        pass
