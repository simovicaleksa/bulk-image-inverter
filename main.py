#!/usr/bin/env python3
"""
Bulk Image Inverter GUI
A cross-platform application for batch inverting image colors.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image, ImageOps
import threading
import time
import os
import sys
import subprocess


class ImageInverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Image Inverter")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Variables
        self.image_paths = []
        self.output_dir = ""
        self.is_processing = False
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # --- Image Selection Section ---
        ttk.Label(main_frame, text="Select Images:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        image_btn_frame = ttk.Frame(main_frame)
        image_btn_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.select_images_btn = ttk.Button(
            image_btn_frame, 
            text="Browse Images...", 
            command=self.select_images
        )
        self.select_images_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.image_count_label = ttk.Label(image_btn_frame, text="No images selected")
        self.image_count_label.pack(side=tk.LEFT)
        
        self.reset_btn = ttk.Button(
            image_btn_frame,
            text="Reset",
            command=self.reset_images
        )
        self.reset_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # --- Output Directory Section ---
        ttk.Label(main_frame, text="Output Directory:").grid(
            row=1, column=0, sticky=tk.W, pady=(10, 5)
        )
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(10, 5))
        output_frame.columnconfigure(0, weight=1)
        
        self.output_entry = ttk.Entry(output_frame, state='readonly')
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.select_output_btn = ttk.Button(
            output_frame, 
            text="Browse...", 
            command=self.select_output_dir
        )
        self.select_output_btn.grid(row=0, column=1)
        
        # --- Image List Section ---
        ttk.Label(main_frame, text="Selected Images:").grid(
            row=2, column=0, sticky=(tk.W, tk.N), pady=(10, 5), columnspan=2
        )
        
        # Create frame for listbox and scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Listbox
        self.image_listbox = tk.Listbox(
            list_frame, 
            height=10,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED
        )
        self.image_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.image_listbox.yview)
        
        # --- Progress Section ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            mode='determinate',
            length=300
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.eta_label = ttk.Label(progress_frame, text="")
        self.eta_label.grid(row=1, column=0, sticky=tk.W)
        
        self.status_label = ttk.Label(progress_frame, text="Ready", foreground="gray")
        self.status_label.grid(row=2, column=0, sticky=tk.W)
        
        # --- Export Button ---
        self.export_btn = ttk.Button(
            main_frame, 
            text="Export Inverted Images", 
            command=self.start_export,
            state='disabled'
        )
        self.export_btn.grid(row=5, column=0, columnspan=2, pady=(15, 0))
        
        # Configure row weights for proper resizing
        main_frame.rowconfigure(3, weight=1)
        
    def select_images(self):
        """Open file dialog to select multiple images"""
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select Images to Invert",
            filetypes=filetypes
        )
        
        if files:
            self.image_paths = list(files)
            self.update_image_list()
            self.update_export_button()
    
    def reset_images(self):
        """Reset/clear all selected images but keep output directory"""
        self.image_paths = []
        self.update_image_list()
        self.update_export_button()
        
        # Reset progress display
        self.progress_bar['value'] = 0
        self.eta_label.config(text="")
        self.status_label.config(text="Ready", foreground="gray")
            
    def select_output_dir(self):
        """Open directory dialog to select output folder"""
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )
        
        if directory:
            self.output_dir = directory
            self.output_entry.config(state='normal')
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)
            self.output_entry.config(state='readonly')
            self.update_export_button()
            
    def update_image_list(self):
        """Update the listbox with selected image filenames"""
        self.image_listbox.delete(0, tk.END)
        
        for img_path in self.image_paths:
            filename = Path(img_path).name
            self.image_listbox.insert(tk.END, filename)
            
        # Update count label
        count = len(self.image_paths)
        self.image_count_label.config(
            text=f"{count} image{'s' if count != 1 else ''} selected"
        )
        
    def update_export_button(self):
        """Enable/disable export button based on selections"""
        if self.image_paths and self.output_dir and not self.is_processing:
            self.export_btn.config(state='normal')
        else:
            self.export_btn.config(state='disabled')
            
    def start_export(self):
        """Start the export process in a separate thread"""
        self.is_processing = True
        self.export_btn.config(state='disabled')
        self.select_images_btn.config(state='disabled')
        self.select_output_btn.config(state='disabled')
        self.reset_btn.config(state='disabled')
        
        # Reset progress
        self.progress_bar['value'] = 0
        self.eta_label.config(text="Calculating...")
        self.status_label.config(text="Processing...", foreground="blue")
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.process_images, daemon=True)
        thread.start()
        
    def process_images(self):
        """Process all images (runs in separate thread)"""
        total_images = len(self.image_paths)
        start_time = time.time()
        
        for index, img_path in enumerate(self.image_paths, 1):
            try:
                # Open image
                img = Image.open(img_path)
                
                # Invert colors
                if img.mode == 'RGBA':
                    # Handle transparency separately
                    r, g, b, a = img.split()
                    rgb_image = Image.merge('RGB', (r, g, b))
                    inverted_rgb = ImageOps.invert(rgb_image)
                    r_inv, g_inv, b_inv = inverted_rgb.split()
                    inverted_img = Image.merge('RGBA', (r_inv, g_inv, b_inv, a))
                elif img.mode == 'RGB':
                    inverted_img = ImageOps.invert(img)
                else:
                    # Convert to RGB first, then invert
                    rgb_img = img.convert('RGB')
                    inverted_img = ImageOps.invert(rgb_img)
                
                # Get original filename and extension
                original_path = Path(img_path)
                output_filename = f"{original_path.stem}_inverted{original_path.suffix}"
                output_path = Path(self.output_dir) / output_filename
                
                # Save with original format
                inverted_img.save(output_path)
                
                # Update progress
                progress = (index / total_images) * 100
                self.root.after(0, self.update_progress, progress, index, total_images, start_time)
                
            except Exception as e:
                error_msg = f"Error processing {Path(img_path).name}: {str(e)}"
                self.root.after(0, self.show_error, error_msg)
        
        # Processing complete
        self.root.after(0, self.processing_complete)
        
    def update_progress(self, progress, current, total, start_time):
        """Update progress bar and ETA (called from main thread)"""
        self.progress_bar['value'] = progress
        
        # Calculate ETA
        elapsed = time.time() - start_time
        if current > 0:
            avg_time_per_image = elapsed / current
            remaining_images = total - current
            eta_seconds = avg_time_per_image * remaining_images
            
            if eta_seconds > 60:
                eta_text = f"ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
            else:
                eta_text = f"ETA: {int(eta_seconds)}s"
                
            self.eta_label.config(text=eta_text)
        
        self.status_label.config(text=f"Processing image {current} of {total}...")
        
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Processing Error", message)
        
    def processing_complete(self):
        """Called when all processing is complete"""
        self.is_processing = False
        self.progress_bar['value'] = 100
        self.eta_label.config(text="Complete!")
        self.status_label.config(text="All images processed successfully", foreground="green")
        
        # Re-enable buttons
        self.select_images_btn.config(state='normal')
        self.select_output_btn.config(state='normal')
        self.reset_btn.config(state='normal')
        self.update_export_button()
        
        # Show completion dialog
        self.show_completion_dialog()
        
    def show_completion_dialog(self):
        """Show completion popup with option to open output folder"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Complete")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        
        # Center the dialog on screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Make modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Message
        message_frame = ttk.Frame(dialog, padding="20")
        message_frame.pack(expand=True, fill=tk.BOTH)
        
        ttk.Label(
            message_frame, 
            text="✓ Export Complete!", 
            font=('Arial', 14),
            foreground="green"
        ).pack(pady=(0, 10))
        
        ttk.Label(
            message_frame, 
            text=f"Successfully processed {len(self.image_paths)} image(s)",
            font=('Arial', 10)
        ).pack(pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(message_frame)
        button_frame.pack()
        
        ttk.Button(
            button_frame, 
            text="Open Output Folder", 
            command=lambda: self.open_output_folder(dialog)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Close", 
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
    def open_output_folder(self, dialog):
        """Open the output folder in file explorer"""
        try:
            if sys.platform == 'win32':
                os.startfile(self.output_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', self.output_dir])
            else:  # Linux and other Unix-like
                subprocess.run(['xdg-open', self.output_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")
        finally:
            dialog.destroy()


def main():
    root = tk.Tk()
    app = ImageInverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()