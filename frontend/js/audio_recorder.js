/**
 * Visionary Multimodal Audio & Diet Ingestion Controller
 * Daily Macro Targets Progress Bar + Voice Speech Logger + Meal Table
 */

document.addEventListener("DOMContentLoaded", () => {
    const recordBtn = document.getElementById("record-audio-btn");
    const textMealBtn = document.getElementById("text-meal-btn");
    const commitMealBtn = document.getElementById("commit-meal-btn");
    
    const audioStatusTag = document.getElementById("nlp-status-tag");
    const transcriptTextEl = document.getElementById("transcript-text");
    const pydanticJsonEl = document.getElementById("pydantic-json-output");

    const macroCalsEl = document.getElementById("macro-cals");
    const macroProtEl = document.getElementById("macro-prot");
    const macroCarbsEl = document.getElementById("macro-carbs");
    const macroFatsEl = document.getElementById("macro-fats");

    // Daily Macro Dashboard Elements
    const dashCalsText = document.getElementById("dash-cals-text");
    const dashCalsBar = document.getElementById("dash-cals-bar");
    const dashProtText = document.getElementById("dash-prot-text");
    const dashProtBar = document.getElementById("dash-prot-bar");
    const dashCarbsText = document.getElementById("dash-carbs-text");
    const dashCarbsBar = document.getElementById("dash-carbs-bar");
    const dashFatsText = document.getElementById("dash-fats-text");
    const dashFatsBar = document.getElementById("dash-fats-bar");

    const foodLogTbody = document.getElementById("food-log-tbody");
    const foodLogCountEl = document.getElementById("food-log-count");

    // Daily Macro Targets & Totals State
    const GOALS = { calories: 2500, protein: 180, carbs: 250, fats: 70 };
    let currentTotals = { calories: 0, protein: 0, carbs: 0, fats: 0 };
    let currentParsedPayload = null;
    let loggedMeals = [];

    let isRecording = false;
    let recognition = null;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            isRecording = true;
            recordBtn.classList.add("recording");
            recordBtn.innerHTML = `<i class="fa-solid fa-square"></i> Listening...`;
            audioStatusTag.innerText = "Status: Listening";
            audioStatusTag.className = "badge-tag warning";
        };

        recognition.onresult = (event) => {
            let text = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                text += event.results[i][0].transcript;
            }
            transcriptTextEl.innerText = `"${text}"`;
        };

        recognition.onend = async () => {
            isRecording = false;
            recordBtn.classList.remove("recording");
            recordBtn.innerHTML = `<i class="fa-solid fa-microphone"></i> Record Meal Speech`;
            audioStatusTag.innerText = "Status: Parsing";
            audioStatusTag.className = "badge-tag";

            const finalSpeech = transcriptTextEl.innerText.replace(/^"|"$/g, '').trim();
            if (finalSpeech && finalSpeech.length > 2) {
                await processMealText(finalSpeech);
            }
        };

        recognition.onerror = () => {
            isRecording = false;
            recordBtn.classList.remove("recording");
            recordBtn.innerHTML = `<i class="fa-solid fa-microphone"></i> Record Meal Speech`;
            audioStatusTag.innerText = "Status: Idle";
            audioStatusTag.className = "badge-tag";
        };
    }

    if (recordBtn) {
        recordBtn.addEventListener("click", () => {
            if (recognition) {
                if (!isRecording) {
                    transcriptTextEl.innerText = "Listening...";
                    recognition.start();
                } else {
                    recognition.stop();
                }
            } else {
                const userText = prompt("Your browser doesn't support Web Speech API. Type what you ate:");
                if (userText) processMealText(userText);
            }
        });
    }

    if (textMealBtn) {
        textMealBtn.addEventListener("click", () => {
            const input = prompt("Enter meal text (e.g. '2 grilled chicken breasts, 1 cup quinoa, half avocado'):", "2 grilled chicken breasts, 1 cup quinoa, half avocado");
            if (input) processMealText(input);
        });
    }

    async function processMealText(mealText) {
        audioStatusTag.innerText = "Status: Querying Gemini & USDA";
        audioStatusTag.className = "badge-tag success";

        try {
            transcriptTextEl.innerText = `"${mealText}"`;

            const res = await fetch("/api/nutrition/parse-meal", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ transcript: mealText })
            });

            const data = await res.json();
            currentParsedPayload = data;
            renderParsedResult(data);
        } catch (err) {
            audioStatusTag.innerText = "Status: Parse Error";
            audioStatusTag.className = "badge-tag warning";
        }
    }

    function renderParsedResult(payload) {
        audioStatusTag.innerText = "Status: Parsed";
        audioStatusTag.className = "badge-tag success";

        pydanticJsonEl.innerText = JSON.stringify(payload, null, 2);

        const total = payload.total_macronutrients || {};
        macroCalsEl.innerText = `${total.calories || 0} kcal`;
        macroProtEl.innerText = `${total.protein_g || 0} g`;
        macroCarbsEl.innerText = `${total.carbs_g || 0} g`;
        macroFatsEl.innerText = `${total.fats_g || 0} g`;
    }

    // Commit Meal to Daily Log & Update Progress Bars
    if (commitMealBtn) {
        commitMealBtn.addEventListener("click", () => {
            if (!currentParsedPayload) {
                alert("Please record or type a meal first before logging.");
                return;
            }

            const total = currentParsedPayload.total_macronutrients || {};
            currentTotals.calories += (total.calories || 0);
            currentTotals.protein += (total.protein_g || 0);
            currentTotals.carbs += (total.carbs_g || 0);
            currentTotals.fats += (total.fats_g || 0);

            loggedMeals.push({
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                name: currentParsedPayload.meal_name || "Meal Ingestion",
                items: (currentParsedPayload.food_items || []).map(i => `${i.quantity} ${i.unit} ${i.item_name}`).join(", "),
                cals: total.calories || 0,
                prot: total.protein_g || 0,
                carbs: total.carbs_g || 0,
                fats: total.fats_g || 0
            });

            updateMacroProgressBars();
            renderFoodLogTable();
            alert("Meal successfully logged to your daily nutrition targets!");
        });
    }

    function updateMacroProgressBars() {
        const calsPct = Math.min(100, Math.round((currentTotals.calories / GOALS.calories) * 100));
        const protPct = Math.min(100, Math.round((currentTotals.protein / GOALS.protein) * 100));
        const carbsPct = Math.min(100, Math.round((currentTotals.carbs / GOALS.carbs) * 100));
        const fatsPct = Math.min(100, Math.round((currentTotals.fats / GOALS.fats) * 100));

        dashCalsText.innerText = `${Math.round(currentTotals.calories)} / ${GOALS.calories} kcal`;
        dashCalsBar.style.width = `${calsPct}%`;

        dashProtText.innerText = `${Math.round(currentTotals.protein)} / ${GOALS.protein} g`;
        dashProtBar.style.width = `${protPct}%`;

        dashCarbsText.innerText = `${Math.round(currentTotals.carbs)} / ${GOALS.carbs} g`;
        dashCarbsBar.style.width = `${carbsPct}%`;

        dashFatsText.innerText = `${Math.round(currentTotals.fats)} / ${GOALS.fats} g`;
        dashFatsBar.style.width = `${fatsPct}%`;
    }

    function renderFoodLogTable() {
        foodLogCountEl.innerText = `${loggedMeals.length} Meals Logged`;

        if (loggedMeals.length === 0) {
            foodLogTbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center" style="color: var(--text-secondary); padding: 20px;">No meals logged yet today. Use the voice logger above to add a meal!</td>
                </tr>`;
            return;
        }

        foodLogTbody.innerHTML = loggedMeals.map(m => `
            <tr>
                <td>${m.time}</td>
                <td><strong>${m.name}</strong></td>
                <td>${m.items}</td>
                <td style="color: var(--accent-amber); font-weight: 700;">${m.cals} kcal</td>
                <td style="color: var(--accent-cyan); font-weight: 700;">${m.prot} g</td>
                <td style="color: var(--accent-emerald); font-weight: 700;">${m.carbs} g</td>
                <td style="color: var(--accent-rose); font-weight: 700;">${m.fats} g</td>
            </tr>
        `).join("");
    }
});
