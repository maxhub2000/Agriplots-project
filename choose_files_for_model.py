import tkinter as tk

def open_file_selector():
    global opl_model_file, dataset_path, mod_selected_button, xlsx_selected_button
    opl_model_file = ""
    dataset_path = ""

    mod_selected_button = None
    xlsx_selected_button = None

    def set_mod_file_path(path, button):
        global opl_model_file, mod_selected_button
        opl_model_file = path
        mod_file_label.config(text=opl_model_file)
        
        # Update button states
        if mod_selected_button:
            mod_selected_button.config(bg="#3498DB")  # Reset the previous button color
        button.config(bg="#1ABC9C")  # Highlight the selected button
        mod_selected_button = button

    def set_xlsx_file_path(path, button):
        global dataset_path, xlsx_selected_button
        dataset_path = path
        xlsx_file_label.config(text=dataset_path)
        
        # Update button states
        if xlsx_selected_button:
            xlsx_selected_button.config(bg="#E74C3C")  # Reset the previous button color
        button.config(bg="#1ABC9C")  # Highlight the selected button
        xlsx_selected_button = button

    def confirm_selection():
        window.destroy()  # Close the window

    window = tk.Tk()
    window.title("File Selector")
    window.state("zoomed")  # Open in maximized mode with standard window controls
    window.configure(bg="#2C3E50")

    # Title label (centered)
    tk.Label(
        window,
        text="Choose Model Configuration",
        font=("Helvetica", 40, "bold"),
        fg="#ECF0F1",
        bg="#2C3E50"
    ).pack(pady=20)

    # .mod file section (aligned left)
    frame = tk.Frame(window, bg="#2C3E50")
    frame.pack(anchor="w", padx=20)

    tk.Label(
        frame, text="Select a model to run:", font=("Helvetica", 30), fg="#ECF0F1", bg="#2C3E50"
    ).pack(pady=15, anchor="w")

    mod_file_path_1 = "models/basic_model/Agriplots_basic_model.mod"
    mod_file_path_2 = "models/advanced_model/Agriplots_advanced_model.mod"
    mod_file_path_3 = "models/advanced_model/Agriplots_basic_model.mod"
    mod_file_path_4 = "models/advanced_model_with_gini/Agriplots_basic_model_with_gini.mod"

    mod_button_1 = tk.Button(
        frame, text="basic model", command=lambda: set_mod_file_path(mod_file_path_1, mod_button_1),
        bg="#3498DB", fg="#ECF0F1", font=("Helvetica", 20), relief="raised", bd=5, width=20
    )
    mod_button_1.pack(pady=5, anchor="w")
    mod_button_2 = tk.Button(
        frame, text="advanced model", command=lambda: set_mod_file_path(mod_file_path_2, mod_button_2),
        bg="#3498DB", fg="#ECF0F1", font=("Helvetica", 20), relief="raised", bd=5, width=20
    )
    mod_button_2.pack(pady=5, anchor="w")
    mod_button_3 = tk.Button(
        frame, text="basic model with gini", command=lambda: set_mod_file_path(mod_file_path_3, mod_button_3),
        bg="#3498DB", fg="#ECF0F1", font=("Helvetica", 20), relief="raised", bd=5, width=20
    )
    mod_button_3.pack(pady=5, anchor="w")
    mod_button_4 = tk.Button(
        frame, text="advanced model with gini", command=lambda: set_mod_file_path(mod_file_path_4, mod_button_4),
        bg="#3498DB", fg="#ECF0F1", font=("Helvetica", 20), relief="raised", bd=5, width=20
    )
    mod_button_4.pack(pady=5, anchor="w")

    global mod_file_label
    mod_file_label = tk.Label(frame, text="", fg="#1ABC9C", bg="#2C3E50", font=("Helvetica", 20))
    mod_file_label.pack(pady=10, anchor="w")

    tk.Label(
        frame, text="Select input dataset:", font=("Helvetica", 30), fg="#ECF0F1", bg="#2C3E50"
    ).pack(pady=15, anchor="w")

    xlsx_file_path_1 = "Agriplots dataset - 1000 rows.xlsx"
    xlsx_file_path_2 = "Agriplots dataset - 10000 rows.xlsx"
    xlsx_file_path_3 = "Agriplots_final - Feasible Fields.xlsx"

    xlsx_button_1 = tk.Button(
        frame, text="1,000 rows dataset", command=lambda: set_xlsx_file_path(xlsx_file_path_1, xlsx_button_1),
        bg="#E74C3C", fg="#ECF0F1", font=("Helvetica", 20), relief="raised", bd=5, width=20
    )
    xlsx_button_1.pack(pady=5, anchor="w")
    xlsx_button_2 = tk.Button(
        frame, text="10,000 rows dataset", command=lambda: set_xlsx_file_path(xlsx_file_path_2, xlsx_button_2),
        bg="#E74C3C", fg="#ECF0F1", font=("Helvetica", 20), relief="raised", bd=5, width=20
    )
    xlsx_button_2.pack(pady=5, anchor="w")
    xlsx_button_3 = tk.Button(
        frame, text="full dataset", command=lambda: set_xlsx_file_path(xlsx_file_path_3, xlsx_button_3),
        bg="#E74C3C", fg="#ECF0F1", font=("Helvetica", 20), relief="raised", bd=5, width=20
    )
    xlsx_button_3.pack(pady=5, anchor="w")

    global xlsx_file_label
    xlsx_file_label = tk.Label(frame, text="", fg="#1ABC9C", bg="#2C3E50", font=("Helvetica", 20))
    xlsx_file_label.pack(pady=10, anchor="w")

    tk.Button(
        frame, text="Run Model", command=confirm_selection,
        bg="#2ECC71", fg="#ECF0F1", font=("Helvetica", 25, "bold"), relief="raised", bd=5, width=15
    ).pack(pady=30, anchor="w")

    window.mainloop()

    return opl_model_file, dataset_path

# Call the function and get the selected file paths
#opl_model_file, dataset_path = open_file_selector()

# Use opl_model_file and dataset_path variables as needed
#print("Selected .mod file path:", opl_model_file)
#print("Selected .xlsx file path:", dataset_path)
