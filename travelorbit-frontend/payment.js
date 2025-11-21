async function makePayment() {
    const tripId = document.getElementById("tripId").value;

    if (!tripId) {
        alert("Please enter trip_id");
        return;
    }

    const resultBox = document.getElementById("result");
    resultBox.style.display = "block";
    resultBox.innerHTML = "Processing payment...";

    try {
        const response = await fetch(`http://127.0.0.1:8000/trips/${tripId}/payment/mock`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        const data = await response.json();

        if (!response.ok) {
            resultBox.innerHTML = `<p class='error'>❌ Error: ${data.detail}</p>`;
            return;
        }

        resultBox.innerHTML = `
            <p class="success">✔ Payment Successful!</p>
            <p><strong>Booking Number:</strong> ${data.booking_number}</p>
            <p><strong>Amount Paid:</strong> ${data.amount} ${data.currency}</p>
            <hr>
            <p>Check your email for:</p>
            <ul>
                <li>Invoice</li>
                <li>Trip Ticket</li>
            </ul>
        `;
    } catch (err) {
        resultBox.innerHTML = `<p class="error">❌ Something went wrong: ${err}</p>`;
    }
}
