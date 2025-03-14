import docker
import time
from docker.errors import NotFound
from typing import Optional, Dict, List, Union, Any
import docker
import time

class FactoryManager:
    def __init__(
        self,
        image: str,
        container_name: str,
        ports: Dict[str, int],
        environment: Dict[str, str],
        volumes: Dict[str, Dict[str, Any]],
        security_opt: Optional[List[str]] = None,
        devices: Optional[List[Dict[str, str]]] = None,
        shm_size: Optional[str] = None,
        restart_policy: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the framework with Docker container configuration.

        :param image: Docker image to run.
        :param container_name: Name for the container.
        :param ports: Port mappings (e.g., {'3000/tcp': 3000, '3001/tcp': 3001}).
        :param environment: Environment variables to set inside the container.
        :param volumes: Volume bindings in the form {host_path: {'bind': container_path, 'mode': 'rw'}}.
        :param security_opt: List of security options (e.g., ["seccomp:unconfined"]).
        :param devices: List of device mappings, e.g., [{"PathOnHost": "/dev/dri", "PathInContainer": "/dev/dri", "CgroupPermissions": "rwm"}].
        :param shm_size: Shared memory size (e.g., "1gb").
        :param restart_policy: Restart policy dictionary (e.g., {"Name": "unless-stopped"}).
        """
        self.image = image
        self.container_name = container_name
        self.ports = ports
        self.environment = environment
        self.volumes = volumes
        self.security_opt = security_opt or []
        self.devices = devices or []
        self.shm_size = shm_size
        self.restart_policy = restart_policy or {"Name": "unless-stopped"}
        self.client = docker.from_env()
        self.container = None

        # Path to the robotgo-cli binary inside the container.
        self.robotgo_cli_path = "/usr/local/bin/robotgo-cli"

    def install_robotgo_cli_in_container(self):
        """
        Download and install the pre-built robotgo-cli binary inside the container.
        """
        check_cmd = f"ls {self.robotgo_cli_path}"
        exec_result = self.container.exec_run(check_cmd)
        if exec_result.exit_code == 0:
            print("robotgo-cli binary already exists inside the container. Skipping download.")
            return

        release_url = "https://github.com/sampagon/robotgo-cli/releases/latest/download/robotgo-cli"
        print("Downloading robotgo-cli binary inside the container...")

        curl_cmd = f"curl -L -o {self.robotgo_cli_path} {release_url}"
        exec_result = self.container.exec_run(curl_cmd)
        if exec_result.exit_code != 0:
            error_msg = exec_result.output.decode('utf-8')
            raise Exception(f"Failed to download robotgo-cli in container: {error_msg}")

        chmod_cmd = f"chmod +x {self.robotgo_cli_path}"
        exec_result = self.container.exec_run(chmod_cmd)
        if exec_result.exit_code != 0:
            error_msg = exec_result.output.decode('utf-8')
            raise Exception(f"Failed to chmod robotgo-cli in container: {error_msg}")

        print("robotgo-cli installed inside the container.")

    def start(self):
        """
        Start or attach to the container:
          - If the container exists, attach to it.
          - Otherwise, create and run a new container using the provided configuration.
        If an error occurs during startup, the container is stopped.
        """
        try:
            try:
                self.container = self.client.containers.get(self.container_name)
                print(f"Attached to existing container '{self.container_name}'.")
            except NotFound:
                print(f"Container '{self.container_name}' not found. Creating a new one...")
                self.container = self.client.containers.run(
                    image=self.image,
                    name=self.container_name,
                    detach=True,
                    ports=self.ports,
                    environment=self.environment,
                    volumes=self.volumes,
                    security_opt=self.security_opt,
                    devices=self.devices,
                    shm_size=self.shm_size,
                    restart_policy=self.restart_policy
                )
                print(f"Container '{self.container_name}' started with ID: {self.container.id}")

            self.container.reload()
            if self.container.status != "running":
                print(f"Container '{self.container_name}' is not running (status: {self.container.status}). Starting it...")
                self.container.start()
                time.sleep(2)
                self.container.reload()
                if self.container.status != "running":
                    raise Exception(f"Container '{self.container_name}' failed to start (status: {self.container.status}).")

            self.install_robotgo_cli_in_container()
        except Exception as e:
            print(f"Error during startup: {e}")
            self.stop()
            raise

    def stop(self):
        """
        Stop the container.
        """
        if self.container:
            try:
                self.container.stop()
                print(f"Container '{self.container_name}' with ID {self.container.id} has been stopped.")
            except Exception as e:
                print(f"Error while stopping container: {e}")
        else:
            print("No container to stop.")

    def __command(self, command_args: List[str]) -> str:
        """
        Execute a robotgo-cli command inside the container.
        
        :param command_args: List of command-line arguments.
        :return: Standard output as a string.
        :raises Exception: If the command fails.
        """
        cmd = [self.robotgo_cli_path] + command_args
        #print("Running command in container:", " ".join(cmd))
        exec_result = self.container.exec_run(cmd)
        if exec_result.exit_code != 0:
            error_msg = exec_result.output.decode('utf-8')
            raise Exception(f"Command '{' '.join(cmd)}' failed with error: {error_msg}")
        return exec_result.output.decode('utf-8').strip()

    # --- Mouse Commands ---
    def mouse_move(self, coordinate: List[Union[int, float]]) -> str:
        """
        Move the mouse to the given coordinate [x, y].
        
        :param coordinate: List of two numbers.
        :raises ValueError: If input is invalid.
        """
        if not (isinstance(coordinate, list) and len(coordinate) == 2 and all(isinstance(n, (int, float)) for n in coordinate)):
            raise ValueError("coordinate must be a list of two numbers")
        x, y = coordinate
        return self.__command(["mouse", "move", "--x", str(x), "--y", str(y)])

    def mouse_click(self, button: str = "left", double: bool = False) -> str:
        """
        Click a mouse button.
        
        :param button: Button name (e.g., left, right, middle, wheelLeft, wheelRight).
        :param double: True for a double click.
        """
        if button not in ["left", "right", "middle", "wheelLeft", "wheelRight"]:
            raise ValueError("Invalid mouse button. Choose from left, right, middle, wheelLeft, wheelRight.")
        args = ["mouse", "click", "--button", button]
        if double:
            args += ["--double", "true"]
        return self.__command(args)

    def mouse_scroll(self, direction: str = "up", steps: int = 10) -> str:
        """
        Scroll the mouse in a given direction.
        
        :param direction: One of "up", "down", "left", "right".
        :param steps: Number of scroll steps.
        """
        if direction not in ["up", "down", "left", "right"]:
            raise ValueError("direction must be one of up, down, left, right")
        if not isinstance(steps, int) or steps < 1:
            raise ValueError("steps must be a positive integer")
        return self.__command(["mouse", "scroll", "--direction", direction, "--steps", str(steps)])

    def mouse_toggle(self, button: str = "left", state: str = "down") -> str:
        """
        Toggle the state of a mouse button.
        
        :param button: The mouse button (e.g., left).
        :param state: "down" or "up".
        """
        if state not in ["down", "up"]:
            raise ValueError("state must be either 'down' or 'up'")
        return self.__command(["mouse", "toggle", "--button", button, "--state", state])

    # --- Keyboard Commands ---
    def keyboard_type(self, text: str) -> str:
        """
        Type a string using the keyboard.
        
        :param text: A non-empty string.
        :raises ValueError: If text is invalid.
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        return self.__command(["keyboard", "type", "--text", text])

    def keyboard_tap(self, key: str, mods: Optional[List[str]] = None) -> str:
        """
        Tap a key with optional modifiers.
        
        :param key: The key to tap.
        :param mods: Optional list of modifier keys (e.g., ["ctrl", "shift"]).
        :raises ValueError: If key is invalid.
        """
        if not isinstance(key, str) or not key.strip():
            raise ValueError("key must be a non-empty string")
        args = ["keyboard", "tap", "--key", key]
        if mods:
            if not all(isinstance(mod, str) and mod.strip() for mod in mods):
                raise ValueError("mods must be a list of non-empty strings")
            args += ["--mods", ",".join(mods)]
        return self.__command(args)

    def keyboard_toggle(self, key: str, state: str = "down") -> str:
        """
        Toggle a key state (down/up).
        
        :param key: The key to toggle.
        :param state: "down" or "up".
        """
        if state not in ["down", "up"]:
            raise ValueError("state must be either 'down' or 'up'")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("key must be a non-empty string")
        return self.__command(["keyboard", "toggle", "--key", key, "--state", state])

    # --- Screen Commands ---
    def screen_capture(self,
                       x: int = 0,
                       y: int = 0,
                       width: int = 100,
                       height: int = 100,
                       full: bool = False) -> str:
        """
        Capture a portion of the screen and save to a file.
        If full is True, the capture uses full screen dimensions.
        """
        for val, name in zip([x, y, width, height], ["x", "y", "width", "height"]):
            if not isinstance(val, int) or val < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if full:
            return self.__command(["screen", "capture", "--full"])
        else:
            return self.__command(["screen", "capture", "--x", str(x), "--y", str(y),
                                    "--width", str(width), "--height", str(height)])

    def screen_getpixel(self, x: int, y: int) -> str:
        """
        Get the color of the pixel at the specified coordinates.
        """
        if not (isinstance(x, int) and isinstance(y, int) and x >= 0 and y >= 0):
            raise ValueError("x and y must be non-negative integers")
        return self.__command(["screen", "getpixel", "--x", str(x), "--y", str(y)])

    def screen_size(self) -> str:
        """
        Get the screen size.
        """
        return self.__command(["screen", "size"])

    # --- Window Commands ---
    def window_activate(self, name: Optional[str] = None, pid: Optional[int] = None) -> str:
        """
        Activate a window by name or process ID.
        At least one of name or pid must be provided.
        """
        if name:
            return self.__command(["window", "activate", "--name", name])
        elif pid and isinstance(pid, int):
            return self.__command(["window", "activate", "--pid", str(pid)])
        else:
            raise ValueError("Please provide either a window name or a valid pid.")

    def window_kill(self, pid: int) -> str:
        """
        Kill a process by PID.
        """
        if not isinstance(pid, int) or pid <= 0:
            raise ValueError("pid must be a positive integer")
        return self.__command(["window", "kill", "--pid", str(pid)])

    def window_title(self) -> str:
        """
        Get the title of the active window.
        """
        return self.__command(["window", "title"])

    # --- Clipboard Commands ---
    def clipboard_read(self) -> str:
        """
        Read text from the clipboard.
        """
        return self.__command(["clipboard", "read"])

    def clipboard_write(self, text: str) -> str:
        """
        Write text to the clipboard.
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")
        return self.__command(["clipboard", "write", "--text", text])

    # --- Process Commands ---
    def process_list(self) -> str:
        """
        List processes (PID and Name).
        """
        return self.__command(["process", "list"])
    
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
