import sqlite3
import os

db_path = r"C:\Users\3171131\Desktop\Front-backend\reporte-de-consumos-backend\db.sqlite3"
if os.path.exists(db_path):
    print("Database found at:", db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Try to find UsuariosTCS or similar table
    user_table = "UsuariosTCS"
        
    cursor.execute(f"SELECT DISTINCT torre FROM {user_table}")
    print("Distinct towers:", cursor.fetchall())
    
    cursor.execute(f"SELECT nombre, usuario, torre, activo FROM {user_table} WHERE LOWER(torre) LIKE '%malla%' LIMIT 10")
    print("\nMalla users sample in DB:")
    for r in cursor.fetchall():
         print("  ", r)
        
    cursor.execute(f"SELECT nombre, usuario, torre, activo FROM {user_table} WHERE nombre LIKE '%LOPERA%' OR nombre LIKE '%FLOREZ%'")
    print("\nLopera / Florez in DB:")
    for r in cursor.fetchall():
         print("  ", r)
            
    conn.close()
else:
    print("Database not found at:", db_path)
