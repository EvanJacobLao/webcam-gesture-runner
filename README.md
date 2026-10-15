# Webcam Gesture Runner

Play a 3D endless runner using webcam gestures: lean to change lanes, jump to jump, and crouch to slide.

A computer vision learning project by **Evan Jacob Lao**. A Python controller combines pretrained body landmarks with rule-based gesture detection and sends keyboard input to the existing Road Surfers browser game.

## Game and model references

- **Game:** [Road Surfers by durga811](https://github.com/durga811/road-surfers), built with Vite, TypeScript, and Three.js. Its source and commit history are preserved. See the [original game documentation](docs/ROAD_SURFERS.md).
- **Pose model:** Google's [MediaPipe Pose Landmarker Lite](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker), which estimates 33 body landmarks per detected person. This project uses the pretrained model; it does not train a custom neural network.
- **Model file:** `src/motion_control/models/pose_landmarker_lite.task`, included in this repository. [Official model download](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task) and [Python API guide](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python).
- **Character asset:** RobotExpressive by Tomas Laulhe, credited as CC0 in the original game README and distributed through the [Three.js examples](https://github.com/mrdoob/three.js/tree/dev/examples/models/gltf/RobotExpressive).

The controller is Evan's contribution; the original game and model are credited to their respective creators. No new license is asserted for upstream code or third-party assets.

## How it works

```text
Webcam -> OpenCV frames -> MediaPipe landmarks
       -> calibrated gesture rules -> Windows keyboard events -> game
```

Sideways lean is measured relative to shoulder width. Jump and crouch use hip displacement relative to a calibrated standing torso height. Visibility checks reject uncertain torso landmarks, and armed flags prevent repeated commands while a gesture is held.

## Requirements

- Windows (the keyboard helper uses Windows APIs).
- Python 3.13; developed with Python 3.13.2 and MediaPipe 1.1.0.
- Node.js and npm.
- Webcam with shoulders and hips visible and space to move.

## Setup and run

```powershell
git clone https://github.com/EvanJacobLao/webcam-gesture-runner.git
cd webcam-gesture-runner
```

In **terminal 1**, start the game from the repository root:

```powershell
npm install
npm run dev
```

Open the URL printed by Vite, normally http://localhost:5173/.

In **terminal 2**, starting from the repository root:

```powershell
cd src/motion_control
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe camera.py
```

Create the environment and install packages only on first setup. For later runs, use the final command from `src/motion_control`. The working directory matters because the model path is relative.

## Calibration and controls

1. Focus the camera window and stand naturally upright.
2. Press **C** to save the standing hip position and torso height. Recalibrate each run and after changing camera position or playing distance.
3. Press **E** in the camera window to enable or disable keyboard output for all four gestures.
4. Focus the browser game, start a run, and use the gestures below.
5. Return to neutral before repeating a gesture. Focus the camera window and press **Q** to quit the controller.

| Gesture | Simulated key | Action |
| --- | --- | --- |
| Lean left | A | One lane left |
| Lean right | D | One lane right |
| Jump | W | Jump |
| Crouch | S | Slide |

A Windows scan-code helper supplies the physical key information expected by the game's `KeyboardEvent.code` mapping. Earlier PyAutoGUI events arrived with an empty `code` during debugging.

## Current limitations

- Enabling controls while already holding a gesture can trigger an action immediately if its flag is armed. Stand upright before enabling. Press **E** in the camera window to disable all gesture key output, or **Q** to quit.
- Generated keys go to the focused application. The controller does not verify browser focus, and camera shortcuts require the camera window to be focused.
- Thresholds are manually tuned. Toe raises, jump preparation, landing, and tracking noise can cause false detections.
- Jump and crouch use relative hip height alone; calibration is kept in memory and assumes the player stays near the calibrated position.
- The keyboard helper currently supports Windows only.

Camera processing runs locally. The controller does not record video.

## Project layout

```text
src/motion_control/
  camera.py                       # Webcam, pose, gestures, and input
  requirements.txt                # Python dependencies
  models/pose_landmarker_lite.task # Pretrained pose model
src/input/InputManager.ts         # Original game key mapping
docs/ROAD_SURFERS.md               # Original game README and credits
```

## Learning goals

Webcam capture, pose landmarks, normalized coordinates, body-relative geometry, calibration, visibility checks, gesture debouncing, and connecting a Python controller to an existing game.
