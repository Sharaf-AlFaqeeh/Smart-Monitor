def camera_on(command):
    if command == "camera on":
        return 1  # turn on the camera
    return 0  # turn on the camera

def camera_off(command):
    if command == "camera off":
        return 1  # turn off the camera
    return 0  # turn off the camera

def buzzer_on(command):
    if command == "buzzer on":
        return 1  # turn on the buzzer
    return 0  # turn on the buzzer

def buzzer_beep(command):
    if command == "buzzer beep":
        return 1  # turn on the buzzer
    return 0  # turn on the buzzer three times

def buzzer_off(command):
    if command == "buzzer off":
        return 1  # turn off the buzzer
    return 0  # stop the buzzer
# ________________________
def camera_right(command):
    if command == "camera right":
        return 1  # move the camera to the right
    return 0  # move the camera to the right

def camera_left(command):
    if command == "camera left":
        return 1  # move the camera to the left
    return 0  # move the camera to the left

def camera_up(command):
    if command == "camera up":
        return 1  # move the camera up
    return 0  # move the camera up

def camera_down(command):
    if command == "camera down":
        return 1  # move the camera down
    return 0  # move the camera down