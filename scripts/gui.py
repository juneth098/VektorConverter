import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import threading
import main  # your main.py with run_conversion()

class ConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Conversion Tool")
        self.geometry("500x380")
        self.resizable(False, False)

        # Variables
        self.input_file = tk.StringVar()
        self.input_type = tk.StringVar(value="ate")
        self.output_type = tk.StringVar(value="vec")
        self.dec_file = None
        self.interval = None

        # Store output radio buttons
        self.output_buttons = {}
        self.convert_button = None

        # Widgets
        self.create_widgets()

    def create_widgets(self):
        # Input File
        tk.Label(self, text="Input File:").pack(anchor="w", padx=10, pady=5)
        frame = tk.Frame(self)
        frame.pack(fill="x", padx=10)
        tk.Entry(frame, textvariable=self.input_file, width=50).pack(side="left")
        tk.Button(frame, text="Browse", command=self.browse_file).pack(side="left", padx=5)

        # Input Type
        tk.Label(self, text="Input Type:").pack(anchor="w", padx=10, pady=5)
        self.input_frame = tk.Frame(self)
        self.input_frame.pack(anchor="w", padx=10)
        self.input_rbs = {}
        for t in ["ate", "stil", "vcd", "vec"]:
            rb = tk.Radiobutton(self.input_frame, text=t.upper(), variable=self.input_type, value=t,
                                command=self.update_output_options, state="disabled")
            rb.pack(side="left", padx=5)
            self.input_rbs[t] = rb

        # Output Type
        tk.Label(self, text="Output Type:").pack(anchor="w", padx=10, pady=5)
        self.output_frame = tk.Frame(self)
        self.output_frame.pack(anchor="w", padx=10)
        for t in ["vec", "j750", "C3380", "C3850"]:
            rb = tk.Radiobutton(self.output_frame, text=t.upper(), variable=self.output_type, value=t,
                                command=self.check_dec_requirement, state="disabled")
            rb.pack(side="left", padx=5)
            self.output_buttons[t] = rb

        # Convert Button
        self.convert_button = tk.Button(self, text="Convert", command=self.convert, state="disabled")
        self.convert_button.pack(pady=10)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

    def browse_file(self):
        file = filedialog.askopenfilename(title="Select input file")
        if file:
            self.input_file.set(file)
            # Enable radio buttons and convert button
            for rb in self.input_rbs.values():
                rb.config(state="normal")
            for rb in self.output_buttons.values():
                rb.config(state="normal")
            self.convert_button.config(state="normal")
            self.update_output_options()
            self.check_dec_requirement()

    def update_output_options(self):
        # Disable Vec output if input type is Vec
        input_type = self.input_type.get()
        if input_type == "vec":
            self.output_buttons["vec"].config(state="disabled")
            if self.output_type.get() == "vec":
                self.output_type.set("j750")
        else:
            self.output_buttons["vec"].config(state="normal")
        self.check_dec_requirement()

    def check_dec_requirement(self):
        output_type = self.output_type.get().upper()
        input_ext = os.path.splitext(self.input_file.get())[1].lower()
        input_type = self.input_type.get()

        requires_dec = False
        # DEC required for Chroma outputs
        if output_type in ["C3380", "C3850"]:
            if (input_type == "ate" and input_ext in [".pat", ".atp"]) or input_type == "vec":
                requires_dec = True

        if requires_dec:
            dec_file = filedialog.askopenfilename(title="Select DEC file")
            if not dec_file:
                messagebox.showerror("Error", "DEC file is required for Chroma conversion")
                self.output_type.set("j750")
                self.dec_file = None
                self.status_var.set("Ready")
                return

            # Only keep filename
            self.dec_file = f"./{os.path.basename(dec_file)}"
            self.status_var.set("Processing DEC file...")

            # Simulate DEC processing in background
            def process_dec():
                import time
                time.sleep(3)  # simulate DEC processing
                self.status_var.set("Ready")

            threading.Thread(target=process_dec).start()
        else:
            self.dec_file = None
            self.status_var.set("Ready")

    def convert(self):
        file_path = self.input_file.get().strip()
        if not file_path or not os.path.isfile(file_path):
            messagebox.showerror("Error", "Please select a valid input file")
            return

        input_ext = os.path.splitext(file_path)[1].lower()
        input_type = self.input_type.get()
        output_type = self.output_type.get().upper()

        # Validate input vs file
        valid_ext = {
            "ate": [".atp", ".pat"],
            "stil": [".stil"],
            "vcd": [".vcd"],
            "vec": [".vec"]
        }
        if input_ext not in valid_ext.get(input_type, []):
            messagebox.showerror("Error", f"Input type {input_type.upper()} does not match file extension {input_ext}")
            return

        # Handle "Same type" error: ATP → J750
        if input_type == "ate" and output_type == "J750" and input_ext == ".atp":
            messagebox.showerror("Error", "Same file type conversion is not allowed")
            return

        # Handle VCD interval
        interval = None
        if input_type == "vcd":
            interval = simpledialog.askinteger(
                "VCD Interval",
                "Enter timing interval (ns, e.g. 41665):",
                minvalue=1
            )
            if interval is None:
                return

        try:
            # ----------- ATE input -----------
            if input_type == "ate":
                main.run_conversion(file_path, ate_type=output_type, dec_file=self.dec_file)

            # ----------- STIL/VCD input -----------
            elif input_type in ["stil", "vcd"]:
                if output_type.lower() == "vec":
                    main.run_conversion(file_path, interval=interval)
                else:
                    if input_type == "stil":
                        vec_file, cmf_file = main.stil2vec.convert_stil_to_vec(file_path)
                    else:  # vcd
                        vec_file, cmf_file = main.vcd2vec.convert_vcd_to_vec(file_path, interval)
                    main.run_conversion(vec_file, ate_type=output_type, dec_file=self.dec_file)

            # ----------- VEC input -----------
            elif input_type == "vec":
                main.run_conversion(file_path, ate_type=output_type, dec_file=self.dec_file)

            messagebox.showinfo("Success", "Conversion completed successfully!")
            self.status_var.set("Ready")

        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed:\n{e}")
            self.status_var.set("Ready")


if __name__ == "__main__":
    app = ConverterGUI()
    app.mainloop()
