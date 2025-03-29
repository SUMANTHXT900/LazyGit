from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
import subprocess
import os
import json
import sys
import time
import threading
import tkinter as tk
from tkinter import filedialog
import signal
import logging
import traceback
import webbrowser
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import GitPython, but handle errors gracefully
try:
    import git
    git_available = True
except ImportError:
    git_available = False
    logger.warning("GitPython not installed. Some functionality will be limited.")
except Exception as e:
    git_available = False
    logger.warning(f"Error importing GitPython: {str(e)}. Some functionality will be limited.")

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Constants
CONFIG_FILE = 'config.json'
REPOS_FILE = 'repositories.json'
terminalOutput = []
gitStatus = {}
currentDirectory = None
isProcessing = False

# Global variable to store selected directory
selected_directory = None
directory_selected_event = threading.Event()

# Variable to control server shutdown
server_shutdown_requested = False

# Check if Git is available on the system
def check_git_available():
    try:
        # Try to run git version command
        result = subprocess.run(['git', '--version'], 
                               text=True,
                               capture_output=True)
        if result.returncode == 0:
            logger.info(f"Git found: {result.stdout.strip()}")
            return True
        else:
            logger.warning(f"Git not found: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.warning(f"Error checking Git availability: {str(e)}")
        return False

# Set git_available based on executable check
git_executable_available = check_git_available()

# Load the last used directory from config.json
def load_config():
    global currentDirectory
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                if 'directory' in config and os.path.isdir(config['directory']):
                    currentDirectory = config['directory']
                    logger.info(f"Loaded directory from config: {currentDirectory}")
                    return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
    return {}

# Save the selected directory to config.json
def save_config():
    try:
        config = {'directory': currentDirectory} if currentDirectory else {}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        
        logger.info("Config saved successfully")
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")

# Function to get saved repositories
def get_saved_repositories():
    try:
        if os.path.exists(REPOS_FILE):
            with open(REPOS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading repositories: {str(e)}")
        return []

# Function to save a new repository to the list
def save_repository(directory):
    try:
        repositories = get_saved_repositories()
        
        # Check if directory already exists in the list
        if directory not in repositories:
            repositories.append(directory)
            
            # Save back to file
            with open(REPOS_FILE, 'w') as f:
                json.dump(repositories, f)
            
            logger.info(f"Added repository to list: {directory}")
        return True
    except Exception as e:
        logger.error(f"Error saving repository to list: {str(e)}")
        return False

@app.route('/')
def index():
    repositories = get_saved_repositories()
    # Add current timestamp for the welcome message
    current_time = time.strftime('%Y-%m-%dT%H:%M:%S')
    return render_template('index.html', repositories=repositories, current_directory=currentDirectory, current_time=current_time)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/get-repositories', methods=['GET'])
def get_repositories():
    """Get all saved repositories for updating the dropdown"""
    try:
        repositories = get_saved_repositories()
        return jsonify({
            "success": True,
            "repositories": repositories,
            "current_directory": currentDirectory
        })
    except Exception as e:
        logger.error(f"Error getting repositories: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/select-directory-dialog', methods=['GET'])
def select_directory_dialog():
    """Open a dialog to select a directory and add it to the repository list"""
    global currentDirectory
    try:
        # Create and hide the tkinter root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Show the directory selection dialog
        directory = filedialog.askdirectory(title="Select Git Repository")
        root.destroy()
        
        if not directory:
            # User cancelled the dialog
            return redirect(url_for('index'))
        
        # Normalize path format
        directory = os.path.normpath(directory)
        
        # Check if it's a git repository
        try:
            if not git_available or not git_executable_available:
                logger.warning("Git functionality is limited because GitPython is not available or Git is not installed")
                # Still allow directory to be set, but warn
                currentDirectory = directory
                save_repository(directory)
                save_config()
                return redirect(url_for('index'))

            repo = git.Repo(directory)
            
            # Save the directory
            currentDirectory = directory
            
            # Add to repositories list
            save_repository(directory)
            
            # Update config
            save_config()
            
            return redirect(url_for('index'))
        except git.exc.InvalidGitRepositoryError:
            # Not a valid git repository
            logger.warning(f"Not a git repository: {directory}")
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error validating git repository: {str(e)}")
            # Still allow directory to be set, but log the error
            currentDirectory = directory
            save_repository(directory)
            save_config()
            return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Error in directory selection: {str(e)}")
        return redirect(url_for('index'))

@app.route('/set-directory', methods=['POST'])
def set_directory():
    global currentDirectory, isProcessing
    
    if isProcessing:
        return jsonify({"error": "Another operation is in progress"}), 409
    
    isProcessing = True
    
    try:
        data = request.get_json()
        directory = data.get('directory', '').strip()
        
        logger.info(f"Setting directory to: {directory}")
        
        if not directory:
            isProcessing = False
            return jsonify({"error": "No directory provided"}), 400
        
        if not os.path.exists(directory):
            isProcessing = False
            return jsonify({"error": f"Directory does not exist: {directory}"}), 400
        
        # Change to the directory to verify it's a git repository
        os.chdir(directory)
        
        try:
            if not git_executable_available:
                logger.warning("Git executable not found, but still setting directory")
                currentDirectory = directory
                save_config()
                save_repository(directory)
                return jsonify({
                    "success": True, 
                    "message": "Repository set successfully (Git functionality may be limited)", 
                    "directory": directory
                })

            # Verify it's a git repository
            subprocess.check_output(['git', 'status'], stderr=subprocess.STDOUT)
            
            # Set the current directory
            currentDirectory = directory
            
            # Save to config
            save_config()
            
            # Add to repositories list
            save_repository(directory)
            
            return jsonify({"success": True, "message": "Repository set successfully", "directory": directory})
        except subprocess.CalledProcessError as e:
            # If git isn't available, we still set the directory but with a warning
            if not git_executable_available:
                currentDirectory = directory
                save_config()
                save_repository(directory)
                isProcessing = False
                return jsonify({
                    "success": True, 
                    "message": "Directory set, but git operations will be limited", 
                    "directory": directory
                })
            isProcessing = False
            return jsonify({"success": False, "error": f"Not a valid git repository: {str(e)}"}), 400
    except Exception as e:
        isProcessing = False
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        isProcessing = False

@app.route('/status', methods=['GET'])
def get_status():
    global currentDirectory
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        if currentDirectory:
            if os.path.exists(currentDirectory):
                cmd = subprocess.Popen(['git', '-C', currentDirectory, 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = cmd.communicate()
                
                if stderr:
                    app.logger.error(f"Git status error: {stderr.decode('utf-8')}")
                    return jsonify({'success': False, 'error': stderr.decode('utf-8')})
                
                output = stdout.decode('utf-8')
                return jsonify({'success': True, 'output': output})
            else:
                return jsonify({'success': False, 'error': 'Selected directory does not exist'})
        else:
            return jsonify({'success': False, 'error': 'No directory selected'})
    except Exception as e:
        app.logger.error(f"Error in get_status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/add', methods=['GET', 'POST'])
def add_changes():
    global currentDirectory, isProcessing
    isProcessing = False  # Reset processing state
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        if not currentDirectory:
            return jsonify({'success': False, 'error': 'No directory selected'})
        
        if not os.path.exists(currentDirectory):
            return jsonify({'success': False, 'error': 'Selected directory does not exist'})
        
        cmd = subprocess.Popen(['git', '-C', currentDirectory, 'add', '.'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = cmd.communicate()
        
        if stderr and b'error' in stderr.lower():
            app.logger.error(f"Git add error: {stderr.decode('utf-8')}")
            return jsonify({'success': False, 'error': stderr.decode('utf-8')})
        
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error in add_changes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/commit', methods=['POST'])
def commit_changes():
    global currentDirectory, isProcessing
    isProcessing = False  # Reset processing state
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'No commit message provided'})
        
        message = data['message']
        
        if not currentDirectory:
            return jsonify({'success': False, 'error': 'No directory selected'})
        
        if not os.path.exists(currentDirectory):
            return jsonify({'success': False, 'error': 'Selected directory does not exist'})
        
        cmd = subprocess.Popen(['git', '-C', currentDirectory, 'commit', '-m', message], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = cmd.communicate()
        
        stdout_text = stdout.decode('utf-8') if stdout else ""
        stderr_text = stderr.decode('utf-8') if stderr else ""
        
        if "fatal:" in stderr_text or "error:" in stderr_text:
            app.logger.error(f"Git commit error: {stderr_text}")
            return jsonify({'success': False, 'error': stderr_text})
        
        if "nothing to commit" in stdout_text or "nothing to commit" in stderr_text:
            return jsonify({'success': False, 'error': 'Nothing to commit. Stage changes first.'})
        
        return jsonify({'success': True, 'message': stdout_text})
    except Exception as e:
        app.logger.error(f"Error in commit_changes: {str(e)}")
        return jsonify({'success': False, 'error': f'Commit failed: {str(e)}'})

@app.route('/push', methods=['GET', 'POST'])
def push_changes():
    global currentDirectory, isProcessing
    isProcessing = False  # Reset processing state
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        if not currentDirectory:
            return jsonify({'success': False, 'error': 'No directory selected'})
        
        if not os.path.exists(currentDirectory):
            return jsonify({'success': False, 'error': 'Selected directory does not exist'})
        
        cmd = subprocess.Popen(['git', '-C', currentDirectory, 'push'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = cmd.communicate()
        
        # Git sometimes outputs information to stderr even on success
        stderr_text = stderr.decode('utf-8') if stderr else ""
        if "fatal:" in stderr_text or "error:" in stderr_text:
            app.logger.error(f"Git push error: {stderr_text}")
            return jsonify({'success': False, 'error': stderr_text})
        
        stdout_text = stdout.decode('utf-8') if stdout else ""
        message = stdout_text or stderr_text
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        app.logger.error(f"Error in push_changes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/pull', methods=['GET', 'POST'])
def pull_changes():
    global currentDirectory, isProcessing
    isProcessing = False  # Reset processing state
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        if not currentDirectory:
            return jsonify({'success': False, 'error': 'No directory selected'})
        
        if not os.path.exists(currentDirectory):
            return jsonify({'success': False, 'error': 'Selected directory does not exist'})
        
        cmd = subprocess.Popen(['git', '-C', currentDirectory, 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = cmd.communicate()
        
        # Git sometimes outputs information to stderr even on success
        stderr_text = stderr.decode('utf-8') if stderr else ""
        if "fatal:" in stderr_text or "error:" in stderr_text:
            app.logger.error(f"Git pull error: {stderr_text}")
            return jsonify({'success': False, 'error': stderr_text})
        
        stdout_text = stdout.decode('utf-8') if stdout else ""
        message = stdout_text or stderr_text
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        app.logger.error(f"Error in pull_changes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/log', methods=['GET'])
def log():
    global currentDirectory, isProcessing
    
    if isProcessing:
        return jsonify({"error": "Another operation is in progress"}), 409
    
    if not currentDirectory:
        return jsonify({"error": "No directory set"}), 400
    
    isProcessing = True
    
    try:
        if not git_executable_available:
            isProcessing = False
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        # Change to the directory
        os.chdir(currentDirectory)
        
        # Run git log
        process = subprocess.Popen(['git', 'log', '--pretty=format:%h|%an|%ar|%s', '-n', '20'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        output_text = stdout.decode('utf-8', errors='replace')
        
        if not output_text:
            return jsonify({"success": True, "commits": [], "directory": currentDirectory})
        
        # Parse the log output
        commits = []
        for line in output_text.split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) == 4:
                    commit = {
                        'hash': parts[0],
                        'author': parts[1],
                        'date': parts[2],
                        'message': parts[3]
                    }
                    commits.append(commit)
        
        return jsonify({"success": True, "commits": commits, "directory": currentDirectory})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        isProcessing = False

@app.route('/switch-repository', methods=['POST'])
def switch_repository():
    """Switch to a different repository from the saved list"""
    global currentDirectory, isProcessing
    
    if isProcessing:
        return jsonify({"error": "Another operation is in progress"}), 409
    
    isProcessing = True
    
    try:
        data = request.get_json()
        directory = data.get('directory', '').strip()
        
        if not directory:
            isProcessing = False
            return jsonify({"success": False, "error": "No directory provided"}), 400
        
        if not os.path.exists(directory):
            isProcessing = False
            return jsonify({"success": False, "error": f"Directory does not exist: {directory}"}), 400
        
        # Verify it's a git repository
        try:
            if not git_available or not git_executable_available:
                logger.warning("Git functionality is limited - still setting directory")
                currentDirectory = directory
                save_config()
                return jsonify({
                    "success": True, 
                    "message": "Switched to directory (Git functionality limited)", 
                    "directory": directory
                })
                
            repo = git.Repo(directory)
            currentDirectory = directory
            
            # Save to config
            save_config()
            
            return jsonify({"success": True, "message": "Switched to repository", "directory": directory})
        except git.exc.InvalidGitRepositoryError:
            isProcessing = False
            return jsonify({"success": False, "error": "Not a valid git repository"}), 400
        except Exception as e:
            logger.error(f"Error validating git repository: {str(e)}")
            # Still set the directory but with a warning
            currentDirectory = directory
            save_config()
            isProcessing = False
            return jsonify({
                "success": True,
                "message": f"Switched to directory (warning: {str(e)})",
                "directory": directory
            })
    except Exception as e:
        isProcessing = False
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        isProcessing = False

@app.route('/git-init', methods=['POST'])
def git_init():
    """Initialize a new Git repository in the current directory"""
    global currentDirectory, isProcessing
    
    if isProcessing:
        isProcessing = False  # Reset if stuck
    
    if not currentDirectory:
        return jsonify({"success": False, "error": "No directory set"}), 400
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        # Change to the directory
        os.chdir(currentDirectory)
        
        # Check if it's already a git repository
        try:
            if git_available:
                git.Repo(currentDirectory)
                return jsonify({
                    "success": False, 
                    "error": "Directory is already a Git repository"
                }), 400
        except git.exc.InvalidGitRepositoryError:
            # Not a git repo, so we can initialize
            pass
        except Exception:
            # If GitPython fails, we'll still try with subprocess
            pass
        
        # Run git init
        process = subprocess.Popen(['git', 'init'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        output_text = stdout.decode('utf-8', errors='replace')
        error_text = stderr.decode('utf-8', errors='replace')
        
        if process.returncode != 0:
            logger.error(f"Error in git init: {error_text}")
            return jsonify({"success": False, "error": error_text}), 500
        
        # Save the repository to the list
        save_repository(currentDirectory)
        
        return jsonify({
            "success": True, 
            "message": output_text or "Repository initialized successfully",
            "directory": currentDirectory
        })
    except Exception as e:
        logger.error(f"Exception in git init: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/git-remote-add', methods=['POST'])
def git_remote_add():
    """Add a remote repository"""
    global currentDirectory, isProcessing
    
    if isProcessing:
        isProcessing = False  # Reset if stuck
    
    if not currentDirectory:
        return jsonify({"success": False, "error": "No directory set"}), 400
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        data = request.get_json()
        remote_name = data.get('name', '').strip()
        remote_url = data.get('url', '').strip()
        
        if not remote_name or not remote_url:
            return jsonify({"success": False, "error": "Remote name and URL are required"}), 400
        
        # Change to the directory
        os.chdir(currentDirectory)
        
        # Run git remote add
        process = subprocess.Popen(['git', 'remote', 'add', remote_name, remote_url], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        error_text = stderr.decode('utf-8', errors='replace')
        
        if process.returncode != 0:
            logger.error(f"Error adding remote: {error_text}")
            return jsonify({"success": False, "error": error_text}), 500
        
        return jsonify({
            "success": True, 
            "message": f"Remote '{remote_name}' added successfully",
            "remote": {"name": remote_name, "url": remote_url}
        })
    except Exception as e:
        logger.error(f"Exception in git remote add: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/git-remotes', methods=['GET'])
def git_remotes():
    """Get list of remote repositories"""
    global currentDirectory, isProcessing
    
    if isProcessing:
        isProcessing = False  # Reset if stuck
    
    if not currentDirectory:
        return jsonify({"success": False, "error": "No directory set"}), 400
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        # Change to the directory
        os.chdir(currentDirectory)
        
        # Run git remote -v
        process = subprocess.Popen(['git', 'remote', '-v'], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        output_text = stdout.decode('utf-8', errors='replace')
        
        # Parse remote output
        remotes = []
        for line in output_text.split('\n'):
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                url = parts[1]
                # Check if remote already exists in the list
                if not any(r['name'] == name for r in remotes):
                    remotes.append({
                        'name': name,
                        'url': url
                    })
        
        return jsonify({
            "success": True,
            "remotes": remotes
        })
    except Exception as e:
        logger.error(f"Exception in git remotes: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/git-branches', methods=['GET'])
def git_branches():
    """Get list of branches in the repository"""
    global currentDirectory, isProcessing
    
    if isProcessing:
        isProcessing = False  # Reset if stuck
    
    if not currentDirectory:
        return jsonify({"success": False, "error": "No directory set"}), 400
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        # Change to the directory
        os.chdir(currentDirectory)
        
        # Run git branch
        process = subprocess.Popen(['git', 'branch', '--all'], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        output_text = stdout.decode('utf-8', errors='replace')
        
        # Parse branch output
        branches = []
        current_branch = None
        
        for line in output_text.split('\n'):
            if not line.strip():
                continue
                
            is_current = line.startswith('*')
            branch_name = line[2:].strip() if is_current else line.strip()
            
            if is_current:
                current_branch = branch_name
                
            if branch_name and branch_name not in branches:
                branches.append(branch_name)
        
        return jsonify({
            "success": True,
            "branches": branches,
            "current_branch": current_branch
        })
    except Exception as e:
        logger.error(f"Exception in git branches: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/git-branch-create', methods=['POST'])
def git_branch_create():
    """Create a new branch"""
    global currentDirectory, isProcessing
    
    if isProcessing:
        isProcessing = False  # Reset if stuck
    
    if not currentDirectory:
        return jsonify({"success": False, "error": "No directory set"}), 400
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        data = request.get_json()
        branch_name = data.get('name', '').strip()
        
        if not branch_name:
            return jsonify({"success": False, "error": "Branch name is required"}), 400
        
        # Change to the directory
        os.chdir(currentDirectory)
        
        # Run git branch
        process = subprocess.Popen(['git', 'branch', branch_name], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        error_text = stderr.decode('utf-8', errors='replace')
        
        if process.returncode != 0:
            logger.error(f"Error creating branch: {error_text}")
            return jsonify({"success": False, "error": error_text}), 500
        
        return jsonify({
            "success": True, 
            "message": f"Branch '{branch_name}' created successfully"
        })
    except Exception as e:
        logger.error(f"Exception in git branch create: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/git-checkout', methods=['POST'])
def git_checkout():
    """Checkout a branch"""
    global currentDirectory, isProcessing
    
    if isProcessing:
        isProcessing = False  # Reset if stuck
    
    if not currentDirectory:
        return jsonify({"success": False, "error": "No directory set"}), 400
    
    try:
        if not git_executable_available:
            return jsonify({
                'success': False, 
                'error': 'Git is not available on your system. Please install Git or set the correct path.'
            })
            
        data = request.get_json()
        branch_name = data.get('branch', '').strip()
        
        if not branch_name:
            return jsonify({"success": False, "error": "Branch name is required"}), 400
        
        # Change to the directory
        os.chdir(currentDirectory)
        
        # Run git checkout
        process = subprocess.Popen(['git', 'checkout', branch_name], 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        output_text = stdout.decode('utf-8', errors='replace')
        error_text = stderr.decode('utf-8', errors='replace')
        
        if process.returncode != 0:
            logger.error(f"Error checking out branch: {error_text}")
            return jsonify({"success": False, "error": error_text}), 500
        
        return jsonify({
            "success": True, 
            "message": output_text or f"Switched to branch '{branch_name}'"
        })
    except Exception as e:
        logger.error(f"Exception in git checkout: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the server"""
    try:
        logger.info("Shutdown requested")
        # Get the werkzeug server object
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        return jsonify({"success": True, "message": "Server shutting down..."})
    except Exception as e:
        logger.error(f"Error in shutdown: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Check for config when the app starts
load_config()

# Function to check environment setup and show warnings
def check_environment():
    # Check for Git
    if not git_executable_available:
        logger.warning("Git executable not found in PATH. Git operations will be disabled.")
        logger.warning("To enable Git functionality:")
        logger.warning("1. Install Git from https://git-scm.com/downloads")
        logger.warning("2. Make sure Git is in your system PATH")
        logger.warning("3. Or set the GIT_PYTHON_GIT_EXECUTABLE environment variable")
        
    # Check for GitPython
    if not git_available:
        logger.warning("GitPython module not available. Some Git operations will be limited.")
        logger.warning("To enable full Git functionality: pip install gitpython")

# Open browser after a slight delay to ensure server is running
def open_browser():
    time.sleep(1.5)  # Short delay to ensure server is up
    try:
        webbrowser.open('http://127.0.0.1:5000')
        logger.info("Opened browser automatically")
    except Exception as e:
        logger.error(f"Failed to open browser: {str(e)}")

if __name__ == '__main__':
    # Log environment status
    check_environment()
    
    # Start browser opening in a separate thread
    threading.Thread(target=open_browser).start()
    
    # Start the Flask app
    try:
        logger.info("Starting Flask server on http://127.0.0.1:5000")
        app.run(debug=False, port=5000)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        print(f"ERROR: Failed to start server: {str(e)}")
        print("Press Enter to exit...")
        input()  # Keep console window open on error 