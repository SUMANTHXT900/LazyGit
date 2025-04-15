import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from PIL import Image, ImageTk, ImageFilter, ImageEnhance
import threading
import time

# Global variables
repo_directory = ""
theme_mode = "darkly"  # Default theme mode (using valid ttkbootstrap theme)
loading = False

class GlassmorphicFrame(ttk.Frame):
    """Custom frame with glassmorphism effect"""
    def __init__(self, master=None, **kwargs):
        self.blur_radius = kwargs.pop('blur_radius', 10)
        self.transparency = kwargs.pop('transparency', 0.7)
        self.bg_color = kwargs.pop('bg_color', '#ffffff')
        ttk.Frame.__init__(self, master, **kwargs)
        
        # Create a background canvas for the blur effect
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bind events to update the background
        self.bind("<Configure>", self._update_background)
    
    def _update_background(self, event=None):
        """Update the background with blur effect"""
        if hasattr(self, '_bg_id'):
            self.canvas.delete(self._bg_id)
        
        # Get the position of the frame relative to the root window
        x = self.winfo_rootx() - self.master.winfo_rootx()
        y = self.winfo_rooty() - self.master.winfo_rooty()
        
        # Take a screenshot of what's behind the frame
        try:
            # Create a background image based on theme
            width, height = self.winfo_width(), self.winfo_height()
            if width <= 1 or height <= 1:
                return
                
            if theme_mode == "darkly":
                bg_color = '#1a1a1a'
                alpha = int(180 * self.transparency)
            else:
                bg_color = '#f0f0f0'
                alpha = int(220 * self.transparency)
                
            # Create a background image
            bg_image = Image.new('RGBA', (width, height), bg_color + hex(alpha)[2:].zfill(2))
            
            # Apply blur effect
            blurred = bg_image.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))
            
            # Convert to PhotoImage
            self.bg_image = ImageTk.PhotoImage(blurred)
            
            # Draw the image on the canvas
            self._bg_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor='nw')
            
            # Raise all child widgets above the background
            for child in self.winfo_children():
                if child != self.canvas:
                    child.lift()
        except Exception as e:
            print(f"Error updating background: {e}")

class HoverButton(ttk.Button):
    """Button with hover effects"""
    def __init__(self, master=None, **kwargs):
        self.hover_color = kwargs.pop('hover_color', None)
        self.normal_style = kwargs.get('style', '')
        ttk.Button.__init__(self, master, **kwargs)
        
        # Bind hover events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Bind click events for animation
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
        
    def _on_enter(self, event):
        """Mouse enter event"""
        # Change background color on hover
        if self.hover_color:
            self.configure(bootstyle=f"{self.cget('bootstyle')}:hover")
        
    def _on_leave(self, event):
        """Mouse leave event"""
        # Restore original style
        if self.hover_color:
            self.configure(bootstyle=self.cget('bootstyle').replace(':hover', ''))
    
    def _on_click(self, event):
        """Mouse click event"""
        # Visual feedback for click
        self.state(['pressed'])
    
    def _on_release(self, event):
        """Mouse release event"""
        # Restore state after click
        self.state(['!pressed'])

class GitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Lazy Git")
        self.root.geometry("900x600")
        self.root.minsize(800, 600)
        
        # Set theme
        self.style = ttk.Style(theme=theme_mode)
        
        # Enable window transparency
        self.root.attributes('-alpha', 0.95)
        
        # Configure app-wide styles
        self.configure_styles()
        
        # Create main layout
        self.create_layout()
        
        # Bind window resize event
        self.root.bind("<Configure>", self.on_window_resize)
        
        # Create loading animation
        self.create_loading_animation()
    
    def configure_styles(self):
        """Configure global styles for the application"""
        # Button styles
        self.style.configure('TButton', font=('Segoe UI', 10), padding=5)
        self.style.configure('TButton.Hover', background='#3a8ab1')
        
        # Primary button style
        self.style.configure('primary.TButton', font=('Segoe UI', 10, 'bold'))
        self.style.configure('primary.TButton.Hover', background='#2980b9')
        
        # Secondary button style
        self.style.configure('secondary.TButton', font=('Segoe UI', 10))
        self.style.configure('secondary.TButton.Hover', background='#95a5a6')
        
        # Title label style
        self.style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        
        # Sidebar style
        self.style.configure('Sidebar.TFrame', background='#2c3e50' if theme_mode == 'darkly' else '#ecf0f1')
        
        # Content frame style
        self.style.configure('Content.TFrame', background='#34495e' if theme_mode == 'darkly' else '#f5f5f5')
    
    def create_layout(self):
        """Create the main application layout"""
        # Main container (using grid for better layout control)
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Create a glassmorphic sidebar for git actions
        self.sidebar = GlassmorphicFrame(
            self.main_container,
            blur_radius=10,
            transparency=0.7,
            bootstyle=SECONDARY
        )
        self.sidebar.pack(side=LEFT, fill=Y, padx=5, pady=5)
        
        # Sidebar title
        self.sidebar_title = ttk.Label(
            self.sidebar.canvas,
            text="Git Actions",
            font=('Segoe UI', 14, 'bold'),
            bootstyle=f"inverse-{SECONDARY}"
        )
        self.sidebar_title.pack(pady=10, padx=10)
        
        # Add sidebar buttons with custom styling
        self.create_sidebar_buttons()
        
        # Create content area
        self.content = GlassmorphicFrame(
            self.main_container,
            blur_radius=5,
            transparency=0.6,
            bootstyle=PRIMARY
        )
        self.content.pack(side=RIGHT, fill=BOTH, expand=YES, padx=5, pady=5)
        
        # Create header with repository selection
        self.header = ttk.Frame(self.content.canvas, bootstyle=PRIMARY)
        self.header.pack(fill=X, padx=10, pady=10)
        
        # Repository selection
        self.select_dir_button = HoverButton(
            self.header,
            text="Select Repository",
            command=self.select_directory,
            style="primary.TButton",
            hover_color="#3498db"
        )
        self.select_dir_button.pack(side=LEFT, padx=5)
        
        # Theme toggle button
        self.theme_button = HoverButton(
            self.header,
            text="🌙" if theme_mode == "darkly" else "☀️",
            command=self.toggle_theme,
            style="secondary.TButton",
            width=3
        )
        self.theme_button.pack(side=RIGHT, padx=5)
        
        # Directory label
        self.directory_label = ttk.Label(
            self.header,
            text="No repository selected",
            font=('Segoe UI', 10),
            bootstyle=INVERSE + PRIMARY
        )
        self.directory_label.pack(side=LEFT, padx=10, fill=X, expand=YES)
        
        # Create main working area
        self.work_area = ttk.Frame(self.content.canvas)
        self.work_area.pack(fill=BOTH, expand=YES, padx=10, pady=5)
        
        # Commit message frame
        self.commit_frame = GlassmorphicFrame(
            self.work_area,
            blur_radius=3,
            transparency=0.5,
            bootstyle=SECONDARY
        )
        self.commit_frame.pack(fill=X, pady=5)
        
        # Commit message label
        self.commit_label = ttk.Label(
            self.commit_frame.canvas,
            text="Commit Message:",
            font=('Segoe UI', 10, 'bold'),
            bootstyle=INVERSE + SECONDARY
        )
        self.commit_label.pack(anchor=W, padx=10, pady=(10, 5))
        
        # Commit message entry
        self.commit_entry = ttk.Entry(self.commit_frame.canvas, font=('Segoe UI', 10))
        self.commit_entry.pack(fill=X, padx=10, pady=(0, 10), ipady=3)
        self.commit_entry.insert(0, "Enter commit message...")
        self.commit_entry.bind("<FocusIn>", self.clear_commit_placeholder)
        self.commit_entry.bind("<FocusOut>", self.restore_commit_placeholder)
        
        # Output area (log)
        self.output_frame = GlassmorphicFrame(
            self.work_area,
            blur_radius=3,
            transparency=0.5,
            bootstyle=PRIMARY
        )
        self.output_frame.pack(fill=BOTH, expand=YES, pady=5)
        
        # Output log label
        self.output_label = ttk.Label(
            self.output_frame.canvas,
            text="Git Output:",
            font=('Segoe UI', 10, 'bold'),
            bootstyle=INVERSE + PRIMARY
        )
        self.output_label.pack(anchor=W, padx=10, pady=(10, 5))
        
        # Output text area
        self.output_text = ScrolledText(
            self.output_frame.canvas,
            padding=10,
            height=15,
            autohide=True,
            font=('Consolas', 10)
        )
        self.output_text.pack(fill=BOTH, expand=YES, padx=10, pady=(0, 10))
        
        # Status bar
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            bootstyle=INFO,
            anchor=E
        )
        self.status_bar.pack(fill=X, side=BOTTOM, padx=10, pady=5)
    
    def create_sidebar_buttons(self):
        """Create sidebar buttons for Git actions"""
        # Add Git action buttons to sidebar
        git_actions = [
            ("Add Changes", self.git_add, PRIMARY),
            ("Commit", self.git_commit, SUCCESS),
            ("Push", self.git_push, DANGER),
            ("Pull", self.git_pull, WARNING),
            ("Status", lambda: self.run_git_command("git status"), INFO),
            ("Log", lambda: self.run_git_command("git log --oneline -n 10"), SECONDARY)
        ]
        
        for text, command, style in git_actions:
            btn = HoverButton(
                self.sidebar.canvas,
                text=text,
                command=command,
                bootstyle=style,
                width=15
            )
            btn.pack(pady=5, padx=10, fill=X)
    
    def create_loading_animation(self):
        """Create a loading animation overlay"""
        self.loading_frame = ttk.Frame(self.root)
        
        # Loading label with dots animation
        self.loading_label = ttk.Label(
            self.loading_frame,
            text="Processing...",
            font=('Segoe UI', 14, 'bold'),
            bootstyle=INFO
        )
        self.loading_label.pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.loading_frame,
            mode='indeterminate',
            bootstyle=INFO,
            length=200
        )
        self.progress.pack(pady=10)
    
    def show_loading(self):
        """Show loading animation overlay"""
        global loading
        loading = True
        
        # Place loading frame over content
        self.loading_frame.place(
            relx=0.5, rely=0.5,
            anchor=CENTER,
            width=300, height=150
        )
        
        # Start progress animation
        self.progress.start()
        
        # Start dot animation in a separate thread
        threading.Thread(target=self.animate_dots, daemon=True).start()
    
    def hide_loading(self):
        """Hide loading animation"""
        global loading
        loading = False
        self.progress.stop()
        self.loading_frame.place_forget()
    
    def animate_dots(self):
        """Animate the loading dots"""
        dots = 0
        while loading:
            dots = (dots + 1) % 4
            self.loading_label.config(text=f"Processing{'.' * dots}")
            time.sleep(0.5)
    
    def on_window_resize(self, event=None):
        """Handle window resize events"""
        # Update glassmorphic effects on resize
        for widget in [self.sidebar, self.content, self.commit_frame, self.output_frame]:
            if hasattr(widget, '_update_background'):
                widget._update_background()
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        global theme_mode
        theme_mode = "flatly" if theme_mode == "darkly" else "darkly"
        
        # Change theme
        self.style.theme_use(theme_mode)
        
        # Update theme button text
        self.theme_button.config(text="🌙" if theme_mode == "darkly" else "☀️")
        
        # Reconfigure styles
        self.configure_styles()
        
        # Update glassmorphic frames
        self.on_window_resize()
    
    def clear_commit_placeholder(self, event):
        """Clear placeholder text when entry gains focus"""
        if self.commit_entry.get() == "Enter commit message...":
            self.commit_entry.delete(0, tk.END)
    
    def restore_commit_placeholder(self, event):
        """Restore placeholder text when entry loses focus"""
        if not self.commit_entry.get():
            self.commit_entry.insert(0, "Enter commit message...")
    
    def select_directory(self):
        """Select Git repository directory"""
        global repo_directory
        selected_directory = filedialog.askdirectory(title="Select Git Repository Directory")
        if selected_directory:
            repo_directory = selected_directory
            os.chdir(repo_directory)
            self.directory_label.config(text=f"Repository: {os.path.basename(repo_directory)}")
            self.output_text.insert(END, f"Changed working directory to: {repo_directory}\n")
            self.output_text.see(END)
            
            # Update status bar
            self.status_bar.config(text=f"Repository: {os.path.basename(repo_directory)} | Ready")
            
            # Check if it's a git repository
            self.run_git_command("git status")
    
    def run_git_command(self, command):
        """Run Git command with loading animation"""
        if not repo_directory:
            messagebox.showwarning("Repository Not Selected", "Please select a Git repository directory first.")
            return
        
        # Show loading animation
        self.show_loading()
        
        # Update status bar
        self.status_bar.config(text=f"Running: {command}")
        
        # Run command in a separate thread
        threading.Thread(target=self._execute_command, args=(command,), daemon=True).start()
    
    def _execute_command(self, command):
        """Execute Git command in a background thread"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            output = result.stdout if result.stdout else result.stderr
            
            # Update UI in the main thread
            self.root.after(0, self._update_output, command, output)
        except Exception as e:
            # Handle errors in the main thread
            self.root.after(0, self._show_error, str(e))
    
    def _update_output(self, command, output):
        """Update output text and status bar"""
        self.output_text.insert(END, f"\n> {command}\n{output}\n")
        self.output_text.see(END)
        self.status_bar.config(text=f"Completed: {command}")
        self.hide_loading()
    
    def _show_error(self, error_message):
        """Display error message"""
        messagebox.showerror("Error", error_message)
        self.status_bar.config(text=f"Error: {error_message[:30]}...")
        self.hide_loading()
    
    def git_add(self):
        """Git add command"""
        self.run_git_command("git add .")
    
    def git_commit(self):
        """Git commit command"""
        commit_message = self.commit_entry.get()
        if commit_message and commit_message != "Enter commit message...":
            self.run_git_command(f'git commit -m "{commit_message}"')
            # Clear the commit message
            self.commit_entry.delete(0, tk.END)
            self.commit_entry.insert(0, "Enter commit message...")
        else:
            messagebox.showwarning("Commit Message", "Please enter a commit message.")
    
    def git_push(self):
        """Git push command"""
        self.run_git_command("git push")
    
    def git_pull(self):
        """Git pull command"""
        self.run_git_command("git pull")


if __name__ == "__main__":
    root = ttk.Window(themename=theme_mode)
    app = GitGUI(root)
    root.mainloop()
