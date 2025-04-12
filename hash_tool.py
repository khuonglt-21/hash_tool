import hashlib
import zlib
import os
import sys
import tkinter as tk
from tkinter import ttk
import threading
import time
import json
from functools import partial

# Supported algorithms (now includes crc32)
algorithms = ['md5', 'sha1', 'sha256', 'crc32', 'sha384', 'sha512']
BUFFER_SIZE = 4 * 1024 * 1024  # 4MB buffer for optimal performance

def get_config_path():
    """Get config file path in executable directory"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(exe_dir, "hash_tool_config.json")

def load_config():
    """Load configuration from file"""
    config_path = get_config_path()
    default_config = {
        'save_to_file': True,
        'window_width': 1000,
        'window_height': 500
    }
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_config

def save_config(config):
    """Save configuration to file"""
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def setup_copy_menu(widget):
    """Setup right-click copy menu for widget"""
    def copy_to_clipboard():
        try:
            if isinstance(widget, tk.Text):
                text = widget.get("sel.first", "sel.last") if widget.tag_ranges("sel") else widget.get("1.0", "end-1c")
            else:
                text = widget.cget("text")
            
            widget.clipboard_clear()
            widget.clipboard_append(text.strip())
        except Exception as e:
            print(f"Copy failed: {e}")

    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Copy", command=copy_to_clipboard)
    
    def show_context_menu(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    widget.bind("<Button-3>", show_context_menu)
    
    if isinstance(widget, tk.Text):
        widget.bind("<Control-c>", lambda e: copy_to_clipboard())
    
    return widget

def compute_hash(path, algo, on_complete_callback):
    """Compute hash with maximum speed (now includes CRC32)"""
    start_time = time.perf_counter()
    
    if algo == 'crc32':
        crc_value = 0
        with open(path, 'rb', buffering=BUFFER_SIZE) as f:
            for chunk in iter(partial(f.read, BUFFER_SIZE), b''):
                crc_value = zlib.crc32(chunk, crc_value)
        hash_value = f"{crc_value & 0xFFFFFFFF:08x}"  # Format as 8-digit hex
    else:
        hash_obj = hashlib.new(algo)
        with open(path, 'rb', buffering=BUFFER_SIZE) as f:
            for chunk in iter(partial(f.read, BUFFER_SIZE), b''):
                hash_obj.update(chunk)
        hash_value = hash_obj.hexdigest()
    
    elapsed = time.perf_counter() - start_time
    on_complete_callback(hash_value, elapsed)

def save_hashes_to_file(file_path, filename, results):
    """Save hash results to file with UTF-8 encoding"""
    try:
        hash_file_path = os.path.join(os.path.dirname(file_path), f"{filename}.hash.txt")
        
        content = [
            filename,
            "=" * 40,
            f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 40,
            ""
        ]
        
        for algo in algorithms:
            if algo in results:
                hash_value = results[algo][0]
                content.append(f"{algo.upper()} : {hash_value}")
        
        content.append("")
        
        with open(hash_file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))
            
    except Exception as e:
        print(f"Error saving hash file: {str(e)}")
        raise

def select_algorithm(file_path):
    """Create hash calculator GUI"""
    config = load_config()
    results = {}
    filename = os.path.basename(file_path)
    file_dir = os.path.dirname(file_path)

    # Main Window
    window = tk.Tk()
    window.title("Hash Calculator")
    window.geometry(f"{config['window_width']}x{config['window_height']}")

    # === Configuration Frame ===
    config_frame = tk.Frame(window, padx=10, pady=5)
    config_frame.pack(fill=tk.X)

    save_var = tk.BooleanVar(value=config['save_to_file'])
    
    def toggle_save():
        new_state = save_var.get()
        save_config({
            'save_to_file': new_state,
            'window_width': window.winfo_width(),
            'window_height': window.winfo_height()
        })
        for algo in algorithms:
            buttons[algo].config(state="normal")
    
    save_cb = tk.Checkbutton(
        config_frame, 
        text="Save hash to file", 
        variable=save_var,
        command=toggle_save
    )
    save_cb.pack(side=tk.LEFT)
    setup_copy_menu(save_cb)

    # === PowerShell Commands ===
    ps_frame = tk.Frame(window, padx=10, pady=5)
    ps_frame.pack(fill=tk.X)

    full_path = os.path.join(file_dir, filename).replace('\\', '\\\\')
    ps_text = tk.Text(ps_frame, height=6, wrap=tk.NONE)
    ps_text.insert(tk.END, "# PowerShell verification commands:\n")
    for algo in algorithms:
        if algo != 'crc32':  # Skip CRC32 as PowerShell doesn't have native support
            ps_text.insert(tk.END, f"Get-FileHash -Algorithm {algo.upper()} \"{full_path}\"\n")
    ps_text.config(state="disabled")
    ps_text.pack(fill=tk.X)
    setup_copy_menu(ps_text)

    # === Buttons Frame ===
    button_frame = tk.Frame(window, padx=10, pady=5)
    button_frame.pack()

    buttons = {}
    for i, algo in enumerate(algorithms):
        btn = tk.Button(
            button_frame, 
            text=algo.upper(), 
            width=12, 
            height=2,
            command=lambda a=algo: on_select(a)
        )
        btn.grid(row=0, column=i, padx=5)
        buttons[algo] = btn

    # === Results Table ===
    table_frame = tk.Frame(window)
    table_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(table_frame)
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Table headers
    headers = ["Algorithm", "Hash Value", "Time (s)"]
    for col, text in enumerate(headers):
        width = 12 if col == 0 else (130 if col == 1 else 10)
        lbl = tk.Label(
            scrollable_frame, 
            text=text, 
            width=width, 
            anchor='w', 
            font='TkDefaultFont 9 bold'
        )
        lbl.grid(row=0, column=col, padx=5, pady=2, sticky='w')
        setup_copy_menu(lbl)

    # Status Bar
    status_var = tk.StringVar()
    status_bar = tk.Label(
        window, 
        textvariable=status_var, 
        anchor='w',
        relief=tk.SUNKEN, 
        padx=5, 
        pady=2,
        foreground='white', 
        background='#0078D7',
        font='TkDefaultFont 9'
    )
    status_bar.pack(fill=tk.X, pady=(5, 0))
    setup_copy_menu(status_bar)

    # Store result widgets
    result_widgets = {}

    def on_select(algo):
        """Handle algorithm selection"""
        buttons[algo].config(state="disabled")
        status_var.set(f"🔍 Calculating {algo.upper()}...")

        def on_complete(hash_value, elapsed_time):
            """Callback when computation completes"""
            results[algo] = (hash_value, elapsed_time)
            
            row = len(results)
            if algo not in result_widgets:
                # Create entry frame for each result
                entry_frame = tk.Frame(scrollable_frame)
                entry_frame.grid(row=row, column=0, columnspan=3, sticky='ew', padx=5, pady=2)
                
                # Algorithm label
                algo_label = tk.Label(
                    entry_frame,
                    text=algo.upper(),
                    width=12,
                    anchor='w'
                )
                algo_label.pack(side=tk.LEFT)
                
                # Hash value label - now using Text widget for selectable text
                hash_text = tk.Text(
                    entry_frame,
                    width=130,
                    height=1,
                    wrap=tk.NONE,
                    font='TkFixedFont'
                )
                hash_text.insert('1.0', hash_value)
                hash_text.config(state='disabled')
                hash_text.pack(side=tk.LEFT)
                
                # Time label
                time_label = tk.Label(
                    entry_frame,
                    text=f"{elapsed_time:.3f}",
                    width=10,
                    anchor='w'
                )
                time_label.pack(side=tk.LEFT)
                
                result_widgets[algo] = {
                    'frame': entry_frame,
                    'algo_label': algo_label,
                    'hash_text': hash_text,
                    'time_label': time_label
                }
                
                setup_copy_menu(hash_text)
                setup_copy_menu(algo_label)
                setup_copy_menu(time_label)
            else:
                result_widgets[algo]['hash_text'].config(state='normal')
                result_widgets[algo]['hash_text'].delete('1.0', 'end')
                result_widgets[algo]['hash_text'].insert('1.0', hash_value)
                result_widgets[algo]['hash_text'].config(state='disabled')
                result_widgets[algo]['time_label'].config(text=f"{elapsed_time:.3f}")
            
            if save_var.get():
                try:
                    save_hashes_to_file(file_path, filename, results)
                    status_var.set(f"✅ {algo.upper()} completed in {elapsed_time:.3f}s | Saved to {filename}.hash.txt")
                except Exception as e:
                    status_var.set(f"⚠️ Failed to save: {str(e)}")
            else:
                status_var.set(f"✅ {algo.upper()} completed in {elapsed_time:.3f}s")

        threading.Thread(
            target=compute_hash,
            args=(file_path, algo, on_complete),
            daemon=True
        ).start()

    def on_closing():
        """Handle window closing"""
        save_config({
            'save_to_file': save_var.get(),
            'window_width': window.winfo_width(),
            'window_height': window.winfo_height()
        })
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_closing)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def handle_ctrl_c(event):
        widget = event.widget
        try:
            if isinstance(widget, tk.Text):
                if widget.tag_ranges("sel"):
                    text = widget.get("sel.first", "sel.last")
                    widget.clipboard_clear()
                    widget.clipboard_append(text.strip())
        except:
            pass
        return "break"
    
    window.bind("<Control-c>", handle_ctrl_c, add=True)

    window.mainloop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hash_tool.exe <file_path>")
        sys.exit(1)
    select_algorithm(sys.argv[1])