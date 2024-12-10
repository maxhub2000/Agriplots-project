from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QPushButton, QLineEdit, QWidget, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication, QFont
import sys
import os
import shutil


def comment_multiple_sections_in_mod(template_file, edited_file, start_texts):
    """
    Creates a copy of the template file, applies comments to multiple specified sections,
    and saves the result in the new file. Handles both single-line and multi-line sections.

    Args:
        template_file (str): Path to the template .mod file (original file).
        edited_file (str): Path to the edited .mod file (modified copy).
        start_texts (list): A list of strings identifying starting lines before the comment blocks.
    """
    # Create a copy of the template file to edit
    shutil.copy(template_file, edited_file)

    with open(edited_file, 'r') as file:
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

    # Check if any new comments were added before overwriting the file
    if not already_commented:
        with open(edited_file, 'w') as file:
            file.writelines(commented_lines)


# Example usage:
template_file_path = "edit_mod_file/template.mod"
edited_file_path = os.path.join("edit_mod_file", "edited.mod")
start_texts_to_comment = [
    "Constraint for an upper bound of the total area used by installed PV's",
    "Linearized Gini coefficient constraint (only for i < j)",
    "Gini constraint (now summing only over i < j)",
    "Constraint for the total energy production of each machoz, upper bounded by the energy consumption of each machoz",
    "Constraint for the total energy production of each yeshuv, upper bounded by the energy consumption of each yeshuv",
    "Constraint for the revenue change in percentage as a result of installing the PV's and influencing the crops, lower bounded by an inputed threshold"
]

# comment_multiple_sections_in_mod(template_file_path, edited_file_path, start_texts_to_comment)




# if __name__ == "__main__":
#     user_input = activate_interface()
#     user_input_total_area_upper_bound = user_input[0]
#     user_input_allowed_loss_from_influence_on_crops_percentage = user_input[1]
#     removed_constraints = user_input[2]
#     print("user_input_total_area_upper_bound:",user_input_total_area_upper_bound)
#     print("user_input_allowed_loss_from_influence_on_crops_percentage:",user_input_allowed_loss_from_influence_on_crops_percentage)
#     print("removed_constraints:",removed_constraints)

    


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = LinearProgrammingInterface()
#     window.show()
#     sys.exit(app.exec_())
