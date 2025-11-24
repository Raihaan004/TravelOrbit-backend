const BASE_URL = "http://127.0.0.1:8000";

let tripId = null;
let registerId = null;
let email = null;
let phoneNumber = null;
let membersCount = 1;

// Chat State Machine
const ChatState = {
    IDLE: 'IDLE',
    AUTH_CHOICE: 'AUTH_CHOICE',
    AUTH_EMAIL: 'AUTH_EMAIL',
    AUTH_EMAIL_OTP: 'AUTH_EMAIL_OTP',
    AUTH_PHONE: 'AUTH_PHONE',
    AUTH_NAME: 'AUTH_NAME',
    AUTH_PHONE_OTP: 'AUTH_PHONE_OTP',
    PASSENGER_COUNT: 'PASSENGER_COUNT',
    PASSENGER_DETAILS: 'PASSENGER_DETAILS'
};

let chatState = ChatState.IDLE;
let pendingAuthAction = null; // { type: 'DEAL' | 'PLAN', data: ... }
let tempAuthEmail = null;
let tempAuthPhone = null;
let tempAuthName = null;
let tempGoogleId = null;
let tempPassengerCount = 0;
let tempPassengers = [];

// ---------- Load Deals & Auto-Start Session ----------
window.addEventListener('load', async function() {
    // Check for existing user
    const user = localStorage.getItem("user");
    if (user) {
        const userData = JSON.parse(user);
        console.log("Logged in as:", userData.name);
        addLogoutButton(userData);
        
        // Set global vars
        registerId = userData.register_id;
        email = userData.email;
        phoneNumber = userData.phone;
    } else {
        // Generate guest ID if not logged in
        registerId = "guest-" + Math.random().toString(36).substr(2, 9);
        email = "guest@example.com";
    }

    // Auto-start session
    await startSession();
    
    // Load deals
    loadDeals();
});

// ---------- Start Session ----------
async function startSession() {
    try {
        const res = await fetch(`${BASE_URL}/trip-plan/session/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ register_id: registerId, email })
        });

        const data = await res.json();
        tripId = data.trip_id;
        console.log("Session started:", tripId);

        // Initial greeting
        addAIMessage("Hi! I'm TravelOrbit ✈️. Where would you like to travel today?");
    } catch (e) {
        console.error("Failed to start session:", e);
        addAIMessage("⚠️ Connection error. Please refresh the page.");
    }
}

// ---------- Handle User Action (Send Button) ----------
async function handleUserAction() {
    const input = document.getElementById("userMessage");
    const message = input.value.trim();
    if (!message) return;

    // Display user message
    addUserMessage(message);
    input.value = "";

    // Route based on state
    switch (chatState) {
        case ChatState.AUTH_CHOICE:
            await handleAuthChoice(message);
            break;
        case ChatState.AUTH_EMAIL:
            await handleAuthEmailInput(message);
            break;
        case ChatState.AUTH_EMAIL_OTP:
            await handleAuthEmailOtpInput(message);
            break;
        case ChatState.AUTH_PHONE:
            await handleAuthPhoneInput(message);
            break;
        case ChatState.AUTH_NAME:
            await handleAuthNameInput(message);
            break;
        case ChatState.AUTH_PHONE_OTP:
            await handleAuthPhoneOtpInput(message);
            break;
        case ChatState.PASSENGER_COUNT:
            await handlePassengerCountInput(message);
            break;
        case ChatState.PASSENGER_DETAILS:
            await handlePassengerDetailsInput(message);
            break;
        case ChatState.IDLE:
        default:
            await sendChatMessage(message);
            break;
    }
}

// ---------- Normal Chat Message ----------
async function sendChatMessage(message) {
    if (!tripId) {
        addAIMessage("❌ Session not active. Refreshing...");
        await startSession();
        return;
    }

    try {
        const res = await fetch(`${BASE_URL}/trip-plan/session/message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                trip_id: tripId,
                register_id: registerId,
                email: email,
                message: message
            })
        });

        if (!res.ok) throw new Error("Failed to send message");

        const data = await res.json();
        
        if (data.ai_message) {
            addAIMessage(data.ai_message);
        }

        if (data.is_final_itinerary) {
            renderItinerary();
            // Trigger Auth Flow for Booking
            initiateBookingFlow('PLAN');
        }
    } catch (e) {
        addAIMessage("❌ Error: " + e.message);
    }
}

