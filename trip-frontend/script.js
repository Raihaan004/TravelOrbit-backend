const BASE_URL = "http://127.0.0.1:8000";

let tripId = null;
let registerId = null;
let email = null;

// ---------- Start Session ----------
async function startSession() {
    registerId = document.getElementById("registerId").value;
    email = document.getElementById("email").value;

    const res = await fetch(`${BASE_URL}/trip-plan/session/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ register_id: registerId, email })
    });

    const data = await res.json();

    tripId = data.trip_id;
    document.getElementById("sessionStatus").innerText =
        "Session Started ✔ Trip ID: " + tripId;

    addAIMessage("Hi! I'm TravelOrbit ✈️. Where would you like to travel?");
}


// ---------- Send Chat Message ----------
async function sendMessage() {
    if (!tripId) {
        alert("Start a session first!");
        return;
    }

    const message = document.getElementById("userMessage").value;
    if (message.trim() === "") return;

    addUserMessage(message);
    document.getElementById("userMessage").value = "";

    const sendButton = document.querySelector(".chat-input button");
    const userInput = document.getElementById("userMessage");
    
    // Disable input while waiting for response
    sendButton.disabled = true;
    userInput.disabled = true;

    try {
        const res = await fetch(`${BASE_URL}/trip-plan/session/message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                trip_id: tripId,
                register_id: registerId,
                email,
                message
            })
        });

        if (!res.ok) {
            const errorData = await res.json();
            const errorDetail = errorData.detail || "Unknown error";
            addAIMessage(`❌ Error: ${errorDetail}`);
            return;
        }

        const data = await res.json();
        addAIMessage(data.ai_message);

        if (data.is_final_itinerary) {
            renderItinerary();
        }
    } catch (err) {
        addAIMessage(`❌ Network error: ${err.message}`);
    } finally {
        // Re-enable input after response (success or error)
        sendButton.disabled = false;
        userInput.disabled = false;
        userInput.focus();
    }
}


// ---------- Chat Rendering ----------
function addUserMessage(text) {
    const box = document.getElementById("chatBox");
    box.innerHTML += `<div class="chat-message user">${text}</div>`;
    box.scrollTop = box.scrollHeight;
}

function addAIMessage(text) {
    const box = document.getElementById("chatBox");
    box.innerHTML += `<div class="chat-message ai">${text}</div>`;
    box.scrollTop = box.scrollHeight;
}


// ---------- Render Itinerary ----------
async function renderItinerary() {
    const res = await fetch(`${BASE_URL}/trip-plan/${tripId}`);
    const trip = await res.json();

    const itineraryBox = document.getElementById("itinerary");
    itineraryBox.classList.remove("hidden");

    let html = `<h2 class="itinerary-title">${trip.ai_summary_json.title}</h2>`;

    trip.ai_summary_json.days.forEach(day => {
        html += `
            <div class="day-block">
                <h3>Day ${day.day}: ${day.title}</h3>
                <ul>
                    ${day.activities.map(a => `
                        <li>
                            <strong>${a.name}</strong><br>
                            <a href="${a.map_url}" target="_blank">📍 Map</a> |
                            <a href="${a.image_search}" target="_blank">🖼 Images</a>
                            <br><small>${a.time || ""}</small>
                        </li>
                    `).join("")}
                </ul>
            </div>
        `;
    });

    itineraryBox.innerHTML = html;
}
