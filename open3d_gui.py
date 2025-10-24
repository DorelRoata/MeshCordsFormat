import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import sys

class MeshAlignmentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Mesh Alignment Tool")
        self.root.geometry("800x650")
        self.root.resizable(True, True)

        # Center the window on screen
        self.root.update_idletasks()
        window_width = 800
        window_height = 650
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.output_format = tk.StringVar(value="stl")
        self.downsample_enabled = tk.BooleanVar(value=False)
        self.downsample_ratio = tk.DoubleVar(value=0.5)

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_label = tk.Label(
            title_frame,
            text="3D Mesh Coordinate Alignment Tool",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)

        # Main content frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input file section
        input_label = tk.Label(main_frame, text="Input File:", font=("Arial", 10, "bold"))
        input_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        input_frame = tk.Frame(main_frame)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        input_frame.columnconfigure(0, weight=1)

        input_entry = tk.Entry(input_frame, textvariable=self.input_file, width=50)
        input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        input_btn = tk.Button(
            input_frame,
            text="Browse",
            command=self.browse_input,
            bg="#3498db",
            fg="white",
            width=10
        )
        input_btn.grid(row=0, column=1)

        # Output file section
        output_label = tk.Label(main_frame, text="Output File:", font=("Arial", 10, "bold"))
        output_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

        output_frame = tk.Frame(main_frame)
        output_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        output_frame.columnconfigure(0, weight=1)

        output_entry = tk.Entry(output_frame, textvariable=self.output_file, width=50)
        output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        output_btn = tk.Button(
            output_frame,
            text="Browse",
            command=self.browse_output,
            bg="#3498db",
            fg="white",
            width=10
        )
        output_btn.grid(row=0, column=1)

        # Format selection section
        format_label = tk.Label(main_frame, text="Output Format:", font=("Arial", 10, "bold"))
        format_label.grid(row=4, column=0, sticky="w", pady=(0, 5))

        format_frame = tk.Frame(main_frame)
        format_frame.grid(row=5, column=0, sticky="ew", pady=(0, 15))

        # Only formats actually supported by trimesh
        formats = [
            ("STL - Standard Tessellation Language (Binary)", "stl"),
            ("STL ASCII - Standard Tessellation Language (Text)", "stl_ascii"),
            ("PLY - Polygon File Format", "ply"),
            ("OBJ - Wavefront OBJ", "obj"),
            ("OFF - Object File Format", "off"),
            ("GLB - GL Transmission Format (Binary) [Recommended]", "glb"),
            ("GLTF - GL Transmission Format (JSON)", "gltf"),
            ("COLLADA - Collaborative Design Activity", "dae")
        ]

        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.output_format,
            values=[f[1] for f in formats],
            state="readonly",
            width=15
        )
        format_combo.grid(row=0, column=0, sticky="w")
        format_combo.current(0)
        format_combo.bind("<<ComboboxSelected>>", self.on_format_change)

        format_desc = tk.Label(
            format_frame,
            text="← Select the desired output file format",
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        format_desc.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Downsample section
        downsample_check = tk.Checkbutton(
            main_frame,
            text="Enable Downsampling (reduce mesh complexity)",
            variable=self.downsample_enabled,
            font=("Arial", 10, "bold"),
            command=self.toggle_downsample
        )
        downsample_check.grid(row=6, column=0, sticky="w", pady=(10, 5))

        self.downsample_frame = tk.Frame(main_frame)
        self.downsample_frame.grid(row=7, column=0, sticky="ew", pady=(0, 15))

        ratio_label = tk.Label(
            self.downsample_frame,
            text="Target Ratio:",
            font=("Arial", 9)
        )
        ratio_label.grid(row=0, column=0, sticky="w")

        self.ratio_scale = tk.Scale(
            self.downsample_frame,
            from_=0.1,
            to=1.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.downsample_ratio,
            length=200,
            state=tk.NORMAL
        )
        self.ratio_scale.grid(row=0, column=1, padx=(10, 10))

        self.ratio_value_label = tk.Label(
            self.downsample_frame,
            text="(0.5 = 50% faces)",
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        self.ratio_value_label.grid(row=0, column=2, sticky="w")

        # Instructions section
        instructions_frame = tk.LabelFrame(
            main_frame,
            text="Instructions",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=10
        )
        instructions_frame.grid(row=8, column=0, sticky="ew", pady=(10, 15))

        instructions_text = (
            "1. Select your input 3D mesh file\n"
            "2. Choose where to save the output file\n"
            "3. Select your desired output format\n"
            "4. (Optional) Enable downsampling to reduce mesh size\n"
            "5. Click 'Start Alignment' to begin\n"
            "6. Follow the interactive 3D viewer to select 3 points"
        )

        instructions_label = tk.Label(
            instructions_frame,
            text=instructions_text,
            font=("Arial", 9),
            justify=tk.LEFT,
            fg="#2c3e50"
        )
        instructions_label.pack(anchor="w")

        # Start button
        start_btn = tk.Button(
            main_frame,
            text="Start Alignment Process",
            command=self.start_alignment,
            bg="#27ae60",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            cursor="hand2"
        )
        start_btn.grid(row=9, column=0, sticky="ew", pady=(10, 0))

        # Make main frame expand
        main_frame.columnconfigure(0, weight=1)

    def toggle_downsample(self):
        if self.downsample_enabled.get():
            self.ratio_scale.config(state=tk.NORMAL)
        else:
            self.ratio_scale.config(state=tk.DISABLED)

    def on_format_change(self, event=None):
        """Update output file extension when format changes"""
        current_output = self.output_file.get()
        if current_output:
            # Get the base filename without extension
            base = os.path.splitext(current_output)[0]
            # Update with new extension
            new_ext = self.output_format.get()
            self.output_file.set(f"{base}.{new_ext}")

    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Select Input 3D File",
            filetypes=[
                ("All Supported 3D Files", "*.stl *.obj *.ply *.off *.gltf *.glb *.dae *.3mf"),
                ("STL files", "*.stl"),
                ("PLY files", "*.ply"),
                ("OBJ files", "*.obj"),
                ("GLB/GLTF files", "*.glb *.gltf"),
                ("COLLADA files", "*.dae"),
                ("OFF files", "*.off"),
                ("3MF files", "*.3mf"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.input_file.set(filename)
            # Auto-suggest output filename
            if not self.output_file.get():
                base = os.path.splitext(filename)[0]
                ext = self.output_format.get()
                self.output_file.set(f"{base}_aligned.{ext}")

    def browse_output(self):
        ext = self.output_format.get()
        filename = filedialog.asksaveasfilename(
            title="Save Output File As",
            defaultextension=f".{ext}",
            filetypes=[
                (f"{ext.upper()} files", f"*.{ext}"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.output_file.set(filename)

    def start_alignment(self):
        # Validate inputs
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file!")
            return

        if not self.output_file.get():
            messagebox.showerror("Error", "Please specify an output file!")
            return

        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("Error", "Input file does not exist!")
            return

        # Build command
        script_path = os.path.join(os.path.dirname(__file__), "open3dv1.py")
        cmd = [
            sys.executable,
            script_path,
            self.input_file.get(),
            self.output_file.get(),
            "--format",
            self.output_format.get()
        ]

        if self.downsample_enabled.get():
            cmd.extend(["--downsample", str(self.downsample_ratio.get())])

        # Run the command directly (no popup)
        try:
            # Minimize this window
            self.root.iconify()

            # Run the subprocess
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True,
                cwd=os.path.dirname(script_path)
            )

            # Restore window
            self.root.deiconify()

            if result.returncode == 0:
                messagebox.showinfo(
                    "Success",
                    f"Alignment completed successfully!\n\nOutput saved to:\n{self.output_file.get()}"
                )
            else:
                messagebox.showerror(
                    "Error",
                    f"Alignment process failed.\nPlease check the console for error messages."
                )

        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Error", f"Failed to start alignment process:\n{str(e)}")

def main():
    root = tk.Tk()
    app = MeshAlignmentGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
