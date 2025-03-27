import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import os

# Change to your Git repository directory
os.chdir(r"C:\Users\91924\Desktop\project\PROJECTS ON GIT HUB\LazyGit")

def run_git_command(command):
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
root.geometry("400x300")

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

commit_entry = tk.Entry(root, width=50)
commit_entry.pack(pady=5)
commit_entry.insert(0, "Enter commit message...")

output_text = scrolledtext.ScrolledText(root, height=10, width=50)
output_text.pack(pady=5)

root.mainloop()
