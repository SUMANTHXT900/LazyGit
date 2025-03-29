// DOM Elements
const repositoryDropdown = document.getElementById('repository-dropdown');
const addRepoBtn = document.getElementById('add-repo-btn');
const refreshReposBtn = document.getElementById('refresh-repos-btn');
const currentDirectoryDisplay = document.getElementById('current-directory');
const themeToggleBtn = document.getElementById('theme-toggle-btn');
const clearOutputBtn = document.getElementById('clear-output-btn');
const terminalOutput = document.getElementById('terminal-output');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingMessage = document.querySelector('.loading-message');

// Git operation buttons
const gitStatusBtn = document.getElementById('git-status-btn');
const gitAddBtn = document.getElementById('git-add-btn');
const gitCommitBtn = document.getElementById('git-commit-btn');
const gitPushBtn = document.getElementById('git-push-btn');
const gitPullBtn = document.getElementById('git-pull-btn');
const gitLogBtn = document.getElementById('git-log-btn');

// Advanced Git operations
const gitInitBtn = document.getElementById('git-init-btn');
const gitBranchesBtn = document.getElementById('git-branches-btn');
const gitRemotesBtn = document.getElementById('git-remotes-btn');
const gitNewBranchBtn = document.getElementById('git-new-branch-btn');
const gitCheckoutBtn = document.getElementById('git-checkout-btn');
const gitAddRemoteBtn = document.getElementById('git-add-remote-btn');

// Modals
const commitModal = document.getElementById('commit-modal');
const commitMessageInput = document.getElementById('commit-message');
const submitCommitBtn = document.getElementById('submit-commit-btn');
const commitHistorySection = document.getElementById('commit-history-section');
const commitList = document.getElementById('commit-list');
const closeHistoryBtn = document.getElementById('close-history-btn');

// Branch modals
const newBranchModal = document.getElementById('new-branch-modal');
const branchNameInput = document.getElementById('branch-name');
const createBranchBtn = document.getElementById('create-branch-btn');
const checkoutModal = document.getElementById('checkout-modal');
const branchSelect = document.getElementById('branch-select');
const checkoutBranchBtn = document.getElementById('checkout-branch-btn');

// Remote modals
const addRemoteModal = document.getElementById('add-remote-modal');
const remoteNameInput = document.getElementById('remote-name');
const remoteUrlInput = document.getElementById('remote-url');
const addRemoteConfirmBtn = document.getElementById('add-remote-confirm-btn');

// State variables
let isProcessing = false;
let processingTimeout = null;
let currentRepoPath = '';
let gitAvailable = true; // Track Git availability

// Initialize application
function initializeApp() {
    setupEventListeners();
    applySavedTheme();
    checkGitAvailability();
    updateUIBasedOnCurrentRepo();

    // Automatically set processing state to false after 15 seconds if stuck
    setInterval(resetProcessingIfStuck, 15000);
}

// Check if Git is available
function checkGitAvailability() {
    fetch('/status')
    .then(response => response.json())
    .then(data => {
        if (data.error && data.error.includes('Git is not available')) {
            gitAvailable = false;
            showGitUnavailableWarning();
        }
    })
    .catch(error => {
        console.error('Error checking Git availability:', error);
    });
}

