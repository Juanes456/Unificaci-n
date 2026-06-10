import customtkinter as ctk
from main import UnificadaApp

app = UnificadaApp()
app.update()

print("Sidebar grid size:", app.sidebar.grid_size())
print("Row configurations:")
for i in range(10):
    print(f"  Row {i}: {app.sidebar.grid_rowconfigure(i)}")

print("Widgets in sidebar:")
for w in app.sidebar.winfo_children():
    info = w.grid_info()
    print(f"  Widget: {w} | row: {info.get('row')}, column: {info.get('column')}, rowspan: {info.get('rowspan')}, columnspan: {info.get('columnspan')}")
    print(f"    Height: {w.winfo_height()}")

app.destroy()
