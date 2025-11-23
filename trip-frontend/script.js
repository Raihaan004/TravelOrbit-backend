const BASE_URL = "http://127.0.0.1:8000";

let tripId = null;
let registerId = null;
let email = null;
let phoneNumber = null;
let membersCount = 1;

// ---------- Test Payment Flow (for frontend testing) ----------
async function testPaymentFlow() {
    // Create a test trip
    registerId = document.getElementById("registerId").value || "test-user-123";
    email = document.getElementById("email").value || "test@example.com";
    
    if (!registerId) {
        alert("Please enter Register ID");
        return;
    }
    if (!email) {
        alert("Please enter Email");
        return;
    }
    
    // Create a test trip in the database
    try {
        const res = await fetch(`${BASE_URL}/trip-plan/session/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ register_id: registerId, email })
        });
        
        const data = await res.json();
        tripId = data.trip_id;
        
        document.getElementById("sessionStatus").innerText = "✔ Test Session Started — Trip ID: " + tripId;
        addAIMessage("🧪 Test mode activated. Skipping to payment and feedback...");
        
        // Show payment area
        setTimeout(() => {
            document.getElementById("packagesArea").classList.add("hidden");
            showPayment();
        }, 500);
    } catch (err) {
        alert("Failed to create test session: " + err);
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

            // Use backend-proxied image URL to avoid CORS/hotlinking issues
            const proxied = `${BASE_URL}${deal.image_url}`;
            const safeImg = proxied || "https://via.placeholder.com/600x400?text=No+Image";
            const imgTag = `<img class="deal-image" src="${safeImg}" alt="${deal.destination}" onerror="this.onerror=null;this.src='https://via.placeholder.com/600x400?text=No+Image'">`;

            // Prefer explicit per-person price from backend; fall back to discounted_price
            const perPerson = deal.price_per_person !== undefined ? Number(deal.price_per_person) : Number(deal.discounted_price);
            const perPersonFormatted = perPerson.toLocaleString();
            const dealHTML = `
                <div class="deal-card">
                    ${imgTag}
                    <div class="deal-destination">${deal.title || deal.destination}</div>
                    ${deal.start_date || deal.end_date ? `<div class="deal-dates">${deal.start_date ? 'From: ' + deal.start_date : ''} ${deal.end_date ? 'To: ' + deal.end_date : ''}</div>` : ''}
                    <div class="deal-description">${deal.description || "Beautiful travel destination"}</div>
                    <div class="deal-per-person">Per person: ₹${perPersonFormatted}</div>
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
        const container = document.getElementById("dealsContainer");
        if (container) container.innerHTML = "<p style='color: white; text-align: center;'>Failed to load deals</p>";
    }
}

// ---------- Show Deal Details Modal ----------
async function showDealDetails(dealId, destination) {
    try {
        const res = await fetch(`${BASE_URL}/deals/${dealId}`);
        const deal = await res.json();

        console.log("=== DEAL DETAILS RECEIVED ===");
        console.log("Full deal object:", deal);
        console.log("Itinerary field:", deal.itinerary);
        console.log("Itinerary type:", typeof deal.itinerary);
        console.log("Has days?:", deal.itinerary && deal.itinerary.days);
        console.log("================================");

        // Store for later use
        window.currentDealId = dealId;
        window.currentDealDestination = destination;
        window.currentDeal = deal;

        // Show modal with deal details
        showDealDetailsModal(deal);
    } catch (error) {
        console.error("Error fetching deal details:", error);
        alert("Failed to load deal details");
    }
}

// ---------- Show Deal Details Modal ----------
function showDealDetailsModal(deal) {
    const modal = document.createElement("div");
    modal.id = "dealDetailsModal";
    modal.className = "modal";
    
    const perPerson = deal.price_per_person !== undefined ? Number(deal.price_per_person) : Number(deal.discounted_price);
    const originalPrice = Number(deal.original_price);
    const discountedPrice = Number(deal.discounted_price);
    const savings = originalPrice - discountedPrice;
    const discountPercentage = deal.discount_percentage || Math.round((savings / originalPrice) * 100);

    console.log("Building itinerary for deal:", deal);
    console.log("Itinerary object:", deal.itinerary);
    console.log("Itinerary type:", typeof deal.itinerary);
    
    // Check for itinerary (backend returns 'itinerary', not 'itinerary_json')
    let itineraryHtml = "";
    
    try {
        if (deal.itinerary) {
            console.log("Found itinerary, processing...");
            
            // Handle if itinerary is a string (might be JSON string)
            let itineraryData = deal.itinerary;
            if (typeof itineraryData === 'string') {
                console.log("Itinerary is string, parsing JSON...");
                itineraryData = JSON.parse(itineraryData);
            }
            
            console.log("Itinerary data after processing:", itineraryData);
            
            if (itineraryData && itineraryData.days && Array.isArray(itineraryData.days) && itineraryData.days.length > 0) {
                console.log("Days found, count:", itineraryData.days.length);
                
                itineraryHtml = itineraryData.days.map((day, idx) => {
                    console.log(`Processing day ${idx}:`, day);
                    const dayNum = day.day !== undefined ? day.day : (idx + 1);
                    
                    let activitiesHtml = "<li>🏖️ Relax and explore</li>";
                    if (day.activities && Array.isArray(day.activities) && day.activities.length > 0) {
                        activitiesHtml = day.activities.map(a => {
                            const actName = typeof a === 'string' ? a : (a.name || 'Activity');
                            return `<li>• ${actName}</li>`;
                        }).join("");
                    }
                    
                    return `
                        <div class="detail-day" style="margin: 15px 0; padding: 12px; background: #f5f7fa; border-left: 4px solid #667eea; border-radius: 4px;">
                            <strong style="font-size: 15px; color: #333;">📍 Day ${dayNum}: ${day.title || 'Exploration'}</strong>
                            <ul style="margin: 8px 0; padding-left: 20px; color: #555; font-size: 13px;">
                                ${activitiesHtml}
                            </ul>
                        </div>
                    `;
                }).join("");
                
                if (itineraryHtml) {
                    console.log("Successfully generated itinerary HTML");
                }
            }
        }
        
        // Fallback if no itinerary or empty itinerary
        if (!itineraryHtml) {
            console.log("No itinerary data, using fallback");
            const duration = deal.duration_days || 4;
            const defaultDays = [];
            
            for (let i = 1; i <= duration; i++) {
                if (i === 1) {
                    defaultDays.push(`
                        <div class="detail-day" style="margin: 15px 0; padding: 12px; background: #f5f7fa; border-left: 4px solid #667eea; border-radius: 4px;">
                            <strong style="font-size: 15px; color: #333;">📍 Day ${i}: Arrival & Settle In</strong>
                            <ul style="margin: 8px 0; padding-left: 20px; color: #555; font-size: 13px;">
                                <li>• Arrive at destination</li>
                                <li>• Check-in at hotel</li>
                                <li>• Relax and get fresh</li>
                            </ul>
                        </div>
                    `);
                } else if (i === duration) {
                    defaultDays.push(`
                        <div class="detail-day" style="margin: 15px 0; padding: 12px; background: #f5f7fa; border-left: 4px solid #667eea; border-radius: 4px;">
                            <strong style="font-size: 15px; color: #333;">📍 Day ${i}: Departure</strong>
                            <ul style="margin: 8px 0; padding-left: 20px; color: #555; font-size: 13px;">
                                <li>• Pack and checkout</li>
                                <li>• Head to airport/station</li>
                                <li>• Safe journey back</li>
                            </ul>
                        </div>
                    `);
                } else {
                    defaultDays.push(`
                        <div class="detail-day" style="margin: 15px 0; padding: 12px; background: #f5f7fa; border-left: 4px solid #667eea; border-radius: 4px;">
                            <strong style="font-size: 15px; color: #333;">📍 Day ${i}: Exploration</strong>
                            <ul style="margin: 8px 0; padding-left: 20px; color: #555; font-size: 13px;">
                                <li>• Visit local attractions</li>
                                <li>• Experience local cuisine</li>
                                <li>• Enjoy adventure activities</li>
                            </ul>
                        </div>
                    `);
                }
            }
            
            itineraryHtml = defaultDays.join("");
            console.log("Using default itinerary template");
        }
    } catch (e) {
        console.error("Error processing itinerary:", e);
        itineraryHtml = `<p style='color: #d32f2f; font-weight: bold;'>⚠️ Error loading itinerary: ${e.message}</p>`;
    }

    modal.innerHTML = `
        <div class="modal-content deal-details-modal" style="max-height: 80vh; overflow-y: auto;">
            <span class="close-modal" onclick="closeDealDetailsModal()">&times;</span>
            <h2 style="color: #333; margin-bottom: 20px;">${deal.title || deal.destination}</h2>
            <div class="modal-body">
                <div class="deal-info">
                    <p style="font-size: 14px; color: #666; margin: 8px 0;"><strong>Duration:</strong> ${deal.duration_days ? deal.duration_days + ' Days' : "Duration not specified"}</p>
                    <p style="font-size: 14px; color: #666; margin: 8px 0;"><strong>Dates:</strong> ${deal.start_date || "Flexible"} to ${deal.end_date || "Flexible"}</p>
                    <p style="font-size: 14px; color: #666; margin: 8px 0;"><strong>Description:</strong> ${deal.description || "No description available"}</p>
                    
                    <div class="pricing-details" style="margin: 20px 0; padding: 15px; background: #f0f3ff; border-radius: 8px;">
                        <p style="margin: 8px 0;">Original Price: <strike style="color: #999;">₹${originalPrice.toLocaleString()}</strike></p>
                        <p style="margin: 8px 0; font-weight: bold; color: #28a745;">Deal Price: ₹${discountedPrice.toLocaleString()}</p>
                        <p style="margin: 8px 0;">Per Person: <strong>₹${perPerson.toLocaleString()}</strong></p>
                        <p style="margin: 8px 0; color: #28a745; font-weight: bold;">You Save: ₹${savings.toLocaleString()} (${discountPercentage}% OFF)</p>
                    </div>
                    
                    <h3 style="margin-top: 25px; margin-bottom: 15px; color: #333; font-size: 16px;">📅 Daily Itinerary:</h3>
                    <div class="itinerary-details" style="margin: 15px 0;">
                        ${itineraryHtml}
                    </div>
                </div>
            </div>
            <div class="modal-footer" style="margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="closeDealDetailsModal()" class="btn-cancel" style="padding: 10px 20px; background: #e0e0e0; border: none; border-radius: 5px; cursor: pointer;">Cancel</button>
                <button onclick="proceedToAuth()" class="btn-primary" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">Proceed to Book</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = "block";
}

// ---------- Close Deal Details Modal ----------
function closeDealDetailsModal() {
    const modal = document.getElementById("dealDetailsModal");
    if (modal) modal.remove();
}

// ---------- Proceed to Auth ----------
function proceedToAuth() {
    closeDealDetailsModal();
    showAuthModal();
}

// ---------- Show Auth Modal ----------
function showAuthModal() {
    const modal = document.createElement("div");
    modal.id = "authModal";
    modal.className = "modal";

    modal.innerHTML = `
        <div class="modal-content auth-modal">
            <span class="close-modal" onclick="closeAuthModal()">&times;</span>
            <h2>🔐 Verify Your Details</h2>
            <div class="modal-body">
                <p>Before booking, please provide your details:</p>
                <div class="form-group">
                    <label>Register ID:</label>
                    <input type="text" id="authRegisterId" placeholder="Enter your Register ID" />
                </div>
                <div class="form-group">
                    <label>Email:</label>
                    <input type="email" id="authEmail" placeholder="Enter your email" />
                </div>
                <div class="form-group">
                    <label>Phone Number:</label>
                    <input type="tel" id="authPhone" placeholder="Enter your phone number" />
                </div>
                <div class="form-group">
                    <label>Full Name:</label>
                    <input type="text" id="authName" placeholder="Enter your full name" />
                </div>
                <div class="form-group">
                    <label>Age:</label>
                    <input type="number" id="authAge" placeholder="Enter your age" min="1" max="120" />
                </div>
                <div class="form-group">
                    <label>Travelling From (Your City):</label>
                    <input type="text" id="authFromPlace" placeholder="e.g., Mumbai, Delhi, Bangalore" />
                </div>
            </div>
            <div class="modal-footer">
                <button onclick="closeAuthModal()" class="btn-cancel">Cancel</button>
                <button onclick="verifyAuth()" class="btn-primary">Verify & Proceed</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = "block";
}

// ---------- Close Auth Modal ----------
function closeAuthModal() {
    const modal = document.getElementById("authModal");
    if (modal) modal.remove();
}

// ---------- Verify Auth and Continue ----------
async function verifyAuth() {
    const authRegisterId = document.getElementById("authRegisterId").value.trim();
    const authEmail = document.getElementById("authEmail").value.trim();
    const authPhone = document.getElementById("authPhone").value.trim();
    const authName = document.getElementById("authName").value.trim();
    const authAge = document.getElementById("authAge").value.trim();
    const authFromPlace = document.getElementById("authFromPlace").value.trim();

    if (!authRegisterId || !authEmail || !authPhone || !authName || !authAge || !authFromPlace) {
        alert("Please fill in all fields");
        return;
    }

    // Store auth info
    registerId = authRegisterId;
    email = authEmail;
    window.fromPlace = authFromPlace;

    // Update the session inputs
    document.getElementById("registerId").value = registerId;
    document.getElementById("email").value = email;

    closeAuthModal();

    // Ask for number of travelers
    showMemberCountModal(authPhone, authName, authAge);
}

// ---------- Show Member Count Modal ----------
function showMemberCountModal(primaryPhone, primaryName, primaryAge) {
    const modal = document.createElement("div");
    modal.id = "memberCountModal";
    modal.className = "modal";

    modal.innerHTML = `
        <div class="modal-content auth-modal">
            <h2>👥 How many members are travelling?</h2>
            <div class="modal-body">
                <p>Including yourself, how many people total will be on this trip?</p>
                <div class="form-group">
                    <label>Number of Members:</label>
                    <input type="number" id="memberCount" placeholder="Enter number" min="1" max="20" value="1" />
                </div>
            </div>
            <div class="modal-footer">
                <button onclick="closeMemberCountModal()" class="btn-cancel">Cancel</button>
                <button onclick="confirmMemberCount('${primaryPhone}', '${primaryName}', '${primaryAge}')" class="btn-primary">Continue</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = "block";
}

// ---------- Close Member Count Modal ----------
function closeMemberCountModal() {
    const modal = document.getElementById("memberCountModal");
    if (modal) modal.remove();
}

// ---------- Confirm Member Count and Collect Details ----------
function confirmMemberCount(primaryPhone, primaryName, primaryAge) {
    const count = parseInt(document.getElementById("memberCount").value);
    if (!count || count < 1) {
        alert("Please enter a valid number");
        return;
    }

    closeMemberCountModal();

    // Store companions info
    window.companionsInfo = [];
    window.totalMembers = count;
    
    // The primary person is always included
    window.primaryMemberInfo = {
        phone: primaryPhone,
        name: primaryName,
        age: parseInt(primaryAge)
    };

    if (count === 1) {
        // No companions needed
        startPlanFromDeal(window.currentDealId, window.currentDealDestination, primaryPhone, primaryName, primaryAge);
    } else {
        // Collect companion details
        showCompanionDetailsModal(0, count, primaryPhone, primaryName, primaryAge);
    }
}

// ---------- Show Companion Details Modal ----------
function showCompanionDetailsModal(companionIndex, totalMembers, primaryPhone, primaryName, primaryAge) {
    const modal = document.createElement("div");
    modal.id = "companionModal";
    modal.className = "modal";

    const companionNumber = companionIndex + 2; // Start from 2 since primary is 1

    modal.innerHTML = `
        <div class="modal-content auth-modal">
            <span class="close-modal" onclick="closeCompanionModal()">&times;</span>
            <h2>👤 Member ${companionNumber} Details</h2>
            <div class="modal-body">
                <p>Entering details for member ${companionNumber} of ${totalMembers}</p>
                <div class="form-group">
                    <label>Full Name:</label>
                    <input type="text" id="companionName" placeholder="Enter full name" />
                </div>
                <div class="form-group">
                    <label>Age:</label>
                    <input type="number" id="companionAge" placeholder="Enter age" min="1" max="120" />
                </div>
                <div class="form-group">
                    <label>Phone Number:</label>
                    <input type="tel" id="companionPhone" placeholder="Enter phone number" />
                </div>
            </div>
            <div class="modal-footer">
                <button onclick="closeCompanionModal()" class="btn-cancel">Cancel</button>
                <button onclick="saveCompanionDetails(${companionIndex}, ${totalMembers}, '${primaryPhone}', '${primaryName}', '${primaryAge}')" class="btn-primary">
                    ${companionIndex + 2 === totalMembers ? 'Finish & Continue' : 'Next Member'}
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = "block";
}

// ---------- Close Companion Modal ----------
function closeCompanionModal() {
    const modal = document.getElementById("companionModal");
    if (modal) modal.remove();
}

// ---------- Save Companion Details ----------
function saveCompanionDetails(companionIndex, totalMembers, primaryPhone, primaryName, primaryAge) {
    const name = document.getElementById("companionName").value.trim();
    const age = document.getElementById("companionAge").value.trim();
    const phone = document.getElementById("companionPhone").value.trim();

    if (!name || !age || !phone) {
        alert("Please fill in all fields");
        return;
    }

    // Store companion info
    window.companionsInfo.push({
        name: name,
        age: parseInt(age),
        phone: phone
    });

    closeCompanionModal();

    // Check if we need to collect more companions
    if (companionIndex + 2 < totalMembers) {
        // Show next companion modal
        showCompanionDetailsModal(companionIndex + 1, totalMembers, primaryPhone, primaryName, primaryAge);
    } else {
        // All companions collected, start the plan
        startPlanFromDeal(window.currentDealId, window.currentDealDestination, primaryPhone, primaryName, primaryAge);
    }
}

// Load deals when page loads
window.addEventListener('load', loadDeals);

// ---------- Start Plan from Deal (AI Chat Flow) ----------
async function startPlanFromDeal(dealId, destination, phone = null, name = null, age = null) {
    registerId = document.getElementById("registerId").value || registerId;
    email = document.getElementById("email").value || email;

    // Ensure register/email set
    if (!registerId) registerId = "REG-" + Math.random().toString(36).substr(2, 9);
    if (!email) email = "user@example.com";

    try {
        // Build passengers list with primary + companions
        let passengers = [{
            name: name,
            age: parseInt(age),
            phone: phone
        }];

        // Add companions if any
        if (window.companionsInfo && window.companionsInfo.length > 0) {
            passengers = passengers.concat(window.companionsInfo);
        }

        // Send all passenger details to backend
        const res = await fetch(`${BASE_URL}/deals/${dealId}/start-plan`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                register_id: registerId,
                email: email,
                passenger_name: name || null,
                contact_phone: phone || null,
                passenger_age: age || null,
                from_city: window.fromPlace || null,
                passengers: passengers  // Send all passenger details (stored in JSONB)
            })
        });

        if (!res.ok) {
            const err = await res.text();
            console.error("start-plan failed:", err);
            alert("Failed to start plan: " + res.status);
            return;
        }

        const data = await res.json();
        tripId = data.trip_id;
        document.getElementById("sessionStatus").innerText = "Session Started ✔ Trip ID: " + tripId;

        // Display AI's first message
        if (data.ai_message) {
            addAIMessage(data.ai_message);
        }

        // For deal bookings, directly show payment
        // Don't wait for itinerary/packages - go straight to payment
        addAIMessage("✅ Booking confirmed! Ready to proceed to payment? 💳");
        
        // Store that we're in deal booking mode for payment
        window.isDealBooking = true;
        
        setTimeout(() => {
            showPayment();
        }, 500);

    } catch (e) {
        console.error("Error calling start-plan:", e);
        alert("Error starting plan. See console for details.");
    }
}

