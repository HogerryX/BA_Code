import os
from pathlib import Path

def debug_comparison(dir_path):
    
    def get_files_method1(path):
        def get_dir_content(path):
            content = os.listdir(path)
            files = []
            for con in content:
                files.append(f"{path}/{con}")
            return files
        
        def filter_dir_content(content):
            files = []
            directories = []
            for file in content:
                if(os.path.isdir(file)):
                    directories.append(file)
                else:
                    files.append(file)
            return {"files": files, "directories": directories}
        
        def read_dir(path):
            directories = []
            files = []
            content = get_dir_content(path)
            files.extend(filter_dir_content(content)["files"])
            directories.extend(filter_dir_content(content)["directories"])
            while len(directories) > 0:
                try:
                    content = get_dir_content(directories[0])
                    files.extend(filter_dir_content(content)["files"])
                    directories.extend(filter_dir_content(content)["directories"])
                except PermissionError as e:
                    print(f"Permission denied for {directories[0]}: {e}")
                except Exception as e:
                    print(f"Error processing {directories[0]}: {e}")
                directories.pop(0)
            return files
        
        return read_dir(path)
    
    def get_files_method2(path):
        try:
            path_obj = Path(path)
            files = []
            for file_path in path_obj.rglob('*'):
                if file_path.is_file():
                    files.append(str(file_path))
            return files
        except Exception as e:
            print(f"Error with pathlib method: {e}")
            return []
    
    def get_files_method3(path):
        try:
            path_obj = Path(path)
            files = []
            try:
                for file_path in path_obj.rglob('*'):
                    if file_path.is_file():
                        files.append(str(file_path))
            except TypeError:
                # Fallback für ältere Python-Versionen
                for file_path in path_obj.rglob('*'):
                    if file_path.is_file():
                        files.append(str(file_path))
            return files
        except Exception as e:
            print(f"Error with pathlib method 3: {e}")
            return []
    
    print(f"Analysiere Verzeichnis: {dir_path}")
    print("=" * 60)
    
    files1 = set(get_files_method1(dir_path))
    files2 = set(get_files_method2(dir_path))
    files3 = set(get_files_method3(dir_path))
    
    print(f"Methode 1 (original): {len(files1)} Dateien")
    print(f"Methode 2 (rglob): {len(files2)} Dateien")
    print(f"Methode 3 (os.walk): {len(files3)} Dateien")
    print()
    
    only_in_method1 = files1 - files2
    only_in_method2 = files2 - files1
    
    if only_in_method1:
        print("Dateien nur in Methode 1 (original):")
        for file in sorted(only_in_method1):
            print(f"  {file}")
            # Prüfe ob es sich um Symlink handelt
            if os.path.islink(file):
                print(f"    -> Symlink zu: {os.readlink(file)}")
        print()
    
    if only_in_method2:
        print("Dateien nur in Methode 2 (pathlib):")
        for file in sorted(only_in_method2):
            print(f"  {file}")
        print()
    
    print("Versteckte Ordner/Dateien gefunden:")
    hidden_files = [f for f in files1 if any(part.startswith('.') for part in Path(f).parts)]
    for file in sorted(hidden_files):
        print(f"  {file}")
    
    return {
        'method1': files1,
        'method2': files2,
        'method3': files3,
        'only_method1': only_in_method1,
        'only_method2': only_in_method2
    }

if __name__ == "__main__":
    dir_path = 'data/files'
    results = debug_comparison(dir_path)