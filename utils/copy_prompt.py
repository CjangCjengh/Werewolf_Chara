import os
import pyperclip
import argparse

def list_files(startpath, file_extensions, exclude_keywords):
    tree_structure = ""

    def is_valid_folder(path):
        for root, _, files in os.walk(path):
            for file in files:
                if (any(file.endswith(ext) for ext in file_extensions) and
                        not any(keyword in file for keyword in exclude_keywords)):
                    return True
        return False

    for root, dirs, files in os.walk(startpath):
        if is_valid_folder(root):
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 4 * level
            tree_structure += f"{indent}{os.path.basename(root)}/\n"
            subindent = ' ' * 4 * (level + 1)
            for file in files:
                if (any(file.endswith(ext) for ext in file_extensions) and
                        not any(keyword in file for keyword in exclude_keywords)):
                    tree_structure += f"{subindent}{file}\n"
    return tree_structure

def collect_all_code(startpath, file_extensions, exclude_keywords):
    all_code = ''
    for root, _, files in os.walk(startpath):
        for file in files:
            if (any(file.endswith(ext) for ext in file_extensions) and
                    not any(keyword in file for keyword in exclude_keywords)):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    all_code += f"### {file_path} ###\n"  # File title with full path
                    all_code += f.read() + '\n\n'
    return all_code

def run(project_path, file_extensions, exclude_keywords, game=None):
    if game and game in exclude_keywords:
        exclude_keywords.remove(game)

    file_tree = list_files(project_path, file_extensions, exclude_keywords)
    pyperclip.copy("File Tree:\n" + file_tree + "\n\n")

    all_code = collect_all_code(project_path, file_extensions, exclude_keywords)
    pyperclip.copy(all_code)

    print("All code and file tree have been copied to the clipboard.")
    print("File Tree:\n" + file_tree)


if __name__ == "__main__":
    # Define the start path and file extensions to look for
    project_path = './'
    file_extensions = ['.py']  # Add other extensions as needed
    exclude_keywords = ['codenames', 'avalon', 'landlord', 'hanabi', 'carcassonne', 'werewolf', 'skyteam', 'azul', 'catan'] 

    # Setup argparse to handle command-line arguments
    parser = argparse.ArgumentParser(description="Collect and copy project file tree and code.")
    parser.add_argument('game', type=str, nargs='?', help="Name of the game to remove from exclude list")

    args = parser.parse_args()
    run(project_path, file_extensions, exclude_keywords, args.game)
