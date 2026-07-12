# import os

# IGNORED_DIRS = {'.git', 'node_modules', 'vendor', 'dist', 'build', '__pycache__', 'coverage', '.idea', '.vscode', 'alembic', 'venv', 'uploads'}
# IGNORED_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.exe', '.dll', '.so', '.mp4', '.pyc', '.csv', '.sql', '.html', '.css'}

# def is_text_file(file_path):
#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             f.read(1024)
#         return True
#     except (UnicodeDecodeError, PermissionError):
#         return False

# def generate_project_structure(source_dir, output_filename):
#     def write_tree(current_dir, outfile, prefix=""):
#         try:
#             entries = sorted(os.listdir(current_dir))
#         except PermissionError:
#             return

#         entries = [e for e in entries if e not in IGNORED_DIRS]
#         entries_count = len(entries)

#         for i, entry in enumerate(entries):
#             full_path = os.path.join(current_dir, entry)
#             is_last = (i == entries_count - 1)
#             pointer = "└── " if is_last else "├── "
            
#             outfile.write(f"{prefix}{pointer}{entry}\n")
            
#             if os.path.isdir(full_path):
#                 extension = "    " if is_last else "│   "
#                 write_tree(full_path, outfile, prefix + extension)

#     with open(output_filename, 'w', encoding='utf-8') as outfile:
#         outfile.write("Struktur Direktori Proyek:\n.\n")
#         write_tree(source_dir, outfile)

# def generate_project_bundle(source_dir, output_filename):
#     with open(output_filename, 'w', encoding='utf-8') as outfile:
#         for root, dirs, files in os.walk(source_dir):
#             dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            
#             for file in files:
#                 ext = os.path.splitext(file)[1].lower()
#                 if ext in IGNORED_EXTS:
#                     continue
                
#                 file_path = os.path.join(root, file)
                
#                 if not is_text_file(file_path):
#                     continue
                
#                 rel_path = os.path.relpath(file_path, source_dir)
#                 outfile.write(f"\n# {rel_path}\n")
                
#                 try:
#                     with open(file_path, 'r', encoding='utf-8') as infile:
#                         content = infile.read()
#                         outfile.write(f"{content}\n")
#                 except Exception as e:
#                     outfile.write(f"// Error: {str(e)}\n")

# if __name__ == "__main__":
#     TARGET_DIRECTORY = '.'
#     STRUCTURE_OUTPUT = 'struktur_proyek.txt'
#     BUNDLE_OUTPUT = 'project_bundle.txt'
    
#     print(f"Memproses {os.path.abspath(TARGET_DIRECTORY)}...")
#     generate_project_structure(TARGET_DIRECTORY, STRUCTURE_OUTPUT)
#     generate_project_bundle(TARGET_DIRECTORY, BUNDLE_OUTPUT)
#     print("Proses selesai.")