// ---------- Initiate Booking Flow (Auth Check) ----------
function initiateBookingFlow(type, data = null) {
    pendingAuthAction = { type, data };
    
    const user = localStorage.getItem("user");
    if (user) {
        // Already logged in
        const userData = JSON.parse(user);
        registerId = userData.register_id;
        email = userData.email;
        
        addAIMessage("✅ You are logged in as " + userData.name);
        startPassengerCollection();
    } else {
        // Need Auth
        chatState = ChatState.AUTH_CHOICE;
        addAIMessage("🔒 To proceed with booking, I need to verify your identity.");
        addAIMessage("Please choose a login method:");
        
        // Add buttons
        const chatBox = document.getElementById("chatBox");
        const btnDiv = document.createElement("div");
        btnDiv.className = "chat-action-buttons";
        btnDiv.innerHTML = `
            <button onclick="triggerAuthChoice('EMAIL')" style="background:#007bff; color:white; border:none; padding:8px 15px; border-radius:15px; cursor:pointer; margin:5px;">📧 Email Login</button>
            <button onclick="triggerAuthChoice('GOOGLE')" style="background:#db4437; color:white; border:none; padding:8px 15px; border-radius:15px; cursor:pointer; margin:5px;">🇬 Google Login</button>
        `;
        chatBox.appendChild(btnDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

function triggerAuthChoice(choice) {
    const input = document.getElementById("userMessage");
    input.value = choice === 'EMAIL' ? "Email Login" : "Google Login";
    // Trigger the send button click or call handleUserAction directly if we can mock the input
    // Since handleUserAction reads from input.value, this works if we call it.
    // But handleUserAction is async.
    handleUserAction();
}

// ---------- Auth Flow Handlers ----------

async function handleAuthChoice(choice) {
    if (choice.toLowerCase().includes("google")) {
        addAIMessage("🔄 Opening Google Login...");
        try {
            const res = await fetch(`${BASE_URL}/auth/google/url`);
            const data = await res.json();
            
            // Open popup
            const width = 500;
            const height = 600;
            const left = (screen.width / 2) - (width / 2);
            const top = (screen.height / 2) - (height / 2);
            
            window.open(data.auth_url, "GoogleLogin", 
                `width=${width},height=${height},top=${top},left=${left}`);
                
            addAIMessage("Waiting for Google Login to complete...");
            
        } catch (e) {
            addAIMessage("❌ Error getting Google Login URL.");
        }
        return;
    }
    
    // Default to Email
    chatState = ChatState.AUTH_EMAIL;
    addAIMessage("Please enter your **Email Address**.");
}

// Global listener for Google Login Popup
window.addEventListener('message', async (event) => {
    if (event.data && event.data.type === 'GOOGLE_LOGIN_RESULT') {
        const result = event.data.payload;
        if (result.status === 'success') {
            completeLogin(result.user);
        } else if (result.status === 'needs_phone') {
            // Handle partial login
            tempAuthEmail = result.google_email;
            tempAuthName = result.google_name;
            tempGoogleId = result.google_temp_id; 
            
            chatState = ChatState.AUTH_PHONE;
            addAIMessage(`✅ Google Login successful, ${tempAuthName}!`);
            addAIMessage("I just need your **Phone Number** to complete the registration.");
        }
    }
});

async function handleAuthEmailInput(inputEmail) {
    // Simple email validation
    if (!inputEmail.includes("@")) {
        addAIMessage("⚠️ Please enter a valid email address.");
        return;
    }

    tempAuthEmail = inputEmail;
    addAIMessage("⏳ Checking email...");

    try {
        const res = await fetch(`${BASE_URL}/auth/email/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: tempAuthEmail })
        });
        
        if (!res.ok) throw new Error(await res.text());
        
        const data = await res.json();

        if (data.status === "existing") {
            chatState = ChatState.AUTH_EMAIL_OTP;
            addAIMessage("✅ Account found! OTP sent to your email. Please enter the **6-digit code**.");
        } else {
            // New User
            chatState = ChatState.AUTH_PHONE;
            addAIMessage("🆕 It looks like you're new here. Let's set up your account.");
            addAIMessage("Please enter your **Phone Number** (e.g., +919876543210).");
        }
    } catch (e) {
        addAIMessage("❌ Error: " + e.message + ". Please try again.");
    }
}

async function handleAuthEmailOtpInput(otp) {
    addAIMessage("⏳ Verifying Email OTP...");

    try {
        const res = await fetch(`${BASE_URL}/auth/email/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: tempAuthEmail, code: otp })
        });

        if (!res.ok) throw new Error("Invalid OTP");

        const data = await res.json();
        completeLogin(data);

    } catch (e) {
        addAIMessage("❌ Verification failed: " + e.message + ". Please enter the OTP again.");
    }
}

