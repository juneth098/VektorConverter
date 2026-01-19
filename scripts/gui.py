# gui.py
# Copyright (c) 2025 Juneth Viktor Ellon Moreno
# All rights reserved

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import main
import metadata
import webbrowser
import logger
import builtins
from datetime import datetime

now = datetime.now()


class ConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # Initialize logger once (console always on)
        logger.init_logger()

        # Variables
        self.input_file = tk.StringVar()
        self.input_type = tk.StringVar()
        self.output_type = tk.StringVar(value="vec")
        self.dec_file = None
        self.interval = None
        self.logging_enabled = tk.BooleanVar(value=False)

        # Store radio buttons
        self.input_rbs = {}
        self.output_buttons = {}
        self.convert_button = None

        self.title(f"VektorConverter v{metadata.script_ver}")
        self.geometry("600x420")
        self.resizable(False, False)

        self.create_widgets()

        # Override print() for logging when checkbox is enabled
        self.original_print = builtins.print
        builtins.print = self.print_override

        # Override status_var.set to log messages with timestamps
        self.original_status_set = self._wrap_status_set()

        # ---- Call cleanup logger on GUI close ----
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # -------------------- Create Widgets --------------------
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
            rb = tk.Radiobutton(
                self.input_frame, text=t.upper(),
                variable=self.input_type, value=t,
                state="disabled"
            )
            rb.pack(side="left", padx=10)
            self.input_rbs[t] = rb

        # Output Type
        tk.Label(self, text="Output Type:").pack(anchor="center", pady=5)
        self.output_frame = tk.Frame(self)
        self.output_frame.pack(anchor="center", pady=5)
        for t in ["vec", "j750", "C3380"]:#"C3850"]: for development
            rb = tk.Radiobutton(
        	self.output_frame, text=t.upper(),
        	variable=self.output_type, value=t,
        	command=self.check_dec_requirement,
            state="normal"
    	   )
            rb.pack(side="left", padx=10)
            self.output_buttons[t] = rb

        # Logging Checkbox
        self.log_checkbox = tk.Checkbutton(
            self, text="Enable Logging",
            variable=self.logging_enabled,
            command=self.toggle_logging
        )
        self.log_checkbox.pack(pady=5)

        # Convert Button
        self.convert_button = tk.Button(self, text="Convert", command=self.convert, state="disabled")
        self.convert_button.pack(pady=10)

        # About Button
        self.about_button = tk.Button(self, text="About", command=self.show_about)
        self.about_button.pack(pady=5)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

    # -------------------- Logger toggle --------------------
    def toggle_logging(self):
        if self.logging_enabled.get():
            logger.enable_file_logging()
            self.status_var.set("Logging enabled")
        else:
            logger.disable_file_logging()
            self.status_var.set("Logging disabled")

    # -------------------- Override print --------------------
    def print_override(self, *args, **kwargs):
        self.original_print(*args, **kwargs)
        if self.logging_enabled.get():
            msg = " ".join(str(a) for a in args)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.log(f"{timestamp} | {msg}")

    # -------------------- Wrap status_var.set --------------------
    def _wrap_status_set(self):
        orig_set = self.status_var.set

        def new_set(value):
            orig_set(value)
            if self.logging_enabled.get():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.log(f"{timestamp} | STATUS: {value}")

        self.status_var.set = new_set
        return orig_set

    # -------------------- Browse and auto-detect --------------------
    def browse_file(self):
        self.status_var.set("Select Vector File")
        file = filedialog.askopenfilename(title="Select input file")

        if file:
            self.input_file.set(file)
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

            for rb in self.input_rbs.values():
                rb.config(state="disabled")

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

        #if output_type in ["C3380", "C3850"]:
        if output_type =="C3380":
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
        #J750 atp to atp
        if input_type == "ate" and output_type == "J750" and input_ext == ".atp":
            messagebox.showerror("Error", "Same file type conversion is not allowed")
            self.status_var.set("ERROR")
            return
        #Chroma pat to pat
        if input_type == "ate" and output_type == "C3380" and input_ext == ".pat":
            messagebox.showerror("Error", "Same file type conversion is not allowed")
            self.status_var.set("ERROR")
            return

        interval = None
        if input_type == "vcd":
            interval = simpledialog.askinteger(
                "VCD Interval",
                "Enter timing interval (ns, e.g. 41665):",
                minvalue=1
            )
            if interval is None:
                messagebox.showerror("Error", "Enter valid timing")
                return

        try:
            main.run_conversion(file_path, ate_type=output_type, dec_file=self.dec_file, interval=interval)
            self.status_var.set("Conversion completed successfully!")
            messagebox.showinfo("Success", "Conversion completed successfully!")
        except Exception as e:
            self.status_var.set("ERROR")
            messagebox.showerror("Error", f"Conversion failed:\n{e}")

    # -------------------- Close window --------------------
    def on_close(self):
        if self.logging_enabled.get():
            logger.disable_file_logging()
        builtins.print = self.original_print
        self.status_var.set = self.original_status_set
        self.destroy()

    # -------------------- About window --------------------
    def show_about(self):
        try:
            author = metadata.author
            version = metadata.script_ver
        except AttributeError:
            author = "Unknown"
            version = "N/A"

        github_url = "https://github.com/juneth098/VektorConverter"

        about_win = tk.Toplevel(self)
        about_win.title("About VektorConverter")
        about_win.resizable(False, False)
        about_win.geometry("400x200")

        info_text = (
            f"VektorConverter\n"
            f"Version: {version}\n\n"
            f"Copyright (c) 2025 {author}\n"
            f"All rights reserved"
        )
        tk.Label(about_win, text=info_text, justify="left").pack(pady=(10, 5), padx=10, anchor="w")

        def open_github(event):
            webbrowser.open_new(github_url)

        link = tk.Label(about_win, text=github_url, fg="blue", cursor="hand2")
        link.pack(pady=(5, 10), padx=10, anchor="w")
        link.bind("<Button-1>", open_github)

        tk.Button(about_win, text="Close", command=about_win.destroy).pack(pady=10)


if __name__ == "__main__":
    app = ConverterGUI()
    app.mainloop()
