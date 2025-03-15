from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QPushButton, QLineEdit, QWidget, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication, QFont
import sys
import os
import shutil



def remove_constraints_from_model(removed_constraints, mod_file_path, constraints_to_comment_texts):
    comments_in_mod_file = []
    for removed_constraint in removed_constraints:
        comments_in_mod_file.append(constraints_to_comment_texts[removed_constraint])
    comment_multiple_sections_in_mod(mod_file_path, comments_in_mod_file)
    print("\n")
    print("The following constraints were removed from the model:")
    for removed_constraint in removed_constraints:
        print(removed_constraint)
    print("\n")


def comment_multiple_sections_in_mod(mod_file_path, start_texts):
    """
    Applies comments to multiple specified sections and saves the changes in the given file.
    Handles both single-line and multi-line sections.

    Args:
        mod_file_path (str): Path to the .mod file that's being modified.
        start_texts (List[str]): List of strings marking the beginning of sections to comment.

    Returns:
        None
    """

    with open(mod_file_path, 'r') as file:
        lines = file.readlines()

    inside_section = False
    inside_block = False  # Track whether inside a multi-line block
    already_commented = set()  # Track already-commented sections
    commented_lines = []
    for i, line in enumerate(lines):
        # Check if this line matches any of the start_texts
        if any(start_text in line for start_text in start_texts) and not inside_section:
            commented_lines.append(line)  # Keep the start_text line outside the comment
            # Check if the next line already has the '/*' comment tag
            if i + 1 < len(lines) and lines[i + 1].strip() == "/*":
                already_commented.add(line.strip())  # Mark this start_text as already commented
            else:
                commented_lines.append("    /*\n")  # Add opening comment tag below the start_text
                inside_section = True
        elif inside_section:
            commented_lines.append(line)  # Include the original line inside the comment block
            if "{" in line:  # Detect the start of a multi-line block
                inside_block = True
            if "}" in line and inside_block:  # Detect the end of a multi-line block
                inside_block = False
                inside_section = False
                commented_lines.append("    */\n")  # Add closing comment tag after the block
            elif not inside_block and line.strip().endswith(";"):  # End single-line section
                inside_section = False
                commented_lines.append("    */\n")  # Add closing comment tag
        else:
            commented_lines.append(line)  # Unmodified lines

    # Check if any new comments were added before overwriting the file,
    # if there were new comments, won't make any changes to the file
    if not already_commented:
        with open(mod_file_path, 'w') as file:
            file.writelines(commented_lines)

