# FactoryManager

FactoryManager is a Python class that simplifies managing a Docker container running a desktop environment. It provides methods to control mouse and keyboard actions, take screenshots, and interact with the container's screen, clipboard, and windows via a pre-installed robotgo-cli binary.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Initializing and Starting a Container](#initializing-and-starting-a-container)
  - [Controlling the Desktop Environment](#controlling-the-desktop-environment)
  - [Exiting and Stopping the Container](#exiting-and-stopping-the-container)
- [API Reference](#api-reference)
  - [Mouse Commands](#mouse-commands)
  - [Keyboard Commands](#keyboard-commands)
  - [Screen Commands](#screen-commands)
  - [Window Commands](#window-commands)
  - [Clipboard Commands](#clipboard-commands)
  - [Process Commands](#process-commands)
- [Error Handling](#error-handling)
- [License](#license)

## Features

### Container Management
- Start, attach to, and stop Docker containers with a custom configuration.

### Desktop Interaction
- Send mouse movements, clicks, scrolls, and keyboard actions directly to the container.

### Screen Operations
- Capture full or partial screenshots, retrieve pixel colors, and get screen dimensions.

### Window and Clipboard Controls
- Activate windows, kill processes, read/write clipboard data, and more.

### Process Management
- List processes running inside the container.

## Requirements
- Python 3.6 or higher
- Docker Engine and the Docker Python SDK
- Internet access for downloading the robotgo-cli binary inside the container

Install the Docker Python SDK via pip:
```bash
pip install docker
```

## Installation

### Clone the Repository
```bash
git clone https://github.com/your-username/factory-manager.git
cd factory-manager
```

### Install Dependencies
Make sure you have Docker installed and running. Then, install the required Python packages:
```bash
pip install docker
```

### Configuration
Adjust your container settings (e.g., image, ports, environment variables, volumes) in your code as needed.

## Usage

### Initializing and Starting a Container
Below is an example of how to initialize and start a container with FactoryManager:

```python
from factorymanager import FactoryManager
import time

# Configure container parameters
fm = FactoryManager(
    image="lscr.io/linuxserver/webtop:debian-kde",
    container_name="debian-kde",
    ports={"3000/tcp": 3000, "3001/tcp": 3001},
    environment={
        "PUID": "1000",
        "PGID": "1000",
        "TZ": "Etc/UTC",
    },
    volumes={"/path/to/config": {"bind": "/config", "mode": "rw"}},
    security_opt=["seccomp:unconfined"],
    devices=[{"PathOnHost": "/dev/dri", "PathInContainer": "/dev/dri", "CgroupPermissions": "rwm"}],
    shm_size="1gb",
    restart_policy={"Name": "unless-stopped"}
)

# Using the FactoryManager in a context manager
with fm as fw:
    print("Container is running and robotgo-cli is installed.")
    # Your code to interact with the container goes here...
    time.sleep(60)
```

### Controlling the Desktop Environment
FactoryManager exposes various methods to simulate user interactions:

```python
# Move mouse to coordinates (100, 200)
fw.mouse_move([100, 200])

# Left-click the mouse
fw.mouse_click(button="left")

# Type a text string
fw.keyboard_type("Hello, FactoryManager!")
```

### Exiting and Stopping the Container
When used as a context manager, FactoryManager automatically stops the container upon exit. Alternatively, you can manually stop the container:

```python
# Stop the container manually if not using a context manager
fm.stop()
```

## API Reference

### Mouse Commands
- `mouse_move(coordinate: List[Union[int, float]]) -> str`
  - Moves the mouse pointer to the specified coordinate [x, y].

- `mouse_click(button: str = "left", double: bool = False) -> str`
  - Simulates a mouse click. Use the double flag for a double-click.

- `mouse_scroll(direction: str = "up", steps: int = 10) -> str`
  - Scrolls the mouse in the given direction ("up", "down", "left", or "right") by a number of steps.

- `mouse_toggle(button: str = "left", state: str = "down") -> str`
  - Toggles the mouse button state (e.g., press down or release).

### Keyboard Commands
- `keyboard_type(text: str) -> str`
  - Types a string using the container's keyboard input.

- `keyboard_tap(key: str, mods: Optional[List[str]] = None) -> str`
  - Taps a specific key with optional modifiers (e.g., ["ctrl", "shift"]).

- `keyboard_toggle(key: str, state: str = "down") -> str`
  - Toggles a key's state between pressed and released.

### Screen Commands
- `screen_capture(x: int = 0, y: int = 0, width: int = 100, height: int = 100, full: bool = False) -> str`
  - Captures a portion of the screen or the full screen if full is True. Returns a base64-encoded image string.

- `screen_getpixel(x: int, y: int) -> str`
  - Retrieves the color of the pixel at the specified coordinates.

- `screen_size() -> str`
  - Returns the screen dimensions.

### Window Commands
- `window_activate(name: Optional[str] = None, pid: Optional[int] = None) -> str`
  - Activates a window by name or process ID.

- `window_kill(pid: int) -> str`
  - Terminates a window/process using its PID.

- `window_title() -> str`
  - Retrieves the title of the currently active window.

### Clipboard Commands
- `clipboard_read() -> str`
  - Reads text from the container's clipboard.

- `clipboard_write(text: str) -> str`
  - Writes text to the clipboard.

### Process Commands
- `process_list() -> str`
  - Lists the processes running in the container (includes PID and process names).

## Error Handling
Methods will raise exceptions if:
- A command executed inside the container fails.
- Input validation (such as coordinates, key values, or button names) does not pass.
- During startup, if any error occurs (for example, if the container fails to start), the container is stopped and the error is raised.