// ---------- Start Session ----------
async function startSession(dealDestination = null) {
    registerId = document.getElementById("registerId").value;
    email = document.getElementById("email").value;
    phoneNumber = document.getElementById("phoneNumber").value;

    const res = await fetch(`${BASE_URL}/trip-plan/session/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ register_id: registerId, email })
    });

    const data = await res.json();
    tripId = data.trip_id;

    document.getElementById("sessionStatus").innerText =
        "Session Started ✔ Trip ID: " + tripId;

    if (dealDestination) {
        addAIMessage(`Hi! I'm TravelOrbit ✈️. Great choice! You're interested in ${dealDestination}. Let's plan your trip!`);
        addUserMessage(`Plan a trip to ${dealDestination}`);
    } else {
        addAIMessage("Hi! I'm TravelOrbit ✈️. Where would you like to travel?");
    }
}




// ---------- Send Chat Message ----------
async function sendMessage() {
    const message = document.getElementById("userMessage").value;
    if (!message.trim()) return;

    // Check if trip session is started
    if (!tripId) {
        addAIMessage("❌ Please start a session first by clicking 'Start Session'");
        return;
    }

    addUserMessage(message);
    document.getElementById("userMessage").value = "";

    // Get current email and register_id from inputs
    const currentEmail = document.getElementById("email").value || email || "user@example.com";
    const currentRegisterId = document.getElementById("registerId").value || registerId || "user123";

    try {
        const res = await fetch(`${BASE_URL}/trip-plan/session/message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                trip_id: tripId,
                register_id: currentRegisterId,
                email: currentEmail,
                message: message
            })
        });

        if (!res.ok) {
            let errorMsg = "Failed to send message";
            try {
                const error = await res.json();
                console.error("Message error:", error);
                if (error.detail) {
                    if (typeof error.detail === 'string') {
                        errorMsg = error.detail;
                    } else if (typeof error.detail === 'object') {
                        errorMsg = JSON.stringify(error.detail);
                    }
                }
            } catch (e) {
                console.error("Could not parse error response");
            }
            addAIMessage("❌ Error: " + errorMsg);
            return;
        }

        const data = await res.json();
        
        if (data.ai_message) {
            addAIMessage(data.ai_message);
        }

        if (data.is_final_itinerary) {
            renderItinerary();
            loadPackages();
        }
    } catch (e) {
        console.error("Network error:", e);
        addAIMessage("❌ Network error: " + e.message);
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
    const sd = trip.start_date ? trip.start_date : (trip.ai_summary_json && trip.ai_summary_json.start_date ? trip.ai_summary_json.start_date : null);
    const ed = trip.end_date ? trip.end_date : (trip.ai_summary_json && trip.ai_summary_json.end_date ? trip.ai_summary_json.end_date : null);
    let datesHtml = '';
    if (sd || ed) {
        datesHtml = `<div class="itinerary-dates">${sd ? 'Start: ' + sd : ''} ${ed ? ' — End: ' + ed : ''}</div>`;
    }

    let html = `${datesHtml}<h2 class="itinerary-title">${trip.ai_summary_json.title}</h2>`;

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
        body: JSON.stringify({ register_id: registerId, email, members_count: membersCount })
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
    try {
        // Validate trip ID exists
        if (!tripId) {
            const paymentMsg = document.getElementById("paymentMsg");
            paymentMsg.innerHTML = `
                <div style="background: #f8d7da; border: 2px solid #dc3545; border-radius: 8px; padding: 15px; margin-top: 15px;">
                    <p style="color: #721c24; font-weight: bold; margin: 5px 0;">❌ Error</p>
                    <p style="color: #721c24; margin: 5px 0;"><strong>Error:</strong> No trip found. Please start a deal booking first.</p>
                </div>
            `;
            addAIMessage("❌ Payment failed: No valid trip ID. Please start a booking first.");
            return;
        }

        const res = await fetch(`${BASE_URL}/trips/${tripId}/payment/mock`, { method: "POST" });
        
        if (!res.ok) {
            let errorMsg = `Payment failed with status ${res.status}`;
            try {
                const errorData = await res.json();
                if (errorData.detail) {
                    errorMsg = typeof errorData.detail === 'string' 
                        ? errorData.detail 
                        : JSON.stringify(errorData.detail);
                }
            } catch (e) {
                // Could not parse error response, use status message
            }
            
            const paymentMsg = document.getElementById("paymentMsg");
            paymentMsg.innerHTML = `
                <div style="background: #f8d7da; border: 2px solid #dc3545; border-radius: 8px; padding: 15px; margin-top: 15px;">
                    <p style="color: #721c24; font-weight: bold; margin: 5px 0;">❌ Payment Failed</p>
                    <p style="color: #721c24; margin: 5px 0;"><strong>Error:</strong> ${errorMsg}</p>
                    <p style="color: #666; margin: 10px 0; font-size: 13px;">Please check your trip details and try again.</p>
                </div>
            `;
            addAIMessage(`❌ Payment failed: ${errorMsg}`);
            return;
        }
        
        const data = await res.json();

        // Update payment message with more details
        const paymentMsg = document.getElementById("paymentMsg");
        paymentMsg.innerHTML = `
            <div style="background: #d4edda; border: 2px solid #28a745; border-radius: 8px; padding: 15px; margin-top: 15px;">
                <p style="color: #155724; font-weight: bold; margin: 5px 0;">✔ Payment Successful!</p>
                <p style="color: #155724; margin: 5px 0;"><strong>Booking Number:</strong> ${data.booking_number}</p>
                <p style="color: #155724; margin: 5px 0;"><strong>Amount:</strong> ₹${data.amount} ${data.currency}</p>
                <p style="color: #666; margin: 10px 0; font-size: 13px;">Confirmation email has been sent with your itinerary and tickets.</p>
            </div>
        `;

        addAIMessage("🎉 Payment received! Your booking is confirmed.\n\n📧 Check your email for:\n• Booking confirmation\n• Trip itinerary\n• All traveler details\n\n⭐ Please leave your feedback below:");
        
        // Show feedback area immediately after payment
        showFeedbackForm();
    } catch (e) {
        console.error("Payment error:", e);
        const paymentMsg = document.getElementById("paymentMsg");
        paymentMsg.innerHTML = `
            <div style="background: #f8d7da; border: 2px solid #dc3545; border-radius: 8px; padding: 15px; margin-top: 15px;">
                <p style="color: #721c24; font-weight: bold; margin: 5px 0;">❌ Network Error</p>
                <p style="color: #721c24; margin: 5px 0;"><strong>Error:</strong> ${e.message}</p>
                <p style="color: #666; margin: 10px 0; font-size: 13px;">Check console for details.</p>
            </div>
        `;
        addAIMessage(`❌ Network error during payment: ${e.message}`);
    }
}

// ---------- Show Feedback Form ----------
function showFeedbackForm() {
    const feedbackBox = document.getElementById("feedbackArea");
    feedbackBox.classList.remove("hidden");
    
    // Scroll to feedback area
    setTimeout(() => {
        feedbackBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

// ---------- Feedback ----------
async function sendFeedback() {
    const rating = document.getElementById("rating").value;
    const comments = document.getElementById("comments").value;

    if (!rating) {
        alert("Please select a rating");
        return;
    }

    const res = await fetch(`${BASE_URL}/trip-plan/${tripId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating, comments })
    });

    if (res.ok) {
        document.getElementById("feedbackMsg").innerHTML = `
            <div style="background: #d4edda; border: 2px solid #28a745; border-radius: 8px; padding: 10px; margin-top: 10px;">
                <p style="color: #155724; font-weight: bold; margin: 0;">✔ Feedback submitted successfully!</p>
            </div>
        `;
        addAIMessage("❤️ Thank you for your feedback! We appreciate your valuable input.");
        
        // Disable rating and comments inputs
        document.getElementById("rating").disabled = true;
        document.getElementById("comments").disabled = true;
        document.getElementById("feedbackArea").querySelector("button").disabled = true;
    } else {
        alert("Failed to submit feedback");
    }
    
    // Show Book Again button after feedback
    showBookAgainOption();
}

