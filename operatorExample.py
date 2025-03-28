from factorymanager import FactoryManager
import time
import base64
from openai import OpenAI

client = OpenAI()

# Create and start the container using FactoryManager
fm = FactoryManager(
    image="lscr.io/linuxserver/webtop:ubuntu-xfce",
    container_name="ubuntu-xfce",
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

with fm as fw:
    # Initial OpenAI operator request
    response = client.responses.create(
        model="computer-use-preview",
        tools=[{
            "type": "computer_use_preview",
            "display_width": 1024,
            "display_height": 768,
            "environment": "linux"  # Use "linux" to match the container's OS
        }],
        input=[
            {
                "role": "user",
                "content": "Check the latest OpenAI news on bing.com."
            }
        ],
        reasoning={
            "generate_summary": "concise",
        },
        truncation="auto"
    )

    print(response.output)

    def handle_model_action(fw, action):
        """
        Execute the computer action using FactoryManager instead of Playwright.
        """
        action_type = action.type

        try:
            match action_type:
                case "click":
                    x, y = action.x, action.y
                    button = action.button
                    print(f"Action: click at ({x}, {y}) with button '{button}'")
                    # Move the mouse to the coordinate and click.
                    fw.mouse_move([x, y])
                    fw.mouse_click(button=button)

                case "scroll":
                    # Map scroll offsets to a direction. This example checks the vertical scroll.
                    scroll_x, scroll_y = action.scroll_x, action.scroll_y
                    # Choose vertical scrolling if nonzero, else horizontal.
                    if scroll_y != 0:
                        direction = "down" if scroll_y > 0 else "up"
                        steps = abs(scroll_y)
                    elif scroll_x != 0:
                        direction = "right" if scroll_x > 0 else "left"
                        steps = abs(scroll_x)
                    else:
                        direction = "up"
                        steps = 10
                    print(f"Action: scroll {direction} by {steps} steps")
                    fw.mouse_scroll(direction=direction, steps=steps)

                case "keypress":
                    keys = action.keys
                    for k in keys:
                        print(f"Action: keypress '{k}'")
                        # Map some common keys to the expected values.
                        if k.lower() == "enter":
                            fw.keyboard_tap("Enter")
                        elif k.lower() == "space":
                            fw.keyboard_tap(" ")
                        else:
                            fw.keyboard_tap(k)

                case "type":
                    text = action.text
                    print(f"Action: type text: {text}")
                    fw.keyboard_type(text)

                case "wait":
                    print("Action: wait")
                    time.sleep(2)

                case "screenshot":
                    # No action needed; screenshot is taken after each call.
                    print("Action: screenshot")

                case _:
                    print(f"Unrecognized action: {action}")

        except Exception as e:
            print(f"Error handling action {action}: {e}")

    def get_screenshot(fw):
        """
        Capture a full-screen screenshot from the container using FactoryManager.
        """
        image_b64 = fw.screen_capture(full=True)
        return base64.b64decode(image_b64)

    def computer_use_loop(fw, response):
        """
        Loop through computer calls, execute each action, take a screenshot, and send it back.
        """
        while True:
            computer_calls = [item for item in response.output if item.type == "computer_call"]
            if not computer_calls:
                print("No computer call found. Output from model:")
                for item in response.output:
                    print(item)
                break  # Exit when no further computer calls are issued.

            # We expect at most one computer call per response.
            computer_call = computer_calls[0]
            last_call_id = computer_call.call_id
            action = computer_call.action

            # Execute the action using the FactoryManager instance.
            handle_model_action(fw, action)
            time.sleep(1)  # Allow time for changes to take effect.

            # Capture a screenshot after the action.
            screenshot_bytes = get_screenshot(fw)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            # Send the screenshot back as computer_call_output.
            response = client.responses.create(
                model="computer-use-preview",
                previous_response_id=response.id,
                tools=[{
                    "type": "computer_use_preview",
                    "display_width": 1024,
                    "display_height": 768,
                    "environment": "linux"
                }],
                input=[
                    {
                        "call_id": last_call_id,
                        "type": "computer_call_output",
                        "output": {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{screenshot_base64}"
                        }
                    }
                ],
                truncation="auto"
            )

        return response

    final_response = computer_use_loop(fw, response)


