import sqlite3
import os

db_path = r"C:\Users\3171131\Desktop\Front-backend\reporte-de-consumos-backend\db.sqlite3"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    names = ["VIVEROS", "PINZON", "CABRERA", "PATINO", "REBAGE", "PACHECO", "GOMEZ", "ORTIZ", "RAMIREZ", "BERRIO", "PEREZ", "BARAJAS"]
    print("Searching names in UsuariosTCS:")
    for n in names:
        cursor.execute("SELECT nombre, usuario, torre, activo FROM UsuariosTCS WHERE nombre LIKE ?", (f"%{n}%",))
        rows = cursor.fetchall()
        for r in rows:
            print(f"  Query: {n} -> Found: {r}")
    conn.close()