async function handleAuthPhoneInput(phone) {
    // Remove spaces and dashes
    let cleanPhone = phone.replace(/[\s-]/g, '');

    // Basic phone validation
    if (cleanPhone.length < 10) {
        addAIMessage("⚠️ Please enter a valid phone number (at least 10 digits).");
        return;
    }
    
    // Auto-add +91 if 10 digits (assuming India default)
    if (cleanPhone.length === 10 && /^\d+$/.test(cleanPhone)) {
        cleanPhone = "+91" + cleanPhone;
    } else if (!cleanPhone.startsWith("+")) {
        // If user typed 919876543210 but forgot +, add it
        cleanPhone = "+" + cleanPhone;
    }
    
    tempAuthPhone = cleanPhone;
    
    if (tempGoogleId) {
        // We have Google ID, skip name, send OTP using Google endpoint
        await sendGooglePhoneOtp();
    } else {
        chatState = ChatState.AUTH_NAME;
        addAIMessage("Please enter your **Full Name**.");
    }
}

async function sendGooglePhoneOtp() {
    addAIMessage(`⏳ Sending OTP to ${tempAuthPhone}...`);
    try {
        const res = await fetch(`${BASE_URL}/auth/google/phone/send-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                google_temp_id: tempGoogleId,
                phone: tempAuthPhone
            })
        });
        
        if (!res.ok) throw new Error(await res.text());
        
        const data = await res.json();
        // Update tempGoogleId to the new OTP ID for verification
        tempGoogleId = data.google_phone_temp_id;
        
        chatState = ChatState.AUTH_PHONE_OTP;
        addAIMessage("✅ OTP sent to your phone! Please enter the **6-digit code**.");
    } catch (e) {
        addAIMessage("❌ Error sending OTP: " + e.message);
    }
}

async function handleAuthNameInput(name) {
    if (name.length < 2) {
        addAIMessage("⚠️ Please enter a valid name.");
        return;
    }
    
    tempAuthName = name;
    addAIMessage(`⏳ Sending OTP to ${tempAuthPhone}...`);
    
    try {
        const res = await fetch(`${BASE_URL}/auth/phone/signup/send-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                phone: tempAuthPhone,
                email: tempAuthEmail,
                name: tempAuthName,
                age: 25, // Default
                location: "Unknown"
            })
        });
        
        if (!res.ok) throw new Error(await res.text());
        
        chatState = ChatState.AUTH_PHONE_OTP;
        addAIMessage("✅ OTP sent to your phone! Please enter the **6-digit code**.");
    } catch (e) {
        addAIMessage("❌ Error sending OTP: " + e.message + ". Please try again.");
    }
}

async function handleAuthPhoneOtpInput(otp) {
    addAIMessage("⏳ Verifying Phone OTP...");

    try {
        let url = `${BASE_URL}/auth/phone/signup/verify`;
        let body = { phone: tempAuthPhone, code: otp };
        
        if (tempGoogleId) {
            url = `${BASE_URL}/auth/google/phone/verify`;
            body = { google_temp_id: tempGoogleId, code: otp };
        }

        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (!res.ok) throw new Error("Invalid OTP");

        const data = await res.json();
        completeLogin(data);

    } catch (e) {
        addAIMessage("❌ Verification failed: " + e.message + ". Please enter the OTP again.");
    }
}

function completeLogin(userData) {
    // Save User
    const user = {
        name: userData.name || "Traveler",
        email: userData.email,
        phone: userData.phone,
        register_id: userData.register_id,
        token: userData.access_token // If available
    };
    localStorage.setItem("user", JSON.stringify(user));
    
    // Update Globals
    registerId = user.register_id;
    email = user.email;
    
    addLogoutButton(user);
    addAIMessage(`🎉 Login successful! Welcome, ${user.name}.`);
    
    // Proceed to next step
    startPassengerCollection();
}

// ---------- Passenger Collection Flow ----------
function startPassengerCollection() {
    chatState = ChatState.PASSENGER_COUNT;
    addAIMessage("👥 How many people are travelling (including yourself)? Please enter a number (e.g., 2).");
}

async function handlePassengerCountInput(input) {
    const count = parseInt(input);
    if (isNaN(count) || count < 1) {
        addAIMessage("⚠️ Please enter a valid number (1 or more).");
        return;
    }

    tempPassengerCount = count;
    tempPassengers = []; // Reset
    
    chatState = ChatState.PASSENGER_DETAILS;
    addAIMessage(`📝 Great, ${count} travelers. Please provide details for **Passenger 1** (Name, Age, Phone).`);
    addAIMessage("Format: `Name, Age, Phone` (e.g., John Doe, 30, 9876543210)");
}

async function handlePassengerDetailsInput(input) {
    // Parse input: "Name, Age, Phone"
    const parts = input.split(",").map(s => s.trim());
    if (parts.length < 2) {
        addAIMessage("⚠️ Please use the format: `Name, Age, Phone`");
        return;
    }

    const pName = parts[0];
    const pAge = parseInt(parts[1]) || 25;
    const pPhone = parts[2] || "";

    tempPassengers.push({ name: pName, age: pAge, phone: pPhone });

    if (tempPassengers.length < tempPassengerCount) {
        const nextNum = tempPassengers.length + 1;
        addAIMessage(`✅ Saved. Please provide details for **Passenger ${nextNum}**.`);
    } else {
        // All collected
        chatState = ChatState.IDLE;
        addAIMessage("✅ All passenger details saved!");
        
        // Execute Pending Action
        if (pendingAuthAction && pendingAuthAction.type === 'DEAL') {
            await finalizeDealBooking(pendingAuthAction.data);
        } else {
            // Normal Plan
            await savePassengersAndProceed();
        }
    }
}

// ---------- Finalize Normal Plan ----------
async function savePassengersAndProceed() {
    try {
        const res = await fetch(`${BASE_URL}/trip-plan/${tripId}/passengers`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                register_id: registerId,
                email: email,
                passengers: tempPassengers,
                contact_phone: tempPassengers[0].phone
            })
        });

        if (!res.ok) throw new Error("Failed to save passengers");

        addAIMessage("📋 Details confirmed. Loading packages...");
        loadPackages();
    } catch (e) {
        addAIMessage("❌ Error saving details: " + e.message);
    }
}

// ---------- Finalize Deal Booking ----------
async function finalizeDealBooking(dealData) {
    const dealId = dealData.id;
    const primary = tempPassengers[0];

    try {
        const res = await fetch(`${BASE_URL}/deals/${dealId}/start-plan`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                register_id: registerId,
                email: email,
                passenger_name: primary.name,
                contact_phone: primary.phone,
                passenger_age: primary.age,
                from_city: "User City", // Could ask this too
                passengers: tempPassengers
            })
        });

        if (!res.ok) throw new Error(await res.text());

        const data = await res.json();
        tripId = data.trip_id; // Update trip ID to the new deal trip
        
        addAIMessage("✅ Booking created for " + dealData.destination + "!");
        addAIMessage("💳 Proceeding to payment...");
        
        setTimeout(() => showPayment(), 1000);

    } catch (e) {
        addAIMessage("❌ Booking failed: " + e.message);
    }
}

