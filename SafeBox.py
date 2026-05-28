import os
import json
import time
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from colorama import Fore, Style, init

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
init(autoreset=True)
LOG_FILE = "vault_audit.log"
METADATA_FILE = "vault_registry.json"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EncryptionEngine:
    """Core Cryptographic Operations using AES-256 CBC Mode"""
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=200000, # Industrial standard
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    @staticmethod
    def encrypt_data(data: bytes, password: str):
        salt = os.urandom(16)
        iv = os.urandom(16)
        key = EncryptionEngine.derive_key(password, salt)
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return salt + iv + ciphertext

    @staticmethod
    def decrypt_data(raw_data: bytes, password: str):
        salt = raw_data[:16]
        iv = raw_data[16:32]
        ciphertext = raw_data[32:]
        
        key = EncryptionEngine.derive_key(password, salt)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        try:
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            return data
        except Exception:
            return None

class SecureVaultApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SENTINEL VAULT - Advanced Encryption Suite v4.0")
        self.root.geometry("700x550")
        self.root.configure(bg="#1e1e1e")
        self.setup_styles()
        self.create_widgets()
        self.registry = self.load_registry()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="#00ffcc", font=("Consolas", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.map("TButton", background=[('active', '#00ffcc')], foreground=[('active', '#1e1e1e')])

    def create_widgets(self):
        # Header
        header = tk.Label(self.root, text="AES-256 CRYPTO ENGINE", font=("Impact", 24), fg="#00ffcc", bg="#1e1e1e")
        header.pack(pady=20)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=30, pady=10, fill="both", expand=True)

        # File Selection
        self.file_label = ttk.Label(main_frame, text="No file selected...")
        self.file_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        btn_select = ttk.Button(main_frame, text="SELECT TARGET FILE", command=self.select_file)
        btn_select.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Password
        ttk.Label(main_frame, text="MASTER ACCESS KEY:").grid(row=2, column=0, pady=20, sticky="w")
        self.password_entry = tk.Entry(main_frame, show="*", font=("Consolas", 12), bg="#2d2d2d", fg="white", insertbackground="white")
        self.password_entry.grid(row=2, column=1, pady=20, sticky="ew")

        # Progress
        self.progress = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=2, pady=10)

        # Actions
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=30)

        self.enc_btn = ttk.Button(btn_frame, text="ENCRYPT FILE", command=lambda: self.process_thread("ENC"))
        self.enc_btn.pack(side="left", padx=10)

        self.dec_btn = ttk.Button(btn_frame, text="DECRYPT FILE", command=lambda: self.process_thread("DEC"))
        self.dec_btn.pack(side="left", padx=10)

        # Status Bar
        self.status = tk.Label(self.root, text="System Ready", bd=1, relief="sunken", anchor="w", bg="#333", fg="white")
        self.status.pack(side="bottom", fill="x")

    def load_registry(self):
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r') as f: return json.load(f)
        return {}

    def save_registry(self, entry):
        self.registry.update(entry)
        with open(METADATA_FILE, 'w') as f: json.dump(self.registry, f, indent=4)

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path = file_path
            self.file_label.config(text=f"Target: {os.path.basename(file_path)}")

    def process_thread(self, mode):
        t = threading.Thread(target=self.run_operation, args=(mode,))
        t.start()

    def run_operation(self, mode):
        password = self.password_entry.get()
        if not password or not hasattr(self, 'file_path'):
            messagebox.showerror("Error", "Please select a file and enter a password!")
            return

        self.status.config(text="Processing... Please wait.")
        self.progress['value'] = 20
        self.root.update_idletasks()

        try:
            with open(self.file_path, 'rb') as f: data = f.read()
            self.progress['value'] = 50
            
            if mode == "ENC":
                result = EncryptionEngine.encrypt_data(data, password)
                output_path = self.file_path + ".vault"
                tag = "ENCRYPTED"
            else:
                result = EncryptionEngine.decrypt_data(data, password)
                output_path = self.file_path.replace(".vault", "_unlocked.txt")
                tag = "DECRYPTED"

            if result is None: raise ValueError("Invalid Password or Corrupt Data!")

            with open(output_path, 'wb') as f: f.write(result)
            
            self.progress['value'] = 100
            self.status.config(text=f"Operation {tag} Successful!")
            
            self.save_registry({
                str(datetime.now()): {
                    "file": os.path.basename(output_path),
                    "action": tag,
                    "status": "Success"
                }
            })
            logging.info(f"{tag} operation on {self.file_path} completed.")
            messagebox.showinfo("Sentinel Vault", f"File successfully {tag}!")
            
        except Exception as e:
            messagebox.showerror("Security Error", str(e))
            logging.error(f"Error during {mode}: {str(e)}")
        finally:
            self.progress['value'] = 0
            self.password_entry.delete(0, 'end')

if __name__ == "__main__":
    root = tk.Tk()
    app = SecureVaultApp(root)
    root.mainloop()