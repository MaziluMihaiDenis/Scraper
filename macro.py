import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import ctypes
import json
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Input Recorder (Combo Support)")
        self.root.geometry("650x750")

        self.actions = []  
        self.recording = False
        self.playing = False
        self.stop_requested = False
        self.start_time = 0
        
        # Track currently pressed modifiers during recording
        self.current_modifiers = set()
        
        self.mouse_ctrl = MouseController()
        self.kb_ctrl = KeyboardController()

        self.setup_ui()

    def setup_ui(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open (.txt)", command=self.load_file)
        filemenu.add_command(label="Save (.txt)", command=self.save_file)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.config(menu=menubar)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.rec_btn = tk.Button(btn_frame, text="Record / Append (F9)", command=self.toggle_record, bg="#2ecc71", fg="white", width=20)
        self.rec_btn.grid(row=0, column=0, padx=5)

        self.play_btn = tk.Button(btn_frame, text="Play Sequence", command=self.play_actions, bg="#3498db", fg="white", width=15)
        self.play_btn.grid(row=0, column=1, padx=5)

        loop_frame = tk.Frame(self.root)
        loop_frame.pack(pady=5)
        tk.Label(loop_frame, text="Repeat Count:").grid(row=0, column=0)
        self.loop_entry = tk.Entry(loop_frame, width=5)
        self.loop_entry.insert(0, "1")
        self.loop_entry.grid(row=0, column=1, padx=5)

        self.tree = ttk.Treeview(self.root, columns=("Type", "Details", "Delay"), show='headings', height=12)
        self.tree.heading("Type", text="Type")
        self.tree.heading("Details", text="Details")
        self.tree.heading("Delay", text="Delay (s)")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        edit_frame = tk.LabelFrame(self.root, text="Modify Actions", padx=10, pady=10)
        edit_frame.pack(fill=tk.X, padx=10, pady=10)
        self.edit_detail = tk.Entry(edit_frame)
        self.edit_detail.grid(row=0, column=0, padx=5)
        self.edit_delay = tk.Entry(edit_frame, width=8)
        self.edit_delay.grid(row=0, column=1, padx=5)
        tk.Button(edit_frame, text="Update", command=self.update_action).grid(row=0, column=2, padx=5)
        tk.Button(edit_frame, text="Delete", command=self.delete_item, bg="#e74c3c", fg="white").grid(row=0, column=3, padx=5)

        self.status_label = tk.Label(self.root, text="F9: Record | ESC: Stop Playback | Combo Support Active", fg="blue")
        self.status_label.pack(pady=5)

    def toggle_record(self):
        if not self.recording:
            if self.actions:
                choice = messagebox.askyesnocancel("Append?", "Keep existing actions?")
                if choice is None: return
                if choice is False:
                    self.actions = []
                    self.tree.delete(*self.tree.get_children())
            
            self.recording = True
            self.start_time = time.time() if not self.actions else time.time() - self.actions[-1]['delay']
            self.current_modifiers.clear()

            # Need suppress=False to allow keys to work while recording
            self.kb_listener = keyboard.Listener(on_press=self.on_press_record, on_release=self.on_release_record)
            self.mouse_listener = mouse.Listener(on_click=self.on_click)
            self.kb_listener.start()
            self.mouse_listener.start()
            self.rec_btn.config(text="STOP Recording (F9)", bg="#e67e22")
        else:
            self.stop_recording()

    def stop_recording(self):
        self.recording = False
        self.rec_btn.config(text="Record / Append (F9)", bg="#2ecc71")
        if hasattr(self, 'mouse_listener'): self.mouse_listener.stop()
        if hasattr(self, 'kb_listener'): self.kb_listener.stop()

    def on_click(self, x, y, button, pressed):
        if pressed and self.recording:
            delay = round(time.time() - self.start_time, 2)
            if(mouse.Button.left == button):
                self.add_action("Left Click", f"{x}, {y}", delay)
            elif(mouse.Button.right == button):
                self.add_action("Right Click", f"{x}, {y}", delay)

    def on_press_record(self, key):
        if key == keyboard.Key.f9:
            self.stop_recording()
            return False
        
        if self.recording:
            # Detect modifier keys (Ctrl, Alt, Shift)
            modifiers = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, 
                         keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
                         keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r}
            
            if key in modifiers:
                self.current_modifiers.add(key)
                return

            delay = round(time.time() - self.start_time, 2)
            k_name = key.char if hasattr(key, 'char') and key.char else str(key)
            
            # If modifiers are held, record as a Combo
            if self.current_modifiers:
                mod_names = [str(m) for m in self.current_modifiers]
                combo_str = "+".join(mod_names) + "+" + k_name
                self.add_action("Combo", combo_str, delay)
            else:
                self.add_action("Key", k_name, delay)

    def on_release_record(self, key):
        if key in self.current_modifiers:
            self.current_modifiers.remove(key)

    def add_action(self, a_type, details, delay):
        action = {'type': a_type, 'details': details, 'delay': delay}
        self.actions.append(action)
        self.root.after(0, lambda: self.tree.insert("", tk.END, values=(a_type, details, delay)))

    def play_actions(self):
        if not self.actions or self.playing: return
        try:
            loops = int(self.loop_entry.get())
        except: return

        self.playing = True
        self.stop_requested = False
        self.status_label.config(text="PLAYING... ESC to Stop", fg="red")

        def run_playback():
            def on_press_stop(key):
                if key == keyboard.Key.esc:
                    self.stop_requested = True
                    return False
            stop_listener = keyboard.Listener(on_press=on_press_stop)
            stop_listener.start()

            iteration = 0
            while not self.stop_requested:
                iteration += 1
                last_ts = 0
                for action in self.actions:
                    if self.stop_requested: break
                    time.sleep(max(0, action['delay'] - last_ts))
                    last_ts = action['delay']

                    details = action['details']
                    if action['type'] == "Left Click":
                        x, y = map(int, details.split(","))
                        self.mouse_ctrl.position = (x, y)
                        self.mouse_ctrl.click(Button.left, 1)
                    elif action['type'] == "Right Click":
                        x, y = map(int, details.split(","))
                        self.mouse_ctrl.position = (x, y)
                        self.mouse_ctrl.click(Button.right, 1)

                    elif action['type'] == "Key":
                        k = getattr(Key, details.split(".")[1]) if "Key." in details else details
                        self.kb_ctrl.press(k)
                        self.kb_ctrl.release(k)
                    
                    elif action['type'] == "Combo":
                        keys = details.split("+")
                        # 1. Press all modifiers
                        to_press = []
                        for k in keys:
                            real_key = getattr(Key, k.split(".")[1]) if "Key." in k else k
                            to_press.append(real_key)
                            self.kb_ctrl.press(real_key)
                        # 2. Release in reverse
                        for real_key in reversed(to_press):
                            self.kb_ctrl.release(real_key)
                
                if loops > 0 and iteration >= loops: break
            
            stop_listener.stop()
            self.playing = False
            self.status_label.config(text="Finished/Stopped", fg="blue")

        threading.Thread(target=run_playback, daemon=True).start()

    # (UI helper methods update_action, delete_item, load/save file remain same as previous version)
    def on_item_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        vals = self.tree.item(selected[0])['values']
        self.edit_detail.delete(0, tk.END); self.edit_detail.insert(0, vals[1])
        self.edit_delay.delete(0, tk.END); self.edit_delay.insert(0, vals[2])

    def update_action(self):
        selected = self.tree.selection()
        if not selected: return
        idx = self.tree.index(selected[0])
        self.actions[idx]['details'] = self.edit_detail.get()
        self.actions[idx]['delay'] = float(self.edit_delay.get())
        self.tree.item(selected[0], values=(self.actions[idx]['type'], self.actions[idx]['details'], self.actions[idx]['delay']))

    def delete_item(self):
        selected = self.tree.selection()
        if not selected: return
        idx = self.tree.index(selected[0])
        del self.actions[idx]; self.tree.delete(selected[0])

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if file_path:
            with open(file_path, 'w') as f: json.dump(self.actions, f)

    def load_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'r') as f: self.actions = json.load(f)
            self.tree.delete(*self.tree.get_children())
            for a in self.actions: self.tree.insert("", tk.END, values=(a['type'], a['details'], a['delay']))

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()