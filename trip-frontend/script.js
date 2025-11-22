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
    const message = document.getElementById("userMessage").value;
    if (!message.trim()) return;

    addUserMessage(message);
    document.getElementById("userMessage").value = "";

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

    const data = await res.json();
    addAIMessage(data.ai_message);

    if (data.is_final_itinerary) {
        renderItinerary();
        loadPackages();
    }
}

// ---------- Chat UI ----------
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

// ---------- Itinerary ----------
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
                    </li>`
                ).join("")}
            </ul>
        </div>`;
    });

    itineraryBox.innerHTML = html;
}

// ---------- Load Packages ----------
async function loadPackages() {
    const res = await fetch(`${BASE_URL}/trip-plan/${tripId}/packages`);
    const data = await res.json();

    const pkgBox = document.getElementById("packagesArea");
    pkgBox.classList.remove("hidden");

    let html = `<h2>💼 Choose a Package</h2>`;
    data.packages.forEach(p => {
        html += `
        <div class="day-block">
            <h3>${p.name}</h3>
            <p>${p.description}</p>
            <p>₹${p.min_price} - ₹${p.max_price}</p>
            <button onclick="selectPackage('${p.id}')">Select</button>
        </div>`;
    });

    pkgBox.innerHTML = html;
}

// ---------- Select Package ----------
async function selectPackage(packageId) {
    const res = await fetch(`${BASE_URL}/trip-plan/${tripId}/packages/${packageId}/select`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ register_id: registerId, email })
    });

    const data = await res.json();
    addAIMessage("Package Selected — Proceed to Payment 💳");
    showPayment();
}

// ---------- Payment ----------
function showPayment() {
    const box = document.getElementById("paymentArea");
    box.classList.remove("hidden");
    box.innerHTML = `
        <h2>💳 Complete Payment</h2>
        <button onclick="mockPayment()">Pay Now</button>
        <p id="paymentMsg"></p>
    `;
}

async function mockPayment() {
    const res = await fetch(`${BASE_URL}/trips/${tripId}/payment/mock`, { method: "POST" });
    const data = await res.json();

    document.getElementById("paymentMsg").innerText =
        `✔ Payment Success — Booking No: ${data.booking_number}`;

    addAIMessage("Payment received 🎉 Now you can leave a feedback.");
    document.getElementById("feedbackArea").classList.remove("hidden");
}

// ---------- Feedback ----------
async function sendFeedback() {
    const rating = document.getElementById("rating").value;
    const comments = document.getElementById("comments").value;

    const res = await fetch(`${BASE_URL}/trip-plan/${tripId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating, comments })
    });

    document.getElementById("feedbackMsg").innerText = "Feedback submitted ✔";
    addAIMessage("Thank you for feedback ❤️");
}