// ---------- Show Deal Details (Chat Trigger) ----------
async function showDealDetails(dealId, destination) {
    // Instead of modal, we simulate a chat request
    addAIMessage(`🔍 Fetching details for **${destination}**...`);
    
    try {
        const res = await fetch(`${BASE_URL}/deals/${dealId}`);
        const deal = await res.json();
        
        // Format deal details as an AI message
        const perPerson = deal.price_per_person || deal.discounted_price;
        
        let msg = `**${deal.title || deal.destination}**\n`;
        msg += `📅 ${deal.duration_days} Days\n`;
        msg += `💰 **₹${perPerson.toLocaleString()}** per person\n`;
        msg += `📝 ${deal.description}\n\n`;
        
        if (deal.itinerary && deal.itinerary.days) {
            msg += `**Itinerary Highlights:**\n`;
            deal.itinerary.days.slice(0, 3).forEach(d => {
                msg += `• Day ${d.day}: ${d.title}\n`;
            });
            if (deal.itinerary.days.length > 3) msg += `...and more!\n`;
        }
        
        msg += `\nDo you want to book this deal?`;
        
        addAIMessage(msg);
        
        // Add a "Book Now" button in chat (simulated)
        const chatBox = document.getElementById("chatBox");
        const btnDiv = document.createElement("div");
        btnDiv.className = "chat-action-buttons";
        btnDiv.innerHTML = `<button onclick="initiateBookingFlow('DEAL', {id: '${dealId}', destination: '${destination}'})" style="background:#28a745; color:white; border:none; padding:8px 15px; border-radius:15px; cursor:pointer; margin-top:5px;">Book Now 🚀</button>`;
        chatBox.appendChild(btnDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (e) {
        addAIMessage("❌ Failed to load details.");
    }
}

// ---------- Load Deals of the Day ----------
async function loadDeals() {
    try {
        const res = await fetch(`${BASE_URL}/deals`);
        const data = await res.json();

        const container = document.getElementById("dealsContainer");
        if (!container) return;
        container.innerHTML = "";

        if (!data.deals || data.deals.length === 0) {
            container.innerHTML = "<p style='color: white; text-align: center;'>No deals available today</p>";
            return;
        }

        data.deals.forEach(deal => {
            const discountBadge = deal.discount_percentage 
                ? `<span class="deal-discount-badge">${deal.discount_percentage}% OFF</span>` 
                : "";

            const proxied = `${BASE_URL}${deal.image_url}`;
            const safeImg = proxied || "https://via.placeholder.com/600x400?text=No+Image";
            
            const perPerson = deal.price_per_person !== undefined ? Number(deal.price_per_person) : Number(deal.discounted_price);
            
            const dealHTML = `
                <div class="deal-card">
                    <img class="deal-image" src="${safeImg}" alt="${deal.destination}" onerror="this.onerror=null;this.src='https://via.placeholder.com/600x400?text=No+Image'">
                    <div class="deal-destination">${deal.title || deal.destination}</div>
                    <div class="deal-per-person">Per person: ₹${perPerson.toLocaleString()}</div>
                    <div class="deal-pricing">
                        <div class="deal-original-price">₹${Number(deal.original_price).toLocaleString()}</div>
                        <div class="deal-discounted-price">
                            ₹${Number(deal.discounted_price).toLocaleString()}
                            ${discountBadge}
                        </div>
                    </div>
                    <button class="deal-details-btn" onclick="showDealDetails('${deal.id}', '${deal.destination}')">
                        Get Details →
                    </button>
                </div>
            `;
            container.innerHTML += dealHTML;
        });
    } catch (error) {
        console.error("Error loading deals:", error);
    }
}

// ---------- UI Helpers ----------
function addUserMessage(text) {
    const box = document.getElementById("chatBox");
    box.innerHTML += `<div class="chat-message user">${text}</div>`;
    box.scrollTop = box.scrollHeight;
}

function addAIMessage(text) {
    const box = document.getElementById("chatBox");
    // Convert newlines to <br> and bold to <strong>
    let formatted = text.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    box.innerHTML += `<div class="chat-message ai">${formatted}</div>`;
    box.scrollTop = box.scrollHeight;
}

function addLogoutButton(user) {
    const container = document.querySelector(".container");
    // Remove existing header if any
    const existing = document.getElementById("userHeader");
    if (existing) existing.remove();

    const header = document.createElement("div");
    header.id = "userHeader";
    header.style.cssText = "display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 10px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);";
    
    header.innerHTML = `
        <div>
            <strong>Welcome, ${user.name}</strong>
        </div>
        <button onclick="logout()" style="background: #dc3545; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer;">Logout</button>
    `;
    
    container.insertBefore(header, container.firstChild);
}

function logout() {
    localStorage.removeItem("user");
    window.location.reload();
}

// ---------- Itinerary & Payment (Existing Logic) ----------
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
                ${day.activities.map(a => `<li>${a.name}</li>`).join("")}
            </ul>
        </div>`;
    });
    itineraryBox.innerHTML = html;
}

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

async function selectPackage(packageId) {
    const res = await fetch(`${BASE_URL}/trip-plan/${tripId}/packages/${packageId}/select`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ register_id: registerId, email, members_count: tempPassengerCount || 1 })
    });
    addAIMessage("Package Selected — Proceed to Payment 💳");
    showPayment();
}

function showPayment() {
    const box = document.getElementById("paymentArea");
    box.classList.remove("hidden");
    box.innerHTML = `
        <h2>💳 Complete Payment</h2>
        <button onclick="handlePayment()">Pay Now</button>
        <p id="paymentMsg"></p>
    `;
    box.scrollIntoView({ behavior: 'smooth' });
}

async function handlePayment() {
    const paymentMsg = document.getElementById("paymentMsg");
    paymentMsg.innerHTML = "Initializing payment...";

    try {
        if (!tripId) throw new Error("No trip found");
        const cleanTripId = tripId.trim();

        const response = await fetch(`${BASE_URL}/trips/${cleanTripId}/payment/create-order`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ trip_id: cleanTripId })
        });

        const orderData = await response.json();
        if (!response.ok) throw new Error(orderData.detail || "Failed to create order");

        const options = {
            "key": orderData.key_id,
            "amount": orderData.amount,
            "currency": orderData.currency,
            "name": "TravelOrbit",
            "description": `Trip Booking #${cleanTripId}`,
            "order_id": orderData.order_id,
            "handler": async function (response) {
                paymentMsg.innerHTML = "Verifying payment...";
                try {
                    const verifyResponse = await fetch(`${BASE_URL}/trips/${cleanTripId}/payment/verify`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            trip_id: cleanTripId,
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature
                        })
                    });
                    const verifyData = await verifyResponse.json();
                    if (verifyResponse.ok) {
                        paymentMsg.innerHTML = `<p style="color:green">✔ Payment Successful! Booking: ${verifyData.booking_number}</p>`;
                        addAIMessage("🎉 Payment received! Your booking is confirmed.");
                        showFeedbackForm();
                    } else {
                        throw new Error(verifyData.detail || "Verification failed");
                    }
                } catch (err) {
                    paymentMsg.innerHTML = `<p class="error">❌ Verification Error: ${err.message}</p>`;
                }
            },
            "prefill": { "email": orderData.email, "contact": orderData.contact },
            "theme": { "color": "#4c6ef5" }
        };

        const rzp1 = new Razorpay(options);
        rzp1.open();

    } catch (e) {
        paymentMsg.innerHTML = `<p class="error">❌ Error: ${e.message}</p>`;
    }
}

function showFeedbackForm() {
    document.getElementById("feedbackArea").classList.remove("hidden");
}

async function sendFeedback() {
    const rating = document.getElementById("rating").value;
    const comments = document.getElementById("comments").value;
    await fetch(`${BASE_URL}/trip-plan/${tripId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating, comments })
    });
    addAIMessage("❤️ Thank you for your feedback!");
    document.getElementById("feedbackArea").innerHTML = "<p>Feedback submitted!</p>";
}

// ---------- Test Payment Flow (Legacy) ----------
async function testPaymentFlow() {
    alert("Test mode is deprecated in this version.");
}
