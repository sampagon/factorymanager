from factorymanager import FactoryManager
import time
import base64

container_name = "chromium"
image = "lscr.io/linuxserver/chromium:latest"
ports = {"3000/tcp": 3000, "3001/tcp": 3001}
environment = {
    "PUID": "1000",
    "PGID": "1000",
    "TZ": "Etc/UTC",
    "CHROME_CLI": "https://nike.com/"
}
volumes = {"/path/to/config": {"bind": "/config", "mode": "rw"}}
security_opt = ["seccomp:unconfined"]
devices = [
    {"PathOnHost": "/dev/dri", "PathInContainer": "/dev/dri", "CgroupPermissions": "rwm"}
]
shm_size = "1gb"
restart_policy = {"Name": "unless-stopped"}

try:
    with FactoryManager(
        image=image,
        container_name=container_name,
        ports=ports,
        environment=environment,
        volumes=volumes,
        security_opt=security_opt,
        devices=devices,
        shm_size=shm_size,
        restart_policy=restart_policy
    ) as fw:
        # Example command that might cause an error.
        time.sleep(10)
        image = fw.screen_capture(full=True)
        decoded_image = base64.b64decode(image)

        # Save the decoded image data to a PNG file
        with open("screenshot.png", "wb") as f:
            f.write(decoded_image)

except Exception as e:
    print(f"An error occurred: {e}")