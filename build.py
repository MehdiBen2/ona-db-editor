import PyInstaller.__main__
import os
import sys
import sqlite3
import shutil

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get Python's DLL directory
python_dll_dir = os.path.join(sys.base_prefix, 'DLLs')
sqlite_dll = os.path.join(python_dll_dir, 'sqlite3.dll')

# If SQLite DLL not found in DLLs, try to copy it from sqlite3 package location
if not os.path.exists(sqlite_dll):
    sqlite_package_dll = os.path.join(os.path.dirname(sqlite3.__file__), "sqlite3.dll")
    if os.path.exists(sqlite_package_dll):
        shutil.copy2(sqlite_package_dll, os.path.join(current_dir, "sqlite3.dll"))
        sqlite_dll = os.path.join(current_dir, "sqlite3.dll")

PyInstaller.__main__.run([
    'app.py',
    '--name=DatabaseManager',
    '--onefile',
    '--windowed',
    '--clean',
    '--noupx',
    '--noconsole',
    f'--distpath={os.path.join(current_dir, "dist")}',
    f'--workpath={os.path.join(current_dir, "build")}',
    f'--add-data={sqlite_dll};.',
    '--hidden-import=pandas',
    '--hidden-import=sqlite3',
])

# Clean up copied DLL if it exists
if os.path.exists(os.path.join(current_dir, "sqlite3.dll")):
    os.remove(os.path.join(current_dir, "sqlite3.dll")) 