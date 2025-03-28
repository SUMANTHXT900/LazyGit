import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import subprocess
import os

# Global variable to store the selected directory
repo_directory = ""

def select_directory():
    global repo_directory
    selected_directory = filedialog.askdirectory(title="Select Git Repository Directory")
    if selected_directory:
        repo_directory = selected_directory
        os.chdir(repo_directory)
        directory_label.config(text=f"Selected Directory: {repo_directory}")
        output_text.insert(tk.END, f"Changed working directory to: {repo_directory}\n")
        output_text.see(tk.END)

def run_git_command(command):
    if not repo_directory:
        messagebox.showwarning("Directory Not Selected", "Please select a Git repository directory first.")
        return
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        output_text.insert(tk.END, result.stdout if result.stdout else result.stderr + "\n")
        output_text.see(tk.END)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def git_add():
    run_git_command("git add .")

def git_commit():
    commit_message = commit_entry.get()
    if commit_message:
        run_git_command(f"git commit -m \"{commit_message}\"")
    else:
        messagebox.showwarning("Commit Message", "Please enter a commit message.")

def git_push():
    run_git_command("git push origin main")

def git_pull():
    run_git_command("git pull origin main")

# GUI Setup
root = tk.Tk()
root.title("Simple Git GUI")
root.geometry("500x400")

# Directory Selection
directory_frame = tk.Frame(root)
directory_frame.pack(pady=5)

select_dir_button = tk.Button(directory_frame, text="Select Directory", command=select_directory, width=15)
select_dir_button.grid(row=0, column=0, padx=5)

directory_label = tk.Label(directory_frame, text="No directory selected", width=50, anchor="w")
directory_label.grid(row=0, column=1, padx=5)

# Git Command Buttons
frame = tk.Frame(root)
frame.pack(pady=5)

git_add_button = tk.Button(frame, text="Add", command=git_add, width=10)
git_add_button.grid(row=0, column=0, padx=5)

git_commit_button = tk.Button(frame, text="Commit", command=git_commit, width=10)
git_commit_button.grid(row=0, column=1, padx=5)

git_push_button = tk.Button(frame, text="Push", command=git_push, width=10)
git_push_button.grid(row=0, column=2, padx=5)

git_pull_button = tk.Button(frame, text="Pull", command=git_pull, width=10)
git_pull_button.grid(row=0, column=3, padx=5)

# Commit Message Entry
commit_entry = tk.Entry(root, width=50)
commit_entry.pack(pady=5)
commit_entry.insert(0, "Enter commit message...")

# Output Text Area
output_text = scrolledtext.ScrolledText(root, height=15, width=60)
output_text.pack(pady=5)

root.mainloop()

#yea the pull is working and the push is working too.