// ---------- Show Book Again Option ----------
function showBookAgainOption() {
    const feedbackBox = document.getElementById("feedbackArea");
    
    // Check if button already exists
    if (feedbackBox.querySelector(".book-again-btn")) {
        return;
    }
    
    // Add separator
    const separator = document.createElement("hr");
    separator.style.cssText = "margin: 20px 0; border: none; border-top: 2px solid #ddd;";
    feedbackBox.appendChild(separator);
    
    // Add Book Again button
    const bookAgainBtn = document.createElement("button");
    bookAgainBtn.className = "book-again-btn";
    bookAgainBtn.textContent = "🎒 Book Another Trip";
    bookAgainBtn.style.cssText = "width: 100%; padding: 15px; margin-top: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition: transform 0.2s ease;";
    bookAgainBtn.onmouseover = function() { this.style.transform = "scale(1.02)"; };
    bookAgainBtn.onmouseout = function() { this.style.transform = "scale(1)"; };
    bookAgainBtn.onclick = resetAndBookAgain;
    
    feedbackBox.appendChild(bookAgainBtn);
    
    // Add message
    addAIMessage("✈️ Ready for your next adventure? Click 'Book Another Trip' to explore more deals!");
}

// ---------- Reset and Book Again ----------
function resetAndBookAgain() {
    // Reset all variables
    tripId = null;
    registerId = null;
    email = null;
    membersCount = 1;
    window.companionsInfo = [];
    window.totalMembers = 1;
    window.primaryMemberInfo = null;
    window.currentDealId = null;
    window.currentDealDestination = null;
    window.fromPlace = null;
    window.isDealBooking = false;
    
    // Hide all areas
    document.getElementById("chatBox").innerHTML = "";
    document.getElementById("itinerary").classList.add("hidden");
    document.getElementById("packagesArea").classList.add("hidden");
    document.getElementById("paymentArea").classList.add("hidden");
    document.getElementById("feedbackArea").classList.add("hidden");
    document.getElementById("sessionStatus").innerText = "";
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Show deals section
    setTimeout(() => {
        loadDeals();
        addAIMessage("✈️ Ready for your next adventure? Check out our latest deals! 🎉");
    }, 500);
}
