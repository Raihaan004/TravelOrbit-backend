const API_BASE_URL = "http://localhost:8000"; // Adjust if deployed

document.addEventListener("DOMContentLoaded", async () => {
    const urlParams = new URLSearchParams(window.location.search);
    let groupId = urlParams.get("group_id");
    const groupNameEl = document.getElementById("group-name");
    const form = document.getElementById("voting-form");
    const messageEl = document.getElementById("message");

    // Check for short code in path (e.g. /vote/AB12CD)
    const pathSegments = window.location.pathname.split('/');
    const potentialCode = pathSegments[pathSegments.length - 1];
    
    // If no group_id param, try to use the code from path
    if (!groupId && potentialCode && potentialCode !== "vote.html") {
        // Resolve code to group details directly
        try {
            const response = await fetch(`${API_BASE_URL}/groups/code/${potentialCode}`);
            if (response.ok) {
                const data = await response.json();
                groupId = data.group_id;
                groupNameEl.textContent = `Voting for: ${data.name}`;
                renderDestinationOptions(data.destination_options);
            } else {
                throw new Error("Group not found");
            }
        } catch (error) {
            groupNameEl.textContent = "Error loading group details.";
            console.error(error);
            form.style.display = "none";
            return;
        }
    } else if (groupId) {
        // Fetch Group Details by ID (Legacy/Direct)
        try {
            const response = await fetch(`${API_BASE_URL}/groups/${groupId}`);
            if (!response.ok) throw new Error("Group not found");
            const data = await response.json();
            groupNameEl.textContent = `Voting for: ${data.name}`;
            renderDestinationOptions(data.destination_options);
        } catch (error) {
            groupNameEl.textContent = "Error loading group details.";
            console.error(error);
        }
    } else {
        groupNameEl.textContent = "Error: No Group ID or Code provided.";
        form.style.display = "none";
        return;
    }

    function renderDestinationOptions(options) {
        const container = document.getElementById("destination-options");
        container.innerHTML = "";
        
        if (!options || options.length === 0) {
            container.innerHTML = '<input type="text" id="destination" placeholder="e.g. Bali, Paris, Goa">';
            return;
        }

        options.forEach((opt, index) => {
            const div = document.createElement("div");
            div.style.marginBottom = "5px";
            div.innerHTML = `
                <label style="font-weight: normal; cursor: pointer;">
                    <input type="radio" name="destination_vote" value="${opt}" ${index === 0 ? 'checked' : ''}> 
                    ${opt}
                </label>
            `;
            container.appendChild(div);
        });
    }

    // Handle Vote Submission
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const name = document.getElementById("name").value;
        const email = document.getElementById("email").value;
        const phone = document.getElementById("phone").value;
        
        // Get selected radio or text input
        let destination = null;
        const radio = document.querySelector('input[name="destination_vote"]:checked');
        if (radio) {
            destination = radio.value;
        } else {
            const textInput = document.getElementById("destination");
            if (textInput) destination = textInput.value;
        }

        const budget = document.getElementById("budget").value;
        const startDate = document.getElementById("start-date").value || null;
        const endDate = document.getElementById("end-date").value || null;
        
        const activities = Array.from(document.querySelectorAll('input[name="activity"]:checked'))
            .map(cb => cb.value);

        const payload = {
            voter_name: name,
            voter_email: email,
            voter_phone: phone,
            destination: destination,
            budget: budget,
            start_date: startDate,
            end_date: endDate,
            activities: activities
        };

        try {
            const response = await fetch(`${API_BASE_URL}/groups/${groupId}/vote`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            
            if (response.ok) {
                messageEl.textContent = "🎉 Vote submitted successfully!";
                messageEl.style.color = "green";
                form.reset();
            } else {
                messageEl.textContent = `Error: ${result.detail || "Failed to submit vote"}`;
                messageEl.style.color = "red";
            }
        } catch (error) {
            messageEl.textContent = "Network error. Please try again.";
            messageEl.style.color = "red";
            console.error(error);
        }
    });
});
