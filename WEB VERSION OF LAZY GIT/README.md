# LazyGit - Modern Web-Based Git GUI

LazyGit is a feature-rich web-based Git GUI that allows you to perform common Git operations through a sleek, modern interface. Built with Flask for the backend and pure HTML, CSS, and JavaScript for the frontend.

## Features

- **Native Windows Directory Picker**: Select Git repositories using the native Windows file dialog
- **Remember Last Directory**: Automatically remembers the last used Git repository
- **Dark Mode Support**: Toggle between light and dark themes
- **Git Operations**:
  - Stage changes (`git add .`)
  - Commit changes with custom messages
  - Push changes to remote repositories
  - Pull changes from remote repositories
  - View Git status
  - View commit history
- **Real-Time Terminal Output**: See the results of Git commands in a stylized terminal display
- **Responsive Design**: Works well on various screen sizes

## Requirements

- Python 3.6+
- Flask
- Git (installed and accessible from command line)
- tkinter (for native file dialog)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/lazygit.git
cd lazygit
```

2. Install the required dependencies:
```bash
pip install flask
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## How to Use

1. When you first launch the application, you'll be prompted to select a Git repository
2. Use the "Select New" button to open the native file dialog and select a Git repository
3. Once a repository is selected, you can perform Git operations using the buttons in the interface
4. The terminal output section will display the results of your Git commands
5. Toggle between dark and light modes using the icon in the top-right corner

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 