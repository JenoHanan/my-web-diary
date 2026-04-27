import tkinter as tk

from tkinter import ttk, messagebox, scrolledtext, simpledialog

import os

import json

import hashlib

from datetime import datetime



PASSWORD_FILE = "password.json"

DIARY_DIR = "diary_entries"

HASH_ITERATIONS = 150_000



def hash_password(password, salt=None):

    if salt is None:

        salt = os.urandom(16)

    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, HASH_ITERATIONS)

    return {'salt': salt.hex(), 'hash': key.hex(), 'iterations': HASH_ITERATIONS}



def save_password_hash(password_hash):

    with open(PASSWORD_FILE, 'w') as f:

        json.dump(password_hash, f)



def load_password_hash():

    if not os.path.exists(PASSWORD_FILE):

        return None

    with open(PASSWORD_FILE, 'r') as f:

        return json.load(f)



def verify_password(password, stored):

    salt = bytes.fromhex(stored['salt'])

    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, stored['iterations'])

    return key.hex() == stored['hash']



def get_entry_filename(title=None):

    now = datetime.now()

    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    safe_title = "".join(c for c in (title or "") if c.isalnum() or c in (' ', '_')).rstrip()

    if safe_title:

        filename = f"{safe_title}_{timestamp}.txt"

    else:

        filename = f"{timestamp}.txt"

    return os.path.join(DIARY_DIR, filename)



def save_entry(content, title=None):

    if not os.path.exists(DIARY_DIR):

        os.makedirs(DIARY_DIR)

    filename = get_entry_filename(title)

    with open(filename, "w", encoding="utf-8") as f:

        f.write(content)

    return filename



def list_entries():

    if not os.path.exists(DIARY_DIR):

        return []

    return sorted(os.listdir(DIARY_DIR))



def read_entry(filename):

    path = os.path.join(DIARY_DIR, filename)

    with open(path, "r", encoding="utf-8") as f:

        return f.read()



def delete_entry(filename):

    path = os.path.join(DIARY_DIR, filename)

    if os.path.exists(path):

        os.remove(path)

        return True

    return False



class LoginWindow(tk.Toplevel):

    def __init__(self, master, verify_password_callback):

        super().__init__(master)

        self.title("Login")

        self.geometry("300x120")

        self.resizable(False, False)

        self.verify_password_callback = verify_password_callback

        self.authenticated = False

        

        ttk.Label(self, text="Enter Password:").pack(pady=10)

        self.password_entry = ttk.Entry(self, show="*")

        self.password_entry.pack(pady=5)

        self.password_entry.focus_set()

        self.password_entry.bind('<Return>', lambda e: self.check_password())

        ttk.Button(self, text="Login", command=self.check_password).pack(pady=10)

        

        # Prevent closing without authentication

        self.protocol("WM_DELETE_WINDOW", self.on_closing)



    def check_password(self):

        password = self.password_entry.get()

        if self.verify_password_callback(password):

            self.authenticated = True

            self.destroy()

        else:

            messagebox.showerror("Login Failed", "Incorrect password. Please try again.")

            self.password_entry.delete(0, tk.END)

    

    def on_closing(self):

        if messagebox.askokcancel("Quit", "Do you want to quit without logging in?"):

            self.authenticated = False

            self.destroy()



