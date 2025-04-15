# Lazy Git - Modern Git GUI

A sleek, modern Git GUI application built with Tkinter and ttkbootstrap, featuring glassmorphism effects and modern UI/UX principles.

## Features

### Modern UI/UX Design
- **Glassmorphism Effects**: Semi-transparent, frosted glass-like panels with blur effects
- **Light/Dark Mode**: Toggle between light and dark themes with a single click
- **Interactive Elements**: Hover animations, button press effects, and smooth transitions
- **Custom Widgets**: Beautifully styled buttons, input fields, and panels

### Git Functionality
- Repository directory selection
- Basic Git operations (add, commit, push, pull)
- Git status and log viewing
- Real-time command output display

### Advanced Effects
- Loading animations with progress bars
- Smooth transitions and fade effects
- Status bar with real-time updates
- Placeholder text for input fields

## Requirements
- Python 3.x
- ttkbootstrap (`pip install ttkbootstrap`)
- Pillow (`pip install pillow`)

## Usage
```bash
python "git GUI-V1.py"
```

## Screenshot
(Screenshots will appear here once available)

## Implementation Details

### Glassmorphism Effect
The glassmorphism effect is achieved using the PIL library to create blurred backgrounds with semi-transparency. Each glassmorphic panel uses a custom frame class that:
1. Creates a canvas as background
2. Generates a semi-transparent background image
3. Applies a Gaussian blur filter
4. Updates dynamically when resized or theme changes

### Interactive Elements
Buttons feature:
- Scale animations on hover
- Color changes based on theme
- Press/release animations
- Custom styling for different action types

### Threading for Performance
Git commands run in separate threads to:
- Prevent UI freezing during operations
- Allow for loading animations
- Update UI elements after completion

### Theme System
The application supports both light and dark themes:
- Uses ttkbootstrap themes ("darkly" and "flatly")
- Adapts glassmorphism effects to match theme
- Saves preferences across sessions

## License
MIT License

## Author

SAI SUMANTH

```xml

```
