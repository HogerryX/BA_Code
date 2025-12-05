import os
from pathlib import Path

def debug_filtering(dir_path, supported_extensions=['.pdf', '.docx']):
    
    def get_all_files(path):
        files = []
        for root, dirs, filenames in os.walk(path, followlinks=True):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(file_path)
        return files
    
    all_files = get_all_files(dir_path)
    print(f"Gesamtanzahl Dateien: {len(all_files)}")
    print("=" * 60)
    
    def filter_original(files):
        def filter_pdf(files):
            file_pdf = []
            for file in files:
                if file.lower().endswith(".pdf"):
                    file_pdf.append(file)
                else:
                    continue
            return file_pdf
        
        def filter_word(files):
            file_word = []
            for file in files:
                if file.lower().endswith(".docx") and not "englisch" in file.lower():
                    file_word.append(file)
                else:
                    continue
            return file_word
        
        pdf_files = filter_pdf(files)
        docx_files = filter_word(files)
        return {'pdf': pdf_files, 'docx': docx_files}
    
    def filter_filehandler(files, supported_extensions):
        supported_files = {ext: [] for ext in supported_extensions}
        unsupported_count = 0
        
        for file_path in files:
            file_extension = Path(file_path).suffix.lower()
            if file_extension in supported_extensions:
                if file_extension == '.docx' and 'englisch' in Path(file_path).name.lower():
                    unsupported_count += 1
                    continue
                supported_files[file_extension].append(file_path)
            else:
                unsupported_count += 1
        
        return supported_files
    
    result1 = filter_original(all_files)
    result2 = filter_filehandler(all_files, supported_extensions)
    
    print("ERGEBNISSE:")
    print(f"Original - PDF: {len(result1['pdf'])}, DOCX: {len(result1['docx'])}")
    print(f"FileHandler - PDF: {len(result2.get('.pdf', []))}, DOCX: {len(result2.get('.docx', []))}")
    print()
    
    pdf1 = set(result1['pdf'])
    pdf2 = set(result2.get('.pdf', []))
    docx1 = set(result1['docx'])
    docx2 = set(result2.get('.docx', []))
    
    print("PDF UNTERSCHIEDE:")
    only_in_original_pdf = pdf1 - pdf2
    only_in_filehandler_pdf = pdf2 - pdf1
    
    if only_in_original_pdf:
        print("Nur in Original:")
        for file in sorted(only_in_original_pdf):
            print(f"  {file}")
    
    if only_in_filehandler_pdf:
        print("Nur in FileHandler:")
        for file in sorted(only_in_filehandler_pdf):
            print(f"  {file}")
    
    if not only_in_original_pdf and not only_in_filehandler_pdf:
        print("Keine Unterschiede bei PDF-Dateien")
    
    print("\nDOCX UNTERSCHIEDE:")
    only_in_original_docx = docx1 - docx2
    only_in_filehandler_docx = docx2 - docx1
    
    if only_in_original_docx:
        print("Nur in Original:")
        for file in sorted(only_in_original_docx):
            print(f"  {file}")
            print(f"    Extension: '{Path(file).suffix}'")
            print(f"    Name: '{Path(file).name}'")
    
    if only_in_filehandler_docx:
        print("Nur in FileHandler:")
        for file in sorted(only_in_filehandler_docx):
            print(f"  {file}")
            print(f"    Extension: '{Path(file).suffix}'")
            print(f"    Name: '{Path(file).name}'")
    
    if not only_in_original_docx and not only_in_filehandler_docx:
        print("Keine Unterschiede bei DOCX-Dateien")
    
    print("\nALLE EXTENSIONS ANALYSE:")
    extensions = {}
    for file in all_files:
        ext = Path(file).suffix.lower()
        if ext not in extensions:
            extensions[ext] = []
        extensions[ext].append(file)
    
    for ext, files in sorted(extensions.items()):
        if ext in ['.pdf', '.docx', '.doc']:
            print(f"Extension '{ext}': {len(files)} Dateien")
            if ext == '.docx':
                englisch_files = [f for f in files if 'englisch' in Path(f).name.lower()]
                if englisch_files:
                    print(f"  Davon mit 'englisch': {len(englisch_files)}")
    
    return {
        'all_files': len(all_files),
        'original': result1,
        'filehandler': result2,
        'pdf_diff': {'only_original': only_in_original_pdf, 'only_filehandler': only_in_filehandler_pdf},
        'docx_diff': {'only_original': only_in_original_docx, 'only_filehandler': only_in_filehandler_docx}
    }

if __name__ == "__main__":
    dir_path = '../../Bachelorarbeit_DBSM_DNB'
    results = debug_filtering(dir_path)