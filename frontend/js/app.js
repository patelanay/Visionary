/**
 * Visionary Biometric Suite - Main Application Controller
 * Tab Navigation + Real-Time Vision Form Checker + Workout Set Logger
 */

document.addEventListener("DOMContentLoaded", () => {
    // Tab Navigation Switcher
    const navTabs = document.querySelectorAll(".nav-tab");
    const tabContents = document.querySelectorAll(".tab-content");

    navTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const targetTab = tab.getAttribute("data-tab");

            navTabs.forEach(t => t.classList.remove("active"));
            tabContents.forEach(c => {
                c.classList.remove("active");
                c.style.display = "none";
            });

            tab.classList.add("active");
            const activeContent = document.getElementById(targetTab);
            if (activeContent) {
                activeContent.classList.add("active");
                activeContent.style.display = "block";
            }
        });
    });

    // Form Execution Standards Database per Exercise
    const EXERCISE_GUIDES = {
        "bicep_curl": {
            name: "Bicep Curl",
            setupAngle: "90° Side Profile",
            distance: "6 - 8 Feet Away",
            alignText: "Optimal Side-Profile Angle Detected (90°)",
            rule1Title: "Elbow Position",
            rule1Desc: "Keep upper arms pinned against torso to isolate biceps.",
            rule2Title: "Range of Motion",
            rule2Desc: "Extend to >160° at bottom and flex to <35° peak contraction.",
            rule3Title: "Form Violation Warning",
            rule3Desc: "Torso swinging (>35° tilt) invalidates rep credit."
        },
        "tricep_pushdown": {
            name: "Tricep Pushdown",
            setupAngle: "90° Side Profile",
            distance: "6 - 8 Feet Away",
            alignText: "Optimal Side-Profile Angle Detected (90°)",
            rule1Title: "Elbow Stability",
            rule1Desc: "Keep elbows fixed in place; avoid shoulder movement.",
            rule2Title: "Full Lockout",
            rule2Desc: "Lock out elbows at >150° and control eccentric return to <70°.",
            rule3Title: "Form Violation Warning",
            rule3Desc: "Shoulder drift (>30° swing) signals momentum cheating."
        },
        "lat_pulldown": {
            name: "Lat Pulldown",
            setupAngle: "0° Frontal Profile",
            distance: "6 - 8 Feet Away",
            alignText: "Optimal Frontal Angle Detected (0°)",
            rule1Title: "Torso Lean",
            rule1Desc: "Maintain upright posture; avoid leaning back past 25°.",
            rule2Title: "Full Pull Range",
            rule2Desc: "Extend arms overhead (>150°) and pull bar down to chest (<70°).",
            rule3Title: "Form Violation Warning",
            rule3Desc: "Excessive backward leaning shifts load to lower back."
        },
        "squat": {
            name: "Squat (Barbell / Bodyweight)",
            setupAngle: "90° Side Profile",
            distance: "6 - 8 Feet Away",
            alignText: "Optimal Side-Profile Angle Detected (90°)",
            rule1Title: "Depth Target",
            rule1Desc: "Lower hips until thigh reaches parallel (<90° knee angle).",
            rule2Title: "Back & Spinal Neutrality",
            rule2Desc: "Maintain vertical torso posture (torso angle <30°).",
            rule3Title: "Form Violation Warning",
            rule3Desc: "Shallow depth (>140° knee angle at bottom) triggers 'GO LOWER'."
        },
        "chest_press": {
            name: "Chest Press / Overhead Press",
            setupAngle: "45° Diagonal / Frontal",
            distance: "6 - 8 Feet Away",
            alignText: "Optimal Frontal Angle Detected (0°)",
            rule1Title: "Symmetric Press Drive",
            rule1Desc: "Drive left and right arms evenly without tilting.",
            rule2Title: "Elbow Extension",
            rule2Desc: "Press arms out to full lockout (>150°) and lower to <70°.",
            rule3Title: "Form Violation Warning",
            rule3Desc: "Asymmetric arm press (>15° imbalance) triggers warning."
        },
        "shoulder_press": {
            name: "Dumbbell Shoulder Press",
            setupAngle: "0° Frontal Profile",
            distance: "6 - 8 Feet Away",
            alignText: "Optimal Frontal Angle Detected (0°)",
            rule1Title: "Overhead Lockout",
            rule1Desc: "Lock out dumbbells directly over shoulder joint at top.",
            rule2Title: "Lowering Phase",
            rule2Desc: "Lower dumbbells until elbows reach 90° shoulder height.",
            rule3Title: "Form Violation Warning",
            rule3Desc: "Arching lower back (>20° lean) signals excessive weight."
        },
        "lunge": {
            name: "Walking / Stationary Lunge",
            setupAngle: "90° Side Profile",
            distance: "6 - 8 Feet Away",
            alignText: "Optimal Side-Profile Angle Detected (90°)",
            rule1Title: "Lead Knee Alignment",
            rule1Desc: "Keep front knee aligned over ankle; avoid knee caving inward.",
            rule2Title: "Depth & Step",
            rule2Desc: "Lower rear knee toward floor until front knee reaches 90°.",
            rule3Title: "Form Violation Warning",
            rule3Desc: "Knee valgus collapse inward triggers valgus alert."
        }
    };

    // DOM Elements for Workout Hub
    const exerciseSelect = document.getElementById("exercise-select");
    const toggleCamBtn = document.getElementById("toggle-cam-btn");
    const videoElement = document.getElementById("input-video");
    const canvasElement = document.getElementById("output-canvas");
    const canvasCtx = canvasElement.getContext("2d");

    const cameraAngleReqEl = document.getElementById("camera-angle-req");
    const cameraAlignTextEl = document.getElementById("camera-align-text");
    const guideExNameEl = document.getElementById("guide-ex-name");
    const rule1TitleEl = document.getElementById("rule-1-title");
    const rule1DescEl = document.getElementById("rule-1-desc");
    const rule2TitleEl = document.getElementById("rule-2-title");
    const rule2DescEl = document.getElementById("rule-2-desc");
    const rule3TitleEl = document.getElementById("rule-3-title");
    const rule3DescEl = document.getElementById("rule-3-desc");

    const wsStatusEl = document.getElementById("ws-status");
    const latencyValEl = document.getElementById("latency-val");
    const hudPhaseEl = document.getElementById("hud-phase");
    const hudRepsEl = document.getElementById("hud-reps");
    const warningsBoxEl = document.getElementById("warnings-box");
    const liveFormScoreEl = document.getElementById("live-form-score");
    const jsonInspectorEl = document.getElementById("json-inspector");

    // Set Logger Elements
    const logWeightInput = document.getElementById("log-weight-input");
    const logTargetRepsInput = document.getElementById("log-target-reps");
    const logSetBtn = document.getElementById("log-set-btn");
    const setsHistoryList = document.getElementById("sets-history-list");

    // State Variables
    let isCameraActive = false;
    let camera = null;
    let websocket = null;
    let sessionId = "sess_" + Math.random().toString(36).substring(2, 9);
    let currentExercise = exerciseSelect.value;
    let highlightJoints = [];
    let currentRepCount = 0;
    let currentFormScore = 98;
    let loggedSets = [];

    // Initialize WebSocket Connection
    function initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/kinematics/${sessionId}`;

        wsStatusEl.innerText = "Connecting...";
        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            wsStatusEl.innerText = "CONNECTED";
            wsStatusEl.style.color = "#10b981";
        };

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleServerTelemetry(data);
        };

        websocket.onclose = () => {
            wsStatusEl.innerText = "DISCONNECTED";
            wsStatusEl.style.color = "#f43f5e";
            setTimeout(initWebSocket, 2000);
        };
    }

    function handleServerTelemetry(data) {
        if (!data.valid) return;

        const latency = data.latency_ms || 0;
        latencyValEl.innerText = `${latency} ms`;

        hudPhaseEl.innerText = `STAGE: ${data.phase || 'DOWN'}`;
        hudRepsEl.innerText = `REPS: ${data.rep_count || 0}`;
        currentRepCount = data.rep_count || 0;
        highlightJoints = data.highlight_joints || [];

        const warnings = data.warnings || [];
        if (warnings.length > 0) {
            currentFormScore = Math.max(70, currentFormScore - 2);
            warningsBoxEl.classList.add("has-warning");
            warningsBoxEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Warning: ${warnings.join(", ")}`;
        } else {
            currentFormScore = Math.min(99, currentFormScore + 1);
            warningsBoxEl.classList.remove("has-warning");
            warningsBoxEl.innerHTML = `<i class="fa-solid fa-shield-halved"></i> Biomechanical Form: Optimal Alignment`;
        }

        liveFormScoreEl.innerText = `${currentFormScore}%`;
        jsonInspectorEl.innerText = JSON.stringify(data, null, 2);
    }

    // MediaPipe Pose Setup
    let pose = null;
    if (window.Pose) {
        pose = new Pose({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
        });

        pose.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        pose.onResults(onPoseResults);
    }

    function onPoseResults(results) {
        canvasCtx.save();
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
        if (results.image) {
            canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);
        }

        if (results.poseLandmarks) {
            drawSkeleton(results.poseLandmarks);

            if (websocket && websocket.readyState === WebSocket.OPEN) {
                const landmarkData = results.poseLandmarks.map(lm => ({
                    x: lm.x,
                    y: lm.y,
                    z: lm.z,
                    visibility: lm.visibility
                }));

                websocket.send(JSON.stringify({
                    exercise: currentExercise,
                    landmarks: landmarkData
                }));
            }
        }
        canvasCtx.restore();
    }

    function drawSkeleton(landmarks) {
        const connections = [
            [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
            [11, 23], [12, 24], [23, 24], [23, 25], [24, 26], [25, 27], [26, 28]
        ];

        canvasCtx.lineWidth = 4;
        connections.forEach(([i, j]) => {
            const p1 = landmarks[i];
            const p2 = landmarks[j];
            if (p1 && p2 && p1.visibility > 0.4 && p2.visibility > 0.4) {
                const isWarning = highlightJoints.includes(i) || highlightJoints.includes(j);
                canvasCtx.strokeStyle = isWarning ? "#f43f5e" : "#10b981";
                canvasCtx.beginPath();
                canvasCtx.moveTo(p1.x * canvasElement.width, p1.y * canvasElement.height);
                canvasCtx.lineTo(p2.x * canvasElement.width, p2.y * canvasElement.height);
                canvasCtx.stroke();
            }
        });

        landmarks.forEach((lm, index) => {
            if (lm.visibility > 0.4 && index <= 28) {
                const isHighlight = highlightJoints.includes(index);
                canvasCtx.fillStyle = isHighlight ? "#f43f5e" : "#06b6d4";
                canvasCtx.beginPath();
                canvasCtx.arc(lm.x * canvasElement.width, lm.y * canvasElement.height, isHighlight ? 8 : 5, 0, 2 * Math.PI);
                canvasCtx.fill();
            }
        });
    }

    function updateExerciseGuide(exKey) {
        const guide = EXERCISE_GUIDES[exKey] || EXERCISE_GUIDES["bicep_curl"];
        cameraAngleReqEl.innerText = guide.setupAngle;
        cameraAlignTextEl.innerText = guide.alignText;
        guideExNameEl.innerText = guide.name;
        rule1TitleEl.innerText = guide.rule1Title;
        rule1DescEl.innerText = guide.rule1Desc;
        rule2TitleEl.innerText = guide.rule2Title;
        rule2DescEl.innerText = guide.rule2Desc;
        rule3TitleEl.innerText = guide.rule3Title;
        rule3DescEl.innerText = guide.rule3Desc;
    }

    // Toggle Camera
    toggleCamBtn.addEventListener("click", () => {
        if (!isCameraActive) {
            if (window.Camera && pose) {
                camera = new Camera(videoElement, {
                    onFrame: async () => {
                        await pose.send({ image: videoElement });
                    },
                    width: 640,
                    height: 480
                });
                camera.start();
                isCameraActive = true;
                toggleCamBtn.innerHTML = `<i class="fa-solid fa-video-slash"></i> Stop Camera`;
            } else {
                alert("Webcam camera API not supported in current browser environment.");
            }
        } else {
            if (camera) camera.stop();
            isCameraActive = false;
            toggleCamBtn.innerHTML = `<i class="fa-solid fa-video"></i> Start Camera`;
        }
    });

    exerciseSelect.addEventListener("change", (e) => {
        currentExercise = e.target.value;
        updateExerciseGuide(currentExercise);
    });

    // Active Set Logger
    logSetBtn.addEventListener("click", () => {
        const weight = logWeightInput.value || "0";
        const reps = currentRepCount > 0 ? currentRepCount : (logTargetRepsInput.value || "10");
        const setNum = loggedSets.length + 1;
        const exName = EXERCISE_GUIDES[currentExercise]?.name || currentExercise;

        const setRecord = {
            setNum,
            exName,
            weight,
            reps,
            score: currentFormScore
        };

        loggedSets.push(setRecord);
        renderLoggedSets();
    });

    function renderLoggedSets() {
        if (loggedSets.length === 0) {
            setsHistoryList.innerHTML = `<li class="empty-list-text">No sets logged yet. Perform exercise and click 'Log Completed Set'.</li>`;
            return;
        }

        setsHistoryList.innerHTML = loggedSets.map(s => `
            <li class="set-item-row">
                <span>Set #${s.setNum}: <strong>${s.exName}</strong></span>
                <span>${s.weight} lbs × ${s.reps} reps (Form: <strong style="color: var(--accent-emerald);">${s.score}%</strong>)</span>
            </li>
        `).join("");
    }

    // Settings API Key Saver
    const settingsSaveBtn = document.getElementById("settings-save-btn");
    const settingsStatusAlert = document.getElementById("settings-status-alert");

    if (settingsSaveBtn) {
        settingsSaveBtn.addEventListener("click", async () => {
            const geminiKey = document.getElementById("settings-gemini-key").value.trim();
            const openaiKey = document.getElementById("settings-openai-key").value.trim();
            const usdaKey = document.getElementById("settings-usda-key").value.trim();
            const mongoUri = document.getElementById("settings-mongo-uri").value.trim();

            settingsSaveBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Verifying Keys...`;

            try {
                const res = await fetch("/api/settings/keys", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        openai_api_key: openaiKey,
                        usda_api_key: usdaKey,
                        mongodb_uri: mongoUri
                    })
                });

                const data = await res.json();
                settingsSaveBtn.innerHTML = `<i class="fa-solid fa-circle-check"></i> Save & Test API Connections`;
                settingsStatusAlert.style.display = "block";
                settingsStatusAlert.className = "status-alert";
                settingsStatusAlert.innerText = "API Keys and Database connections saved successfully!";
            } catch (err) {
                settingsSaveBtn.innerHTML = `<i class="fa-solid fa-circle-check"></i> Save & Test API Connections`;
                settingsStatusAlert.style.display = "block";
                settingsStatusAlert.className = "status-alert error";
                settingsStatusAlert.innerText = "Error testing API connections.";
            }
        });
    }

    // Initialize Page
    updateExerciseGuide(currentExercise);
    initWebSocket();
});
