from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel, QPushButton, QLineEdit, QWidget, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication, QFont
import sys

dunam_upper_bound, allowed_loss_percentage = 0, 0


class LinearProgrammingInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.resize(800, 300)

    def init_ui(self):
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen_geometry.width(), screen_geometry.height())
        self.setWindowTitle("Choose Your Agriplots Model")
        self.setStyleSheet("background-color: #f7f9fb;")

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 10, 30, 10)
        self.layout.setSpacing(10)

        header = QLabel("Choose Your Agriplots Model")
        header.setStyleSheet("font-size: 50px; font-weight: bold; color: white; background-color: #2e86c1; padding: 20px;")
        header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(header)

        objective_function = QLabel(
            '<p style="font-size: 40px; color: #41a3e0;"><b>Objective Function</b></p>'
            '<p style="font-size: 30px; color: #34495e;">Maximize <b>Total Energy Production</b></p>'
        )
        objective_function.setTextFormat(Qt.RichText)
        self.layout.addWidget(objective_function)

        constraints = QLabel('<p style="font-size: 40px; color: #41a3e0;"><b>Constraints</b></p>')
        constraints.setTextFormat(Qt.RichText)
        self.layout.addWidget(constraints)

        # List to store constraint data
        self.constraints_data = []

        # Add each constraint with indicative names
        self.add_constraint("Total Area PV Installations ≤", "Dunam", True, name="total_area_constraint")
        self.add_constraint("Percentage Change in Revenue ≤", "%", True, can_remove=False, name="revenue_change_constraint")
        self.add_constraint("Total Energy Production of yeshuv ≤ <b>Total Energy Consumption of yeshuv</b>", "", False, name="energy_production_per_yeshuv_constraint")
        self.add_constraint("Total Energy Production of machoz ≤ <b>Total Energy Consumption of machoz</b>", "", False, name="energy_production_per_machoz_constraint", default_removed=True)

        self.remove_constraints_button = QPushButton("Remove Constraints")
        self.remove_constraints_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #e74c3c; padding: 5px 10px;")
        self.remove_constraints_button.setFixedSize(400, 50)
        self.remove_constraints_button.clicked.connect(self.enable_constraints_removal)
        self.layout.addWidget(self.remove_constraints_button, alignment=Qt.AlignLeft)

        self.confirm_changes_button = QPushButton("✓")
        self.confirm_changes_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #27ae60; padding: 5px;")
        self.confirm_changes_button.setFixedSize(50, 50)
        self.confirm_changes_button.clicked.connect(self.confirm_constraints_changes)
        self.confirm_changes_button.hide()
        self.layout.addWidget(self.confirm_changes_button, alignment=Qt.AlignLeft)

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #27ae60; padding: 5px 10px;")
        self.confirm_button.setFixedSize(150, 50)
        self.confirm_button.clicked.connect(self.confirm_parameters)
        self.layout.addWidget(self.confirm_button, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

        # Variables to hold parameter values
        self.dunam_upper_bound_value = None
        self.allowed_loss_percentage_value = None
        self.removed_constraints = []

    def add_constraint(self, text, unit, has_input, can_remove=True, name=None, default_removed=False):
        """Adds a constraint to the layout."""
        constraint_layout = QHBoxLayout()

        constraint_label = QLabel(text)
        constraint_label.setStyleSheet("font-size: 20px; color: #34495e;")
        constraint_label.setTextFormat(Qt.RichText)
        constraint_layout.addWidget(constraint_label)

        input_field = None
        if has_input:
            input_field = QLineEdit()
            input_field.setStyleSheet("font-size: 20px; color: #34495e; background-color: white; padding: 5px;")
            input_field.setFixedWidth(100)
            constraint_layout.addWidget(input_field)

            unit_label = QLabel(unit)
            unit_label.setStyleSheet("font-size: 20px; color: #34495e;")
            constraint_layout.addWidget(unit_label)

        self.layout.addLayout(constraint_layout)

        # Define initial state (removed or not)
        removed = default_removed
        if default_removed:
            # Mark the constraint as removed (strike-through)
            font = QFont(constraint_label.font())
            font.setStrikeOut(True)
            constraint_label.setFont(font)

        self.constraints_data.append({
            "layout": constraint_layout,
            "label": constraint_label,
            "input": input_field,
            "removed": removed,
            "can_remove": can_remove,
            "name": name
        })

    def enable_constraints_removal(self):
        self.remove_constraints_button.setEnabled(False)
        self.confirm_changes_button.show()

        for i, data in enumerate(self.constraints_data):
            if not data["can_remove"]:
                continue

            remove_button = QPushButton("-")
            remove_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #e74c3c; padding: 5px;")
            remove_button.setFixedSize(50, 50)
            remove_button.clicked.connect(lambda _, d=data, idx=i: self.remove_constraint(d, idx))
            data["layout"].addWidget(remove_button)

            restore_button = QPushButton("⮌")
            restore_button.setStyleSheet("font-size: 20px; font-weight: bold; color: white; background-color: #3498db; padding: 5px;")
            restore_button.setFixedSize(50, 50)
            restore_button.hide()
            restore_button.clicked.connect(lambda _, d=data, idx=i: self.restore_constraint(d, idx))
            data["layout"].addWidget(restore_button)

            data["remove_button"] = remove_button
            data["restore_button"] = restore_button

            # Hide buttons based on initial state
            if data["removed"]:
                remove_button.hide()
                restore_button.show()

    def remove_constraint(self, data, index):
        """Marks a constraint as removed and ensures mutual exclusivity for constraints 3 and 4."""
        font = QFont(data["label"].font())
        font.setStrikeOut(True)
        data["label"].setFont(font)

        if data["input"]:
            data["input"].setEnabled(False)
            data["input"].setStyleSheet("font-size: 20px; color: #b3b3b3; background-color: #f7f7f7; padding: 5px;")

        data["remove_button"].hide()
        data["restore_button"].show()
        data["removed"] = True

        if data["name"] == "energy_production_per_yeshuv_constraint":
            self.restore_constraint(self.constraints_data[3], 3)
        elif data["name"] == "energy_production_per_machoz_constraint":
            self.restore_constraint(self.constraints_data[2], 2)

    def restore_constraint(self, data, index):
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
        removed_constraints = []  # Store removed constraint names (unmodified)
        parameter_values = {}  # Store confirmed parameter values with their names

        for data in self.constraints_data:
            if data["removed"]:
                removed_constraints.append(data["name"])  # Use the raw name field directly
            else:
                if data["input"]:
                    try:
                        value = float(data["input"].text())
                        parameter_values[data["name"]] = value
                    except ValueError:
                        QMessageBox.warning(self, "Invalid Input", f"Please enter a valid numeric value for constraint: {data['label'].text()}")
                        return

        self.dunam_upper_bound_value = parameter_values.get("total_area_constraint")
        self.allowed_loss_percentage_value = parameter_values.get("revenue_change_constraint")

        message = f"The following parameters have been set:\n\n"
        if self.dunam_upper_bound_value is not None:
            message += f"Dunam Upper Bound = {self.dunam_upper_bound_value} Dunam\n"
        if self.allowed_loss_percentage_value is not None:
            message += f"Allowed Loss Percentage = {self.allowed_loss_percentage_value}%\n"

        if removed_constraints:
            message += "\nRemoved Constraints:\n" + "\n".join(removed_constraints)
        else:
            message += "\nNo constraints were removed."

        QMessageBox.information(self, "Parameters Confirmed", message)

        self.removed_constraints = removed_constraints
        print(f"Dunam Upper Bound: {self.dunam_upper_bound_value}, Allowed Loss Percentage: {self.allowed_loss_percentage_value}")
        print("Removed Constraints:", removed_constraints)
        self.close()


def activate_interface():
    app = QApplication(sys.argv)
    window = LinearProgrammingInterface()
    window.show()
    app.exec_()
    return window.dunam_upper_bound_value, window.allowed_loss_percentage_value, window.removed_constraints


if __name__ == "__main__":
    user_input = activate_interface()
    user_input_dunam_upper_bound = user_input[0]
    user_input_allowed_loss_percentage = user_input[1]
    removed_constraints = user_input[2]
    print("Dunam Upper Bound:", user_input_dunam_upper_bound)
    print("Allowed Loss Percentage:", user_input_allowed_loss_percentage)
    print("Removed Constraints:", removed_constraints)
