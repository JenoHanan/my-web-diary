import streamlit as st
import os
import json
import hashlib
from datetime import datetime

PASSWORD_FILE = "password.json"
DIARY_DIR = "diary_entries"
HASH_ITERATIONS = 150_000

# --- Core Logic Functions (Kept exactly as you wrote them!) ---

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
    return sorted(os.listdir(DIARY_DIR), reverse=True)

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

# --- Streamlit Web UI ---

def main():
    st.set_page_config(page_title="Personal Diary", page_icon="📓")
    
    # Initialize session state for login tracking
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    stored_hash = load_password_hash()

    # 1. Initial Password Setup
    if stored_hash is None:
        st.title("Welcome to your New Diary 📓")
        st.info("It looks like this is your first time. Let's set up a password.")
        new_password = st.text_input("Set a password:", type="password")
        confirm_password = st.text_input("Confirm password:", type="password")
        
        if st.button("Set Password"):
            if not new_password:
                st.error("Password cannot be empty.")
            elif new_password != confirm_password:
                st.error("Passwords do not match!")
            else:
                save_password_hash(hash_password(new_password))
                st.success("Password set successfully! Reloading...")
                st.rerun()
        return 

    # 2. Login Screen
    if not st.session_state.authenticated:
        st.title("Personal Diary 🔒")
        password = st.text_input("Enter Password:", type="password")
        
        if st.button("Login"):
            if verify_password(password, stored_hash):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        return 

    # 3. Main Application (Authenticated)
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio("Choose an action:", ["Write Entry", "View Entries", "Delete Entry"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    if menu == "Write Entry":
        st.title("Write New Entry 📝")
        title = st.text_input("Title (optional):")
        content = st.text_area("Dear Diary...", height=300)
        
        if st.button("Save Entry"):
            if not content.strip():
                st.error("Diary entry is empty.")
            else:
                filename = save_entry(content, title)
                st.success(f"Saved successfully as '{os.path.basename(filename)}'")

    elif menu == "View Entries":
        st.title("Your Entries 📖")
        entries = list_entries()
        
        if not entries:
            st.info("No entries found. Go write something!")
        else:
            selected_entry = st.selectbox("Select an entry to read:", entries)
            if selected_entry:
                content = read_entry(selected_entry)
                st.text_area("Contents:", content, height=400, disabled=True)

    elif menu == "Delete Entry":
        st.title("Delete Entry 🗑️")
        entries = list_entries()
        
        if not entries:
            st.info("No entries to delete.")
        else:
            selected_entry = st.selectbox("Select an entry to delete:", entries)
            if st.button("Delete Selected Entry"):
                if delete_entry(selected_entry):
                    st.success(f"Entry '{selected_entry}' deleted.")
                    st.rerun()
                else:
                    st.error("Failed to delete entry.")

if __name__ == "__main__":
    main()