// Show warning when Git is not available
function showGitUnavailableWarning() {
    const warningMessage = `
        Git executable was not found on your system. Git operations will not work.
        
        To fix this:
        1. Install Git from https://git-scm.com/downloads
        2. Make sure Git is in your system PATH
        3. Restart the application
    `;
    
    logToTerminal(warningMessage, 'error');
    
    // Also add a warning banner
    const warningBanner = document.createElement('div');
    warningBanner.className = 'warning-banner';
    warningBanner.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <span>Git not available - Install Git to enable full functionality</span>
        <button class="close-banner"><i class="fas fa-times"></i></button>
    `;
    
    document.querySelector('.container').prepend(warningBanner);
    
    // Add event listener to close button
    warningBanner.querySelector('.close-banner').addEventListener('click', function() {
        warningBanner.remove();
    });
}

// Processing API responses with improved error handling
function processApiResponse(response, successCallback, errorCallback) {
    // Handle non-JSON responses gracefully
    if (!response.ok) {
        if (response.status === 500) {
            return response.text().then(text => {
                logToTerminal(`Server error (500): ${text.substring(0, 200)}...`, 'error');
                if (errorCallback) errorCallback(text);
            });
        }
        return response.json().catch(e => {
            // Handle parsing error (not JSON)
            logToTerminal(`Error: Server returned invalid response`, 'error');
            if (errorCallback) errorCallback('Server returned invalid response');
        }).then(data => {
            if (data) {
                logToTerminal(`Error: ${data.error || 'Unknown error'}`, 'error');
                if (errorCallback) errorCallback(data.error || 'Unknown error');
            }
        });
    }
    
    // Handle JSON responses
    return response.json().then(data => {
        if (data.success) {
            if (successCallback) successCallback(data);
        } else {
            // Check for Git not available error
            if (data.error && data.error.includes('Git is not available')) {
                gitAvailable = false;
                showGitUnavailableWarning();
            }
            
            logToTerminal(`Error: ${data.error || 'Unknown error'}`, 'error');
            if (errorCallback) errorCallback(data.error || 'Unknown error');
        }
    }).catch(e => {
        logToTerminal(`Error parsing response: ${e.message}`, 'error');
        if (errorCallback) errorCallback(e.message);
    });
}

// Override fetch for better error handling
const originalFetch = window.fetch;
window.fetch = function(url, options) {
    return originalFetch(url, options).catch(error => {
        logToTerminal(`Network error: ${error.message}. Check your connection.`, 'error');
        throw error;
    });
};

// Reset processing state if stuck
function resetProcessingIfStuck() {
    if (isProcessing) {
        const lastActivityTime = parseInt(localStorage.getItem('lastActivityTime') || '0');
        const currentTime = Date.now();
        
        // If more than 20 seconds have passed since the last activity and isProcessing is still true
        if (currentTime - lastActivityTime > 20000) {
            logToTerminal('Processing state reset due to timeout', 'warning');
            resetProcessingState();
        }
    }
}

// Reset processing state
function resetProcessingState() {
    clearTimeout(processingTimeout);
    isProcessing = false;
    loadingOverlay.classList.remove('active');
}

// Set processing state with timeout
function setProcessing(message = 'Processing operation...') {
    isProcessing = true;
    loadingMessage.textContent = message;
    loadingOverlay.classList.add('active');
    
    // Store the time of the last activity
    localStorage.setItem('lastActivityTime', Date.now().toString());
    
    // Set a timeout to automatically reset the processing state after 30 seconds
    // This prevents the UI from getting stuck if an operation fails
    clearTimeout(processingTimeout);
    processingTimeout = setTimeout(() => {
        resetProcessingState();
        logToTerminal('Operation timed out. The UI has been reset.', 'warning');
    }, 30000);
}

// Set up event listeners
function setupEventListeners() {
    // Repository management
    repositoryDropdown.addEventListener('change', handleRepositoryChange);
    addRepoBtn.addEventListener('click', openDirectoryDialog);
    refreshReposBtn.addEventListener('click', refreshRepositories);
    
    // Basic Git operations
    gitStatusBtn.addEventListener('click', getGitStatus);
    gitAddBtn.addEventListener('click', stageChanges);
    gitCommitBtn.addEventListener('click', showCommitDialog);
    gitPushBtn.addEventListener('click', pushChanges);
    gitPullBtn.addEventListener('click', pullChanges);
    gitLogBtn.addEventListener('click', getCommitHistory);
    
    // Advanced Git operations
    gitInitBtn.addEventListener('click', initializeRepository);
    gitBranchesBtn.addEventListener('click', listBranches);
    gitRemotesBtn.addEventListener('click', listRemotes);
    gitNewBranchBtn.addEventListener('click', showNewBranchDialog);
    gitCheckoutBtn.addEventListener('click', showCheckoutDialog);
    gitAddRemoteBtn.addEventListener('click', showAddRemoteDialog);
    
    // Modal actions
    submitCommitBtn.addEventListener('click', commitChanges);
    document.querySelectorAll('.modal-close-btn, .modal-cancel-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.dataset.target || 'commit-modal';
            hideModal(target);
        });
    });
    
    closeHistoryBtn.addEventListener('click', () => {
        hideModal('commit-history-section');
    });
    
    // Branch modal actions
    createBranchBtn.addEventListener('click', createNewBranch);
    checkoutBranchBtn.addEventListener('click', checkoutSelectedBranch);
    
    // Remote modal actions
    addRemoteConfirmBtn.addEventListener('click', addRemoteRepository);
    
    // UI
    themeToggleBtn.addEventListener('click', toggleTheme);
    clearOutputBtn.addEventListener('click', clearTerminal);
    
    // Shutdown button
    const shutdownBtn = document.getElementById('shutdown-btn');
    if (shutdownBtn) {
        shutdownBtn.addEventListener('click', shutdownServer);
    }
}

// Update UI based on current repository
function updateUIBasedOnCurrentRepo() {
    const hasRepo = currentDirectoryDisplay.textContent !== 'No repository selected';
    currentRepoPath = hasRepo ? currentDirectoryDisplay.textContent : '';
    
    const gitButtons = document.querySelectorAll('.git-operations button, .git-advanced-operations button');
    gitButtons.forEach(btn => {
        btn.disabled = !hasRepo;
    });
}

// Repository Management
function handleRepositoryChange() {
    const selectedRepo = repositoryDropdown.value;
    if (!selectedRepo) return;
    
    if (isProcessing) {
        resetProcessingState();
    }
    
    setProcessing('Switching repository...');
    
    fetch('/switch-repository', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ directory: selectedRepo })
    })
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            currentDirectoryDisplay.textContent = selectedRepo;
            currentRepoPath = selectedRepo;
            updateUIBasedOnCurrentRepo();
            logToTerminal(`Switched to repository: ${selectedRepo}`, 'success');
        } else {
            logToTerminal(`Failed to switch repository: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error switching repository: ${error}`, 'error');
    });
}

function openDirectoryDialog() {
    if (isProcessing) {
        resetProcessingState();
    }
    
    setProcessing('Opening directory selection dialog...');
    
    fetch('/select-directory-dialog')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            refreshRepositories();
            logToTerminal(`Directory selected: ${data.directory}`, 'success');
        } else {
            logToTerminal(`No directory selected or error: ${data.error || 'User cancelled'}`, 'info');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error selecting directory: ${error}`, 'error');
    });
}

