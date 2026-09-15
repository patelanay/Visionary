import numpy as np
from typing import Dict, Any, List, Tuple

class KinematicsEngine:
    """
    Real-time 3D Biomechanical Vector Math Engine.
    Uses NumPy to calculate joint spatial angles, torso lean, symmetry, 
    and biomechanical form deviations from MediaPipe 33-point 3D coordinates.
    """

    # MediaPipe Landmark Constants
    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    @staticmethod
    def _to_array(landmark: Dict[str, float]) -> np.ndarray:
        return np.array([landmark.get('x', 0.0), landmark.get('y', 0.0), landmark.get('z', 0.0)])

    @classmethod
    def calculate_angle_2d(cls, a: Dict[str, float], b: Dict[str, float], c: Dict[str, float]) -> float:
        """
        Calculates 2D interior angle at vertex b using planar arctan2.
        Drastically more accurate & stable for 2D camera feeds than noisy 3D depth arccos.
        """
        p_a = np.array([a.get('x', 0.0), a.get('y', 0.0)])
        p_b = np.array([b.get('x', 0.0), b.get('y', 0.0)])
        p_c = np.array([c.get('x', 0.0), c.get('y', 0.0)])

        radians = np.arctan2(p_c[1] - p_b[1], p_c[0] - p_b[0]) - np.arctan2(p_a[1] - p_b[1], p_a[0] - p_b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360.0 - angle
        return float(angle)

    @classmethod
    def calculate_vertical_angle(cls, top: Dict[str, float], bottom: Dict[str, float]) -> float:
        """
        Calculates angle relative to vertical Y axis (torso inclination).
        """
        p_top = cls._to_array(top)
        p_bottom = cls._to_array(bottom)
        vec = p_top - p_bottom
        vertical = np.array([0.0, -1.0, 0.0]) # Screen top is -Y in MediaPipe

        norm_vec = np.linalg.norm(vec)
        if norm_vec == 0:
            return 0.0

        cosine = np.dot(vec, vertical) / norm_vec
        cosine = np.clip(cosine, -1.0, 1.0)
        return float(np.degrees(np.arccos(cosine)))

    @classmethod
    def calculate_distance_3d(cls, a: Dict[str, float], b: Dict[str, float]) -> float:
        p_a = cls._to_array(a)
        p_b = cls._to_array(b)
        return float(np.linalg.norm(p_a - p_b))

    @classmethod
    def analyze_exercise_telemetry(cls, landmarks: List[Dict[str, float]], exercise_type: str) -> Dict[str, Any]:
        """
        Main evaluation entry point. Returns joint angles, form deviations, and warning flags.
        """
        if not landmarks or len(landmarks) < 25:
            return {"valid": False, "error": "Insufficient landmarks"}

        # Extract primary landmarks
        l_shoulder, r_shoulder = landmarks[cls.LEFT_SHOULDER], landmarks[cls.RIGHT_SHOULDER]
        l_elbow, r_elbow = landmarks[cls.LEFT_ELBOW], landmarks[cls.RIGHT_ELBOW]
        l_wrist, r_wrist = landmarks[cls.LEFT_WRIST], landmarks[cls.RIGHT_WRIST]
        l_hip, r_hip = landmarks[cls.LEFT_HIP], landmarks[cls.RIGHT_HIP]
        l_knee, r_knee = landmarks[cls.LEFT_KNEE], landmarks[cls.RIGHT_KNEE]
        l_ankle, r_ankle = landmarks[cls.LEFT_ANKLE], landmarks[cls.RIGHT_ANKLE]

        # Calculate 2D interior angles using planar arctan2 formula
        left_elbow_angle = cls.calculate_angle_2d(l_shoulder, l_elbow, l_wrist)
        right_elbow_angle = cls.calculate_angle_2d(r_shoulder, r_elbow, r_wrist)
        
        left_shoulder_angle = cls.calculate_angle_2d(l_hip, l_shoulder, l_elbow)
        right_shoulder_angle = cls.calculate_angle_2d(r_hip, r_shoulder, r_elbow)

        left_swing_angle = cls.calculate_angle_2d(l_hip, l_shoulder, l_elbow)
        right_swing_angle = cls.calculate_angle_2d(r_hip, r_shoulder, r_elbow)

        left_knee_angle = cls.calculate_angle_2d(l_hip, l_knee, l_ankle)
        right_knee_angle = cls.calculate_angle_2d(r_hip, r_knee, r_ankle)

        # Midpoint torso inclination
        mid_shoulder = {'x': (l_shoulder['x'] + r_shoulder['x']) / 2, 'y': (l_shoulder['y'] + r_shoulder['y']) / 2}
        mid_hip = {'x': (l_hip['x'] + r_hip['x']) / 2, 'y': (l_hip['y'] + r_hip['y']) / 2}
        torso_angle = cls.calculate_vertical_angle(mid_shoulder, mid_hip)

        # Determine active side (or average)
        primary_angle = left_elbow_angle
        swing_angle = left_swing_angle

        metrics = {
            "valid": True,
            "exercise": exercise_type,
            "left_elbow_angle": round(left_elbow_angle, 1),
            "right_elbow_angle": round(right_elbow_angle, 1),
            "left_shoulder_angle": round(left_shoulder_angle, 1),
            "right_shoulder_angle": round(right_shoulder_angle, 1),
            "left_knee_angle": round(left_knee_angle, 1),
            "right_knee_angle": round(right_knee_angle, 1),
            "torso_angle": round(torso_angle, 1),
            "primary_angle": round(primary_angle, 1),
            "swing_angle": round(swing_angle, 1),
            "warnings": [],
            "highlight_joints": []
        }

        ex_lower = exercise_type.lower().replace(" ", "_")

        if "bicep" in ex_lower:
            metrics["primary_angle"] = round(left_elbow_angle, 1)
            if left_swing_angle > 35:
                metrics["warnings"].append("BAD FORM: ELBOW SWINGING!")
                metrics["highlight_joints"].extend([cls.LEFT_ELBOW, cls.LEFT_SHOULDER])

        elif "tricep" in ex_lower:
            metrics["primary_angle"] = round(left_elbow_angle, 1)
            if left_swing_angle > 30:
                metrics["warnings"].append("BAD FORM: KEEP ELBOW PINNED!")
                metrics["highlight_joints"].extend([cls.LEFT_ELBOW, cls.LEFT_SHOULDER])

        elif "lat_pull" in ex_lower or "pulldown" in ex_lower:
            metrics["primary_angle"] = round(left_elbow_angle, 1)

        elif "squat" in ex_lower:
            metrics["primary_angle"] = round(left_knee_angle, 1)
            if 90 < left_knee_angle < 140:
                # Warning checked during down stage in state machine
                pass

        elif "chest" in ex_lower or "press" in ex_lower or "shoulder" in ex_lower:
            metrics["primary_angle"] = round(left_elbow_angle, 1)

        return metrics
