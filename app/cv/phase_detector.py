import time
from typing import Dict, Any

class ExercisePhaseDetector:
    """
    Biomechanical Stage State Machine & Repetition Counter.
    Uses exact thresholds from reference vision models.
    """

    def __init__(self, exercise_type: str = "bicep_curl"):
        self.set_exercise(exercise_type)

    def set_exercise(self, exercise_type: str):
        ex_clean = exercise_type.lower().replace(" ", "_")
        
        if "bicep" in ex_clean:
            self.exercise_key = "bicep_curl"
        elif "tricep" in ex_clean:
            self.exercise_key = "tricep_pushdown"
        elif "lat_pull" in ex_clean or "pulldown" in ex_clean:
            self.exercise_key = "lat_pulldown"
        elif "squat" in ex_clean:
            self.exercise_key = "squat"
        elif "chest" in ex_clean or "press" in ex_clean or "shoulder" in ex_clean:
            self.exercise_key = "chest_press"
        else:
            self.exercise_key = "bicep_curl"

        self.stage = "unknown"
        self.rep_count = 0
        self.last_phase_change = time.time()

    def process_frame(self, primary_angle: float, swing_angle: float = 0.0) -> Dict[str, Any]:
        """
        Updates stage state ('up' vs 'down') and rep count using exact reference mechanics.
        """
        now = time.time()
        rep_completed = False
        ex = self.exercise_key

        if ex == "bicep_curl":
            if primary_angle > 160:
                self.stage = "down"
            elif primary_angle < 35 and self.stage == "down":
                self.stage = "up"
                if swing_angle <= 35:
                    self.rep_count += 1
                    rep_completed = True
                    self.last_phase_change = now

        elif ex == "tricep_pushdown":
            if primary_angle < 70:
                self.stage = "up"
            elif primary_angle > 150 and self.stage == "up":
                self.stage = "down"
                if swing_angle <= 30:
                    self.rep_count += 1
                    rep_completed = True
                    self.last_phase_change = now

        elif ex == "lat_pulldown":
            if primary_angle > 150:
                self.stage = "up"
            elif primary_angle < 70 and self.stage == "up":
                self.stage = "down"
                self.rep_count += 1
                rep_completed = True
                self.last_phase_change = now

        elif ex == "squat":
            if primary_angle > 160:
                self.stage = "up"
            elif primary_angle < 90 and self.stage == "up":
                self.stage = "down"
                self.rep_count += 1
                rep_completed = True
                self.last_phase_change = now

        elif ex == "chest_press":
            if primary_angle < 70:
                self.stage = "down"
            elif primary_angle > 150 and self.stage == "down":
                self.stage = "up"
                self.rep_count += 1
                rep_completed = True
                self.last_phase_change = now

        # Fallback for initial frame
        if self.stage == "unknown":
            self.stage = "down" if primary_angle > 100 else "up"

        return {
            "exercise": self.exercise_key,
            "phase": self.stage.upper(),
            "rep_count": self.rep_count,
            "rep_completed": rep_completed,
            "primary_angle": round(primary_angle, 1)
        }