function refreshRepositories() {
    if (isProcessing) {
        resetProcessingState();
    }
    
    setProcessing('Refreshing repositories...');
    
    fetch('/get-repositories')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            const currentRepo = repositoryDropdown.value;
            
            // Clear dropdown
            while (repositoryDropdown.options.length > 1) {
                repositoryDropdown.remove(1);
            }
            
            // Add repositories
            data.repositories.forEach(repo => {
                const option = document.createElement('option');
                option.value = repo;
                option.textContent = repo;
                repositoryDropdown.appendChild(option);
            });
            
            // Restore selection if exists
            if (currentRepo && data.repositories.includes(currentRepo)) {
                repositoryDropdown.value = currentRepo;
            }
            
            logToTerminal(`Repositories refreshed (${data.repositories.length} found)`, 'success');
        } else {
            logToTerminal(`Failed to refresh repositories: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error refreshing repositories: ${error}`, 'error');
    });
}

// Basic Git Operations
function getGitStatus() {
    if (isProcessing) {
        resetProcessingState();
    }
    
    setProcessing('Getting git status...');
    
    fetch('/status')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal('Git Status:', 'heading');
            data.output.split('\n').forEach(line => {
                logToTerminal(line, getStatusLineType(line));
            });
        } else {
            logToTerminal(`Error getting status: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function getStatusLineType(line) {
    if (line.includes('modified:')) return 'modified';
    if (line.includes('new file:')) return 'added';
    if (line.includes('deleted:')) return 'deleted';
    if (line.includes('Untracked files:')) return 'heading';
    if (line.includes('Changes not staged')) return 'heading';
    if (line.includes('Changes to be committed:')) return 'heading';
    if (line.includes('Your branch is ahead')) return 'warning';
    if (line.includes('Your branch is behind')) return 'warning';
    if (line.includes('nothing to commit')) return 'success';
    return 'info';
}

function stageChanges() {
    setProcessing('Staging changes...');
    
    fetch('/add')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal('Changes staged successfully', 'success');
            // Refresh status
            getGitStatus();
        } else {
            logToTerminal(`Error staging changes: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function showCommitDialog() {
    commitMessageInput.value = '';
    showModal('commit-modal');
}

function commitChanges() {
    const message = commitMessageInput.value.trim();
    if (!message) {
        logToTerminal('Commit message cannot be empty', 'error');
        return;
    }
    
    hideModal('commit-modal');
    setProcessing('Committing changes...');
    
    fetch('/commit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal(`Changes committed: ${message}`, 'success');
            // Refresh status
            getGitStatus();
        } else {
            logToTerminal(`Error committing changes: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function pushChanges() {
    setProcessing('Pushing changes to remote...');
    
    fetch('/push')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal('Changes pushed to remote successfully', 'success');
        } else {
            logToTerminal(`Error pushing changes: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function pullChanges() {
    setProcessing('Pulling changes from remote...');
    
    fetch('/pull')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal('Changes pulled from remote successfully', 'success');
            // Refresh status
            getGitStatus();
        } else {
            logToTerminal(`Error pulling changes: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function getCommitHistory() {
    setProcessing('Loading commit history...');
    
    fetch('/log')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            displayCommitHistory(data.commits);
        } else {
            logToTerminal(`Error getting commit history: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function displayCommitHistory(commits) {
    commitList.innerHTML = '';
    
    if (commits.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'commit-item empty';
        emptyMessage.textContent = 'No commits found in this repository';
        commitList.appendChild(emptyMessage);
    } else {
        commits.forEach(commit => {
            const commitItem = document.createElement('div');
            commitItem.className = 'commit-item';
            
            const commitHash = document.createElement('div');
            commitHash.className = 'commit-hash';
            commitHash.textContent = commit.hash;
            
            const commitInfo = document.createElement('div');
            commitInfo.className = 'commit-info';
            
            const commitTitle = document.createElement('div');
            commitTitle.className = 'commit-title';
            commitTitle.textContent = commit.message;
            
            const commitDetails = document.createElement('div');
            commitDetails.className = 'commit-details';
            commitDetails.textContent = `${commit.author} · ${commit.date}`;
            
            commitInfo.appendChild(commitTitle);
            commitInfo.appendChild(commitDetails);
            
            commitItem.appendChild(commitHash);
            commitItem.appendChild(commitInfo);
            
            commitList.appendChild(commitItem);
        });
    }
    
    showModal('commit-history-section');
}

// Advanced Git Operations
function initializeRepository() {
    if (isProcessing) {
        resetProcessingState();
    }
    
    if (!confirm('This will initialize a new Git repository in the current directory. Continue?')) {
        return;
    }
    
    setProcessing('Initializing Git repository...');
    
    fetch('/git-init')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal('Git repository initialized successfully', 'success');
            // Refresh status
            getGitStatus();
        } else {
            logToTerminal(`Error initializing repository: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function listBranches() {
    if (isProcessing) {
        resetProcessingState();
    }
    
    setProcessing('Fetching branches...');
    
    fetch('/git-branches')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal('Git Branches:', 'heading');
            data.branches.forEach(branch => {
                const prefix = branch.current ? '* ' : '  ';
                logToTerminal(`${prefix}${branch.name}`, branch.current ? 'success' : 'info');
            });
        } else {
            logToTerminal(`Error listing branches: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function listRemotes() {
    if (isProcessing) {
        resetProcessingState();
    }
    
    setProcessing('Fetching remotes...');
    
    fetch('/git-remotes')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            if (data.remotes.length === 0) {
                logToTerminal('No remote repositories configured', 'info');
            } else {
                logToTerminal('Git Remotes:', 'heading');
                data.remotes.forEach(remote => {
                    logToTerminal(`${remote.name} (${remote.url})`, 'info');
                });
            }
        } else {
            logToTerminal(`Error listing remotes: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function showNewBranchDialog() {
    branchNameInput.value = '';
    showModal('new-branch-modal');
}

function createNewBranch() {
    const branchName = branchNameInput.value.trim();
    if (!branchName) {
        logToTerminal('Branch name cannot be empty', 'error');
        return;
    }
    
    hideModal('new-branch-modal');
    setProcessing('Creating new branch...');
    
    fetch('/git-branch-create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: branchName })
    })
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal(`Branch "${branchName}" created successfully`, 'success');
            // Refresh branches
            listBranches();
        } else {
            logToTerminal(`Error creating branch: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function showCheckoutDialog() {
    // Clear previous options
    while (branchSelect.options.length > 1) {
        branchSelect.remove(1);
    }
    
    setProcessing('Loading branches...');
    
    fetch('/git-branches')
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            data.branches.forEach(branch => {
                const option = document.createElement('option');
                option.value = branch.name;
                option.textContent = branch.name + (branch.current ? ' (current)' : '');
                option.disabled = branch.current;
                branchSelect.appendChild(option);
            });
            
            showModal('checkout-modal');
        } else {
            logToTerminal(`Error loading branches: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function checkoutSelectedBranch() {
    const branchName = branchSelect.value;
    if (!branchName) {
        logToTerminal('Please select a branch to checkout', 'error');
        return;
    }
    
    hideModal('checkout-modal');
    setProcessing(`Checking out branch "${branchName}"...`);
    
    fetch('/git-checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ branch: branchName })
    })
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal(`Switched to branch "${branchName}"`, 'success');
            // Refresh status
            getGitStatus();
        } else {
            logToTerminal(`Error checking out branch: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

function showAddRemoteDialog() {
    remoteNameInput.value = '';
    remoteUrlInput.value = '';
    showModal('add-remote-modal');
}

function addRemoteRepository() {
    const name = remoteNameInput.value.trim();
    const url = remoteUrlInput.value.trim();
    
    if (!name || !url) {
        logToTerminal('Remote name and URL are required', 'error');
        return;
    }
    
    hideModal('add-remote-modal');
    setProcessing('Adding remote repository...');
    
    fetch('/git-remote-add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, url })
    })
    .then(response => response.json())
    .then(data => {
        resetProcessingState();
        
        if (data.success) {
            logToTerminal(`Remote "${name}" added successfully`, 'success');
            // Refresh remotes
            listRemotes();
        } else {
            logToTerminal(`Error adding remote: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        resetProcessingState();
        logToTerminal(`Error: ${error}`, 'error');
    });
}

// Terminal Output Functions
function logToTerminal(message, type = 'info') {
    const timestamp = new Date().toISOString().replace('T', ' ').substr(0, 19);
    
    // Create the log entry
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    // Format the message based on type
    let icon, typeClass;
    
    switch (type) {
        case 'success':
            icon = '<i class="fas fa-check-circle"></i>';
            typeClass = 'success';
            break;
        case 'error':
            icon = '<i class="fas fa-times-circle"></i>';
            typeClass = 'error';
            break;
        case 'warning':
            icon = '<i class="fas fa-exclamation-triangle"></i>';
            typeClass = 'warning';
            break;
        case 'command':
            icon = '<i class="fas fa-terminal"></i>';
            typeClass = 'command';
            break;
        default:
            icon = '<i class="fas fa-info-circle"></i>';
            typeClass = 'info';
    }
    
    // Create HTML structure
    logEntry.innerHTML = `
        <span class="timestamp">${timestamp}</span>
        <span class="log-icon ${typeClass}">${icon}</span>
        <span class="message ${typeClass}">${formatMessage(message)}</span>
    `;
    
    // Add to terminal
    terminalOutput.appendChild(logEntry);
    
    // Scroll to bottom
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

function formatMessage(message) {
    // Convert JSON objects to formatted string
    if (typeof message === 'object') {
        return `<pre>${JSON.stringify(message, null, 2)}</pre>`;
    }
    
    // Handle multiline text
    if (message.includes('\n')) {
        return `<pre>${message}</pre>`;
    }
    
    // Escape HTML characters
    const escaped = message
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Highlight git command outputs
    return escaped
        .replace(/modified: (\S+)/g, 'modified: <span class="warning">$1</span>')
        .replace(/new file: (\S+)/g, 'new file: <span class="success">$1</span>')
        .replace(/deleted: (\S+)/g, 'deleted: <span class="error">$1</span>')
        .replace(/(On branch) (\S+)/g, '$1 <span class="success">$2</span>')
        .replace(/(HEAD detached at) (\S+)/g, '$1 <span class="warning">$2</span>')
        .replace(/(Changes not staged for commit)/g, '<span class="warning">$1</span>')
        .replace(/(Untracked files)/g, '<span class="info">$1</span>')
        .replace(/(Your branch is ahead)/g, '<span class="success">$1</span>')
        .replace(/(Your branch is behind)/g, '<span class="warning">$1</span>')
        .replace(/(nothing to commit, working tree clean)/g, '<span class="success">$1</span>');
}

function clearTerminal() {
    // Add a divider before clearing
    const divider = document.createElement('div');
    divider.className = 'terminal-divider';
    divider.innerHTML = '<span>Terminal cleared</span>';
    terminalOutput.appendChild(divider);
    
    // Wait a brief moment before clearing
    setTimeout(() => {
        terminalOutput.innerHTML = '';
        logToTerminal('Terminal cleared', 'info');
    }, 300);
}

function showLoadingOverlay(message = 'Processing...') {
    loadingMessage.textContent = message;
    loadingOverlay.classList.add('active');
}

function hideLoadingOverlay() {
    loadingOverlay.classList.remove('active');
}

function toggleTheme() {
    const isDarkMode = document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', isDarkMode ? 'true' : 'false');
    
    const icon = themeToggleBtn.querySelector('i');
    icon.className = isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
    
    logToTerminal(`Theme switched to ${isDarkMode ? 'dark' : 'light'} mode`, 'info');
}

function applySavedTheme() {
    const savedDarkMode = localStorage.getItem('darkMode');
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldBeDarkMode = savedDarkMode === null ? prefersDarkMode : savedDarkMode === 'true';
    
    if (shouldBeDarkMode) {
        document.body.classList.add('dark-mode');
        themeToggleBtn.querySelector('i').className = 'fas fa-sun';
    } else {
        document.body.classList.remove('dark-mode');
        themeToggleBtn.querySelector('i').className = 'fas fa-moon';
    }
}

// Toggle modal display
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
    }
}

// Function to shut down the server
function shutdownServer() {
    if (confirm('Are you sure you want to shut down the application?')) {
        setProcessing('Shutting down server...');
        
        fetch('/shutdown', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                logToTerminal('Server is shutting down. You can close this window.', 'success');
                // Display a message to the user
                alert('The application has been shut down. You can close this window now.');
            } else {
                resetProcessingState();
                logToTerminal(`Failed to shut down the server: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            // The server might shut down before we get a response
            setTimeout(() => {
                resetProcessingState();
                logToTerminal('Server has shut down. You can close this window.', 'success');
                alert('The application has been shut down. You can close this window now.');
            }, 1000);
        });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp); 