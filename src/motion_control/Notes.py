cv2 — The OpenCV library.
VideoCapture() —Svideo from a camera or read video from a file.
0 — The camera index, usually referring to your default webcam.
cap — A variable storing the VideoCapture object.




BaseOptions = Select Trained Pose Model Detector

PoseLandmarker Options = Configure detector to use BaseOption and RunningMode Type

PoseLandmarker = Create Detector using Options Configured

RunningMode Selects Vision Type (Photo, Video)


import cv2
import mediapipe as mp
import time

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

lean_armed = True

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

        torso_visible = all(
            point.visibility >= 0.6
            for point in [left_shoulder, right_shoulder, left_hip, right_hip]
            )

        if torso_visible:
            shoulder_width = abs(left_shoulder.x - right_shoulder.x)
            if shoulder_width > 0.01:
                lean_ratio = lean_offset / shoulder_width
                if -0.08 <= lean_ratio <= 0.08:
                    lean_armed = True
                    print("Standing Straight")

            if lean_armed:
                if lean_ratio < -0.20:
                    print("Leaning Right")
                    lean_armed = False
                elif lean_ratio > 0.20:
                    print("Leaning Left")
                    lean_armed = False

        # Draw dot on all points of body

        for landmark in result.pose_landmarks[0]:
            # Convert relative to pixel position in image
            pixel_x = int(landmark.x * width)
            pixel_y = int(landmark.y * height)
            cv2.circle(frame, (pixel_x, pixel_y), 5, (0, 255, 0), -1)





    cv2.imshow("Live Video Feed", frame)
    if cv2.waitKey(1) == ord('q'):
        print("Bai Bai!")
        break

# deselects chosen camera
camera.release()
landmarker.close()
# close all windows
cv2.destroyAllWindows()
