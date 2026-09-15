import pytest
from app.cv.kinematics import KinematicsEngine
from app.cv.phase_detector import ExercisePhaseDetector

def test_2d_angle_calculation_right_angle():
    a = {'x': 1.0, 'y': 0.0}
    b = {'x': 0.0, 'y': 0.0}
    c = {'x': 0.0, 'y': 1.0}

    angle = KinematicsEngine.calculate_angle_2d(a, b, c)
    assert abs(angle - 90.0) < 0.01

def test_bicep_curl_stage_transitions():
    detector = ExercisePhaseDetector("bicep_curl")
    
    # 1. Starting position: arm fully extended (> 160 deg) -> Stage 'DOWN'
    res = detector.process_frame(165.0, swing_angle=10.0)
    assert res["phase"] == "DOWN"
    assert res["rep_count"] == 0

    # 2. Curl position: arm contracted (< 35 deg) while stage was 'DOWN' -> Stage 'UP' & Rep +1!
    res = detector.process_frame(30.0, swing_angle=10.0)
    assert res["phase"] == "UP"
    assert res["rep_count"] == 1
    assert res["rep_completed"] is True

def test_bicep_curl_bad_form_no_rep():
    detector = ExercisePhaseDetector("bicep_curl")
    detector.process_frame(165.0, swing_angle=10.0)

    # Excessive elbow swing (> 35 deg) should prevent rep increment
    res = detector.process_frame(30.0, swing_angle=45.0)
    assert res["rep_completed"] is False
