(function() {
    // Helper function to get the CSRF token from the cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    document.addEventListener('DOMContentLoaded', () => {
        const searchBtn = document.getElementById('searchbutton');
        const researchBtn = document.getElementById('researchbutton');

        if (searchBtn) {
            searchBtn.addEventListener('click', sendData);
            console.log("Search button listener attached!");
        }
        if (researchBtn) {
            researchBtn.addEventListener('click', sendData);
            console.log("Research button listener attached!");
        }
    });

    function sendData() {
        // --- 1. GRAB FRESH TOKEN ---
        const freshToken = getCookie('csrftoken');

        // --- Collect Data ---
        const checkedBoxes = document.querySelectorAll('input[name="additions"]:checked');
        const selectedAdditions = Array.from(checkedBoxes).map(cb => cb.value);

        const data = {
            amount: document.getElementById('amount')?.value || '',
            specialty: document.querySelector('input[name="specialty"]:checked')?.value || '',
            additions: selectedAdditions,
            sorting: document.querySelector('input[name="sorting"]:checked')?.value || '',
            address: document.getElementById('address')?.value || '',
            day: document.getElementById('day-select')?.value || '',
        };

        // --- UI Feedback (The "Loading" state) ---
        const sBtn = document.getElementById('searchbutton');
        const rBtn = document.getElementById('researchbutton');
        const txt = document.getElementById('buttontext');
        const spin = document.getElementById('spinner');

        if (sBtn) sBtn.disabled = true;
        if (rBtn) rBtn.disabled = true;
        // Using optional chaining (?) in case these IDs don't exist on both pages
        if (txt) txt.style.display = 'none';
        if (spin) spin.style.display = 'inline';

        fetch('/analysis/rest_search/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': freshToken, // Uses the fresh cookie token
            },
            // Ensures your session (login) stays active during the fetch
            credentials: 'same-origin', 
            body: JSON.stringify(data)
        })
        .then(response => {
            // Safety check: if Django returns HTML (like a 403 or 404 page)
            if (!response.ok) {
                return response.text().then(text => { throw new Error(text) });
            }
            return response.json();
        })
        .then(data => {
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            }
        })
        .catch(error => {
            console.error("Fetch Error:", error);
            // If you get the 403 error again, it will alert here
            alert("Search failed. Check console for details.");
        })
        .finally(() => {
            // Reset UI
            if (sBtn) sBtn.disabled = false;
            if (rBtn) rBtn.disabled = false;
            if (txt) txt.style.display = 'inline';
            if (spin) spin.style.display = 'none';
        });
    }
})();