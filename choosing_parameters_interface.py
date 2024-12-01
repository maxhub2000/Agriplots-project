from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QPushButton, QLineEdit, QWidget, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication, QFont
import sys

T__, M__ = 0,0
class LinearProgrammingInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.resize(800, 300)

    def init_ui(self):
        # Get the screen geometry and set the window size to full screen
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height())
        self.setWindowTitle("Linear Programming Problem")
        self.setStyleSheet("background-color: #f7f9fb;")

        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 10, 30, 10)
        self.layout.setSpacing(10)

        # Header
        header = QLabel("Linear Programming Problem")
        header.setStyleSheet("font-size: 50px; font-weight: bold; color: white; background-color: #2e86c1; padding: 20px;")
        header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(header)

        # Objective Function Section
        objective_function = QLabel(
            '<p style="font-size: 40px; color: #41a3e0;"><b>Objective Function</b></p>'
            '<p style="font-size: 30px; color: #34495e;">Maximize <b>Total Energy Production</b></p>'
        )
        objective_function.setTextFormat(Qt.RichText)
        self.layout.addWidget(objective_function)

        # Constraints Section
        constraints = QLabel('<p style="font-size: 40px; color: #41a3e0;"><b>Constraints</b></p>')
        constraints.setTextFormat(Qt.RichText)
        self.layout.addWidget(constraints)

        # Constraint elements storage
        self.constraints_data = []

        # Add Constraints
        self.add_constraint("1. Total Area PV Installations ≤", "Dunam", True)
        self.add_constraint("2. Percentage Change in Revenue ≤", "%", True)
        self.add_constraint("3. Total Energy Production of yeshuv ≤ <b>Total Energy Consumption of yeshuv</b>", "", False)
        self.add_constraint("4. Total Energy Production of machoz ≤ <b>Total Energy Consumption of machoz</b>", "", False)

        # Remove Constraints Button
        self.remove_constraints_button = QPushButton("Remove Constraints")
        self.remove_constraints_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #e74c3c; padding: 5px 10px;")
        self.remove_constraints_button.setFixedSize(400, 50)
        self.remove_constraints_button.clicked.connect(self.enable_constraints_removal)
        self.layout.addWidget(self.remove_constraints_button, alignment=Qt.AlignLeft)

        # Confirm Changes Button (initially hidden)
        self.confirm_changes_button = QPushButton("✓")
        self.confirm_changes_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #27ae60; padding: 5px;")
        self.confirm_changes_button.setFixedSize(50, 50)
        self.confirm_changes_button.clicked.connect(self.confirm_constraints_changes)
        self.confirm_changes_button.hide()
        self.layout.addWidget(self.confirm_changes_button, alignment=Qt.AlignLeft)

        # Confirm Button
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #27ae60; padding: 5px 10px;")
        self.confirm_button.setFixedSize(150, 50)
        self.confirm_button.clicked.connect(self.confirm_parameters)
        self.layout.addWidget(self.confirm_button, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

        # Variables to hold T and M values
        self.t_value = None
        self.m_value = None
        self.removed_constraints = []

    def add_constraint(self, text, unit, has_input):
        """Adds a constraint to the layout."""
        constraint_layout = QHBoxLayout()

        # Constraint label
        constraint_label = QLabel(text)
        constraint_label.setStyleSheet("font-size: 20px; color: #34495e;")
        constraint_label.setTextFormat(Qt.RichText)
        constraint_layout.addWidget(constraint_label)

        # Input field and unit (if applicable)
        input_field = None
        if has_input:
            input_field = QLineEdit()
            input_field.setStyleSheet("font-size: 20px; color: #34495e; background-color: white; padding: 5px;")
            input_field.setFixedWidth(100)
            constraint_layout.addWidget(input_field)

            unit_label = QLabel(unit)
            unit_label.setStyleSheet("font-size: 20px; color: #34495e;")
            constraint_layout.addWidget(unit_label)

        # Add constraint to layout
        self.layout.addLayout(constraint_layout)

        # Save constraint data
        self.constraints_data.append({
            "layout": constraint_layout,
            "label": constraint_label,
            "input": input_field,
            "removed": False
        })

    def enable_constraints_removal(self):
        """Enables removal buttons for all constraints."""
        self.remove_constraints_button.setEnabled(False)
        self.confirm_changes_button.show()

        for data in self.constraints_data:
            # Add remove button
            remove_button = QPushButton("-")
            remove_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #e74c3c; padding: 5px;")
            remove_button.setFixedSize(50, 50)
            remove_button.clicked.connect(lambda _, d=data: self.remove_constraint(d))
            data["layout"].addWidget(remove_button)

            # Add restore button (initially hidden)
            restore_button = QPushButton("⮌")
            restore_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #3498db; padding: 5px;")
            restore_button.setFixedSize(50, 50)
            restore_button.hide()
            restore_button.clicked.connect(lambda _, d=data: self.restore_constraint(d))
            data["layout"].addWidget(restore_button)

            data["remove_button"] = remove_button
            data["restore_button"] = restore_button

    def remove_constraint(self, data):
        """Marks a constraint as removed."""
        font = QFont(data["label"].font())
        font.setStrikeOut(True)
        data["label"].setFont(font)

        if data["input"]:
            data["input"].setEnabled(False)
            data["input"].setStyleSheet("font-size: 20px; color: #b3b3b3; background-color: #f7f7f7; padding: 5px;")

        data["remove_button"].hide()
        data["restore_button"].show()
        data["removed"] = True

    def restore_constraint(self, data):
        """Restores a removed constraint."""
        font = QFont(data["label"].font())
        font.setStrikeOut(False)
        data["label"].setFont(font)

        if data["input"]:
            data["input"].setEnabled(True)
            data["input"].setStyleSheet("font-size: 20px; color: #34495e; background-color: white; padding: 5px;")

        data["restore_button"].hide()
        data["remove_button"].show()
        data["removed"] = False

    def confirm_constraints_changes(self):
        """Finalizes the constraints changes."""
        for data in self.constraints_data:
            if "remove_button" in data:
                data["remove_button"].hide()
            if "restore_button" in data:
                data["restore_button"].hide()

        self.confirm_changes_button.hide()
        self.remove_constraints_button.setEnabled(True)

    def confirm_parameters(self):
        """Handles the confirm button click event."""
        removed_constraints = []  # Store removed constraint numbers
        parameter_values = []  # Store confirmed parameter values
        
        for i, data in enumerate(self.constraints_data):
            if data["removed"]:
                removed_constraints.append(f"constraint {i + 1}")  # Add constraint number to the list
            else:
                # Attempt to read input value only if the input exists and is not removed
                if data["input"]:
                    try:
                        parameter_values.append(float(data["input"].text()))
                    except ValueError:
                        QMessageBox.warning(self, "Invalid Input", f"Please enter a valid numeric value for constraint: {data['label'].text()}")
                        return

        # Assign T and M values only if they exist in the confirmed parameter values
        self.t_value = parameter_values[0] if len(parameter_values) > 0 else None
        self.m_value = parameter_values[1] if len(parameter_values) > 1 else None

        # Prepare the message box text
        message = f"The following parameters have been set:\n\n"
        if self.t_value is not None:
            message += f"T = {self.t_value} Dunam\n"
        if self.m_value is not None:
            message += f"M = {self.m_value}%\n"

        if removed_constraints:
            message += "\nRemoved Constraints:\n" + "\n".join(removed_constraints)
        else:
            message += "\nNo constraints were removed."

        # Display the message box
        QMessageBox.information(self, "Parameters Confirmed", message)


        self.removed_constraints = removed_constraints
        # Print parameter values and removed constraints for debugging
        print(f"T: {self.t_value}, M: {self.m_value}")
        print("Removed Constraints:", removed_constraints)
        # Close the application
        self.close()
        



# def activate_interface():
#     app = QApplication(sys.argv)
#     window = LinearProgrammingInterface()
#     window.show()
#     # window.destroy()
#     # sys.exit(app.exec_())

#     user_input_total_area_upper_bound = window.t_value
#     user_input_allowed_loss_from_influence_on_crops_percentage = window.m_value
#     return user_input_total_area_upper_bound, user_input_allowed_loss_from_influence_on_crops_percentage


def activate_interface():
    app = QApplication(sys.argv)
    window = LinearProgrammingInterface()
    window.show()
    app.exec_()  # Blocks until the window is closed
    return window.t_value, window.m_value, window.removed_constraints  # Return the parameters after closing



if __name__ == "__main__":
    user_input = activate_interface()
    user_input_total_area_upper_bound = user_input[0]
    user_input_allowed_loss_from_influence_on_crops_percentage = user_input[1]
    removed_constraints = user_input[2]
    print("user_input_total_area_upper_bound:",user_input_total_area_upper_bound)
    print("user_input_allowed_loss_from_influence_on_crops_percentage:",user_input_allowed_loss_from_influence_on_crops_percentage)
    print("removed_constraints:",removed_constraints)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = LinearProgrammingInterface()
#     window.show()
#     sys.exit(app.exec_())
