# gui.py
# Copyright (c) 2025 Juneth Viktor Ellon Moreno
# All rights reserved

import tkinter as tk
from importlib.metadata import metadata
from tkinter import filedialog, messagebox, simpledialog
import os
import threading
import main  # your main.py with run_conversion()
import metadata
import webbrowser

class ConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"VektorConverter v{metadata.script_ver}")
        self.geometry("600x380")
        self.resizable(False, False)

        # Variables
        self.input_file = tk.StringVar()
        self.input_type = tk.StringVar()
        self.output_type = tk.StringVar(value="vec")
        self.dec_file = None
        self.interval = None

        # Store radio buttons
        self.input_rbs = {}
        self.output_buttons = {}
        self.convert_button = None

        self.create_widgets()

    def create_widgets(self):
        # Input File
        tk.Label(self, text="Vector File:").pack(anchor="center", pady=5)
        frame = tk.Frame(self)
        frame.pack(anchor="center", pady=5)
        tk.Entry(frame, textvariable=self.input_file, width=50).pack(side="left")
        tk.Button(frame, text="Browse", command=self.browse_file).pack(side="left", padx=5)

        # Input Type
        tk.Label(self, text="Input Type:").pack(anchor="center", pady=5)
        self.input_frame = tk.Frame(self)
        self.input_frame.pack(anchor="center", pady=5)
        for t in ["ate", "stil", "vcd", "vec"]:
            rb = tk.Radiobutton(self.input_frame, text=t.upper(), variable=self.input_type, value=t,
                                state="disabled")  # Locked initially
            rb.pack(side="left", padx=10)
            self.input_rbs[t] = rb

        # Output Type
        tk.Label(self, text="Output Type:").pack(anchor="center", pady=5)
        self.output_frame = tk.Frame(self)
        self.output_frame.pack(anchor="center", pady=5)
        for t in ["vec", "j750", "C3380", "C3850"]:
            rb = tk.Radiobutton(self.output_frame, text=t.upper(), variable=self.output_type, value=t,
                                command=self.check_dec_requirement, state="disabled")
            rb.pack(side="left", padx=10)
            self.output_buttons[t] = rb

        # Convert Button
        self.convert_button = tk.Button(self, text="Convert", command=self.convert, state="disabled")
        self.convert_button.pack(pady=20)

        # About Button
        self.about_button = tk.Button(self, text="About", command=self.show_about)
        self.about_button.pack(pady=5)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

    # -------------------- Browse and auto-detect --------------------
    def browse_file(self):
        self.status_var.set("Select Vector File")
        file = filedialog.askopenfilename(title="Select input file")

        if file:
            self.input_file.set(file)

            # Auto-select input type based on file extension
            ext = os.path.splitext(file)[1].lower()
            if ext in [".atp", ".pat"]:
                self.input_type.set("ate")
            elif ext == ".stil":
                self.input_type.set("stil")
            elif ext == ".vcd":
                self.input_type.set("vcd")
            elif ext == ".vec":
                self.input_type.set("vec")
            else:
                self.status_var.set("ERROR")
                messagebox.showerror("Error", f"Unsupported file type: {ext}")
                return

            # Lock input type radio buttons
            for rb in self.input_rbs.values():
                rb.config(state="disabled")

            # Enable output buttons and convert button
            for rb in self.output_buttons.values():
                rb.config(state="normal")
            self.convert_button.config(state="disabled")
            self.update_output_options()
            self.check_dec_requirement()
            self.convert_button.config(state="normal")


    # -------------------- Update output options --------------------
    def update_output_options(self):
        input_type = self.input_type.get()
        if input_type == "vec":
            self.status_var.set("Vec output disabled")
            self.output_buttons["vec"].config(state="disabled")
            if self.output_type.get() == "vec":
                self.output_type.set("j750")
        else:
            self.output_buttons["vec"].config(state="normal")
        self.check_dec_requirement()

    # -------------------- DEC requirement --------------------
    def check_dec_requirement(self):
        output_type = self.output_type.get().upper()
        input_ext = os.path.splitext(self.input_file.get())[1].lower()
        input_type = self.input_type.get()
        requires_dec = False

        if output_type in ["C3380", "C3850"]:
            if (input_type == "ate" and input_ext in [".pat", ".atp"]) or input_type in ["vec", "stil", "vcd"]:
                requires_dec = True
                self.status_var.set("DEC file required")

                self.convert_button.config(state="disabled")

        if requires_dec:
            dec_file = filedialog.askopenfilename(title="Select DEC file")
            if not dec_file:
                messagebox.showerror("Error", "DEC file is required for Chroma conversion")
                self.status_var.set("ERROR")
                self.output_type.set("j750")
                self.dec_file = None
                self.convert_button.config(state="normal")
                return
            self.status_var.set("Processing DEC file...")
            self.dec_file = f"./{os.path.basename(dec_file)}"
            self.convert_button.config(state="normal")
            self.status_var.set("Ready")

        else:
            self.dec_file = None
            self.status_var.set("Ready")

    # -------------------- Convert button --------------------
    def convert(self):
        file_path = self.input_file.get().strip()
        if not file_path or not os.path.isfile(file_path):
            messagebox.showerror("Error", "Please select a valid input file")
            return

        input_ext = os.path.splitext(file_path)[1].lower()
        input_type = self.input_type.get()
        output_type = self.output_type.get().upper()

        # Validate file vs input type
        valid_ext = {
            "ate": [".atp", ".pat"],
            "stil": [".stil"],
            "vcd": [".vcd"],
            "vec": [".vec"]
        }
        if input_ext not in valid_ext.get(input_type, []):
            messagebox.showerror("Error", f"Selected file ({input_ext}) does not match input type {input_type.upper()}")
            self.status_var.set("ERROR")
            return

        # Same-type check (ATP → J750)
        if input_type == "ate" and output_type == "J750" and input_ext == ".atp":
            messagebox.showerror("Error", "Same file type conversion is not allowed")
            self.status_var.set("ERROR")
            return

        # Handle VCD interval
        interval = None
        if input_type == "vcd":
            self.status_var.set("Enter Timing")
            interval = simpledialog.askinteger(
                "VCD Interval",
                "Enter timing interval (ns, e.g. 41665):",
                minvalue=1
            )
            if interval is None:
                messagebox.showerror("Error", "Enter valid timing")
                self.status_var.set("ERROR")
                return

        # ---------------- Run conversion ----------------
        try:
            main.run_conversion(file_path, ate_type=output_type, dec_file=self.dec_file, interval=interval)
            messagebox.showinfo("Success", "Conversion completed successfully!")
            self.status_var.set("Done")
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed:\n{e}")
            self.status_var.set("ERROR")

    def show_about(self):
        try:
            author = metadata.author
            version = metadata.script_ver
        except AttributeError:
            author = "Unknown"
            version = "N/A"

        github_url = "https://github.com/juneth098/VektorConverter"

        # Create a new top-level window
        about_win = tk.Toplevel(self)
        about_win.title("About VektorConverter")
        about_win.resizable(False, False)
        about_win.geometry("400x200")

        # Tool info
        info_text = (
            f"VektorConverter\n"
            f"Version: {version}\n\n"
            f"Copyright (c) 2025 {author}\n"
            f"All rights reserved"
        )
        tk.Label(about_win, text=info_text, justify="left").pack(pady=(10, 5), padx=10, anchor="w")

        # Clickable GitHub link
        def open_github(event):
            webbrowser.open_new(github_url)

        link = tk.Label(about_win, text=github_url, fg="blue", cursor="hand2")
        link.pack(pady=(5, 10), padx=10, anchor="w")
        link.bind("<Button-1>", open_github)

        # Close button
        tk.Button(about_win, text="Close", command=about_win.destroy).pack(pady=10)

if __name__ == "__main__":
    app = ConverterGUI()
    app.mainloop()
