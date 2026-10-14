import cv2
import mediapipe as mp
import time
import ctypes

# Press key + scan Code
def press_key(letter):
    windows = ctypes.windll.user32
    virtual_key = ord(letter.upper())
    scan_code = windows.MapVirtualKeyW(virtual_key, 0)

    windows.keybd_event(virtual_key, scan_code, 0, 0)
    try:
        time.sleep(0.02)
    finally:
        windows.keybd_event(virtual_key, scan_code, 2, 0)

# Set up Pose Model

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOption = mp.tasks.vision.PoseLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOption(
    base_options = BaseOptions(model_asset_path = "models/pose_landmarker_lite.task"),
    running_mode = RunningMode.VIDEO
)

landmarker = PoseLandmarker.create_from_options(options)
print("Pose detector loaded")


# Select Camera Source and Resolution

camera = cv2.VideoCapture(0)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

controls_enabled = False
lean_armed = True
jump_armed = True
crouch_armed = True

standing_hip_y = None
standing_torso_height = None

while camera.isOpened():
    received, frame,= camera.read()

    if not received:
        print("Error: Unable to receive frame")
        break

    #Convert OpenCV BGR to MediaPipe sRGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(mp.ImageFormat.SRGB, data=rgb_frame)

    # Set up timestamps for captures taken
    timestamp_ms = int(time.monotonic() * 1000)

    # Detect Pose
    result = landmarker.detect_for_video(mp_image, timestamp_ms)

    # Check Pose
    height, width, channels= frame.shape

    calibration_ready = False

    if result.pose_landmarks:

        # Draw line from left to right shoulder

        left_shoulder = result.pose_landmarks[0][11]
        right_shoulder = result.pose_landmarks[0][12]

        l_shoulder_pixel_x = int(left_shoulder.x * width)
        l_shoulder_pixel_y = int(left_shoulder.y * height)
        r_shoulder_pixel_x = int(right_shoulder.x * width)
        r_shoulder_pixel_y = int(right_shoulder.y * height)

        cv2.line(frame, (l_shoulder_pixel_x, l_shoulder_pixel_y), (r_shoulder_pixel_x, r_shoulder_pixel_y), (0, 255, 0), 2)

        left_hip = result.pose_landmarks[0][23]
        right_hip = result.pose_landmarks[0][24]

        shoulder_centre_x = (left_shoulder.x + right_shoulder.x) / 2
        hip_centre_x = (left_hip.x + right_hip.x) / 2
        lean_offset = shoulder_centre_x - hip_centre_x

        # Check confidence level of torso points
        torso_visible = all(
            point.visibility >= 0.6
            for point in [left_shoulder, right_shoulder, left_hip, right_hip]
            )

        if torso_visible:
            shoulder_width = abs(left_shoulder.x - right_shoulder.x)
            if shoulder_width > 0.01:
                lean_ratio = lean_offset / shoulder_width

                # Check if no longer leaning
                if -0.08 <= lean_ratio <= 0.08:
                    lean_armed = True
                    # print("Standing Straight")

                if lean_armed:
                    if lean_ratio < -0.20:
                        print("Leaning Right")
                        if controls_enabled:
                            print("Sending RIGHT")
                            press_key('d')
                        lean_armed = False
                    elif lean_ratio > 0.20:
                        print("Leaning Left")
                        press_key('a')
                        lean_armed = False

            # Handle Jumping

            hip_centre_y = (right_hip.y + left_hip.y) / 2
            shoulder_centre_y = (right_shoulder.y + left_shoulder.y) / 2
            torso_height =  hip_centre_y - shoulder_centre_y
            calibration_ready = torso_height > 0.01

            # Calculate upward displacement while compensating for distance from camera
            if standing_hip_y is not None and standing_torso_height is not None:
                upward_displacement = standing_hip_y - hip_centre_y
                jump_ratio = upward_displacement/standing_torso_height

                # Check if standing before re-arming Jump
                if -0.10 <= jump_ratio <= 0.10:
                    jump_armed = True
                    crouch_armed = True

                if jump_armed:
                    if jump_ratio >= 0.30:
                        print("Jump!")
                        press_key('w')
                        jump_armed = False

                # Handle Crouching
                if crouch_armed:
                    if jump_ratio < -0.15:
                        print("Crouch!")
                        press_key('s')
                        crouch_armed = False



        # Draw dot on all points of body

        for landmark in result.pose_landmarks[0]:
            # Convert relative to pixel position in image
            pixel_x = int(landmark.x * width)
            pixel_y = int(landmark.y * height)
            cv2.circle(frame, (pixel_x, pixel_y), 5, (0, 255, 0), -1)





    cv2.imshow("Live Video Feed", frame)
    key = cv2.waitKey(1)

    # Configure key pressess

    if key == ord('q'):
        print("Bai Bai!")
        break
    elif key ==ord('c'):
        print("Hip Calibration Requested")
        if calibration_ready:
            standing_hip_y = hip_centre_y
            standing_torso_height = torso_height
            print(f"Calibration Setting: \n Hip Height: {standing_hip_y} \n Torso Height: {standing_torso_height}")
        else:
            print("Make Sure Shoulders and Hips are Visible")
    elif key == ord('e'):
        controls_enabled = not controls_enabled
        print("Motion controls:", "ON" if controls_enabled else "OFF")
camera.release()
landmarker.close()
cv2.destroyAllWindows()
