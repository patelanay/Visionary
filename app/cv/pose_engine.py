import time
import numpy as np
from typing import Dict, Any, List, Optional
from app.cv.kinematics import KinematicsEngine
from app.cv.phase_detector import ExercisePhaseDetector

# Attempt MediaPipe import with fallback if running on headless server without GPU
try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False

class PoseEngine:
    """
    Sub-30ms Kinematic Analysis Engine.
    Processes 33-point 3D spatial landmarks from MediaPipe Pose.
    Calculates angle trigonometry via NumPy and runs movement phase classification.
    """

    def __init__(self, default_exercise: str = "bicep_curl"):
        self.kinematics = KinematicsEngine()
        self.phase_detector = ExercisePhaseDetector(default_exercise)
        self.current_exercise = default_exercise

        if MP_AVAILABLE and hasattr(mp, 'solutions') and hasattr(mp.solutions, 'pose'):
            self.mp_pose = mp.solutions.pose
            self.pose_detector = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1, # 0 = fast, 1 = balanced, 2 = precise
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        else:
            self.mp_pose = None
            self.pose_detector = None

    def set_exercise(self, exercise_name: str):
        self.current_exercise = exercise_name
        self.phase_detector.set_exercise(exercise_name)

    def process_landmarks(self, landmarks_list: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Process pre-extracted 33-point spatial landmark array (sent from client camera JS or backend).
        Executes sub-30ms kinematic vector math and state detection.
        """
        start_time = time.time()

        # Step 1: Evaluate biomechanics via Kinematics Engine
        telemetry = self.kinematics.analyze_exercise_telemetry(landmarks_list, self.current_exercise)
        
        if not telemetry.get("valid", False):
            return {
                "valid": False,
                "error": telemetry.get("error", "Invalid landmarks"),
                "latency_ms": round((time.time() - start_time) * 1000, 2)
            }

        # Step 2: Feed primary angle and swing angle into Phase & Rep Detector
        primary_angle = telemetry["primary_angle"]
        swing_angle = telemetry.get("swing_angle", 0.0)
        phase_data = self.phase_detector.process_frame(primary_angle, swing_angle)

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "valid": True,
            "exercise": self.current_exercise,
            "latency_ms": latency_ms,
            "telemetry": telemetry,
            "phase": phase_data["phase"],
            "rep_count": phase_data["rep_count"],
            "rep_completed": phase_data["rep_completed"],
            "warnings": telemetry["warnings"],
            "highlight_joints": telemetry["highlight_joints"],
            "timestamp": time.time()
        }