class DiaryApp(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title("Personal Diary")

        self.geometry("500x400")

        self.resizable(False, False)

        self.configure(bg="#f8f1f1")

        self.create_widgets()



    def create_widgets(self):

        title_label = ttk.Label(self, text="My Personal Diary", font=("Georgia", 20, "bold"))

        title_label.pack(pady=10)

        write_btn = ttk.Button(self, text="Write Entry", command=self.open_write_window)

        write_btn.pack(fill='x', padx=40, pady=5)

        view_btn = ttk.Button(self, text="View Entries", command=self.open_view_window)

        view_btn.pack(fill='x', padx=40, pady=5)

        delete_btn = ttk.Button(self, text="Delete Entry", command=self.open_delete_window)

        delete_btn.pack(fill='x', padx=40, pady=5)



    def open_write_window(self):

        WriteEntryWindow(self, self.on_entry_saved)



    def on_entry_saved(self, filename):

        messagebox.showinfo("Saved", f"Diary saved as '{os.path.basename(filename)}'")



    def open_view_window(self):

        ViewEntriesWindow(self)



    def open_delete_window(self):

        DeleteEntryWindow(self)



class WriteEntryWindow(tk.Toplevel):

    def __init__(self, master, save_callback):

        super().__init__(master)

        self.title("Write New Entry")

        self.geometry("500x400")

        ttk.Label(self, text="Title (optional):").pack(pady=5)

        self.title_entry = ttk.Entry(self)

        self.title_entry.pack(fill='x', padx=10)

        ttk.Label(self, text="Content:").pack(pady=5)

        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Calibri", 13))

        self.text_area.pack(fill='both', expand=True, padx=10, pady=5)

        ttk.Button(self, text="Save Entry", command=self.save_entry).pack(pady=10)

        self.save_callback = save_callback



    def save_entry(self):

        title = self.title_entry.get().strip()

        content = self.text_area.get("1.0", tk.END).strip()

        if not content:

            messagebox.showerror("Empty Entry", "Diary entry is empty.")

            return

        filename = save_entry(content, title)

        self.save_callback(filename)

        self.destroy()



class ViewEntriesWindow(tk.Toplevel):

    def __init__(self, master):

        super().__init__(master)

        self.title("View Entries")

        self.geometry("500x400")

        self.entries = list_entries()

        

        if not self.entries:

            ttk.Label(self, text="No entries found.", font=("Calibri", 13)).pack(pady=20)

            return

        

        self.listbox = tk.Listbox(self)

        self.listbox.pack(side='left', fill='y', padx=10, pady=10)

        for entry in self.entries:

            self.listbox.insert(tk.END, entry)

        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Calibri", 13), state='disabled')

        self.text_area.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        self.listbox.bind('<<ListboxSelect>>', self.display_entry)



    def display_entry(self, event):

        selection = self.listbox.curselection()

        if selection:

            filename = self.entries[selection[0]]

            content = read_entry(filename)

            self.text_area.config(state='normal')

            self.text_area.delete("1.0", tk.END)

            self.text_area.insert(tk.END, content)

            self.text_area.config(state='disabled')



class DeleteEntryWindow(tk.Toplevel):

    def __init__(self, master):

        super().__init__(master)

        self.title("Delete Entry")

        self.geometry("400x300")

        self.entries = list_entries()

        

        if not self.entries:

            ttk.Label(self, text="No entries to delete.", font=("Calibri", 13)).pack(pady=20)

            return

        

        self.listbox = tk.Listbox(self)

        self.listbox.pack(fill='both', expand=True, padx=10, pady=10)

        for entry in self.entries:

            self.listbox.insert(tk.END, entry)

        ttk.Button(self, text="Delete Selected Entry", command=self.delete_selected).pack(pady=10)



    def delete_selected(self):

        selection = self.listbox.curselection()

        if not selection:

            messagebox.showwarning("No Selection", "Please select an entry to delete.")

            return

        

        filename = self.entries[selection[0]]

        confirm = messagebox.askyesno("Confirm Delete", f"Delete '{filename}'?")

        if confirm:

            if delete_entry(filename):

                messagebox.showinfo("Deleted", f"Entry '{filename}' deleted.")

                self.listbox.delete(selection[0])

                self.entries.pop(selection[0])

            else:

                messagebox.showerror("Error", "Failed to delete entry.")



def main():

    # Initial password setup

    stored_hash = load_password_hash()

    if stored_hash is None:

        # Prompt for new password

        root = tk.Tk()

        root.withdraw()

        password = simpledialog.askstring("Set Password", "Set a password for your diary:", show="*")

        if not password:

            messagebox.showerror("Error", "Password cannot be empty.")

            root.destroy()

            return

        save_password_hash(hash_password(password))

        messagebox.showinfo("Success", "Password set successfully!")

        root.destroy()

        stored_hash = load_password_hash()

    

    # Create main app (hidden initially)

    app = DiaryApp()

    app.withdraw()

    

    # Show login window

    login = LoginWindow(app, lambda pw: verify_password(pw, stored_hash))

    app.wait_window(login)

    

    # Check if authentication was successful

    if login.authenticated:

        app.deiconify()

        app.mainloop()

    else:

        app.destroy()



if __name__ == "__main__":

    main()
