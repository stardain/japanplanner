window.openDetails = function(element) {
    // 1. Locate all Modal elements
    const modal = document.getElementById('restaurantModal');
    const nameEl = document.getElementById('modalRestName');
    const ratingEl = document.getElementById('modalRating');
    const shortDescEl = document.getElementById('modalShortDesc');
    const longDescEl = document.getElementById('modalLongDesc');
    const timeEl = document.getElementById('modalTime');
    const stationEl = document.getElementById('modalStation');
    const openHoursEl = document.getElementById('modalOpenHours');
    const closedOnEl = document.getElementById('modalClosedOn');
    const feeEl = document.getElementById('modalFee');
    const imageEl = document.getElementById('modalImage');
    const saveBtn = document.getElementById('modalSaveButton');
    const saveMsg = document.getElementById('saveMessage'); 

    if (!modal) {
        console.error("Popup elements missing from HTML! Check your IDs.");
        return;
    }

    // 2. Reset the Save Message visibility
    saveMsg.style.display = 'none';

    // 3. Fill Modal fields from the clicked card's dataset
    // Note: JavaScript automatically converts data-short-desc to element.dataset.shortDesc (camelCase)
    nameEl.textContent = element.dataset.name || "Restaurant Name";
    ratingEl.textContent = (element.dataset.rating || "N/A") + " / 4";
    shortDescEl.textContent = element.dataset.shortDesc || "";
    timeEl.textContent = (element.dataset.time || "??") + " min away";
    stationEl.textContent = element.dataset.station || "Station unknown";
    closedOnEl.textContent = element.dataset.closedOn || "Always open";
    feeEl.textContent = element.dataset.fee || "No fee info";
    imageEl.src = element.dataset.mainPic || "";

    // Format Long Description (Decodes and handles tags like 【Tag】)
    let rawDesc = element.dataset.longDesc || "";
    const cleanDesc = rawDesc.replace(/【([^】]+)】/g, '<div class="featured-tag">【$1】</div>');
    if (longDescEl) longDescEl.innerHTML = cleanDesc;

    // Pull Open Hours from the 'hidden-hours' div inside the specific card
    const card = element.closest('.restaurant-card');
    const hiddenHours = card.querySelector('.hidden-hours');
    if (openHoursEl) {
        openHoursEl.innerHTML = hiddenHours ? hiddenHours.innerHTML : "<li>Hours not available</li>";
    }

    // 4. FIX: Re-bind the Close Button
    // We re-assign this every time the modal opens to ensure it's active
    const closeBtn = document.getElementById('modalCloseButton');
    if (closeBtn) {
        closeBtn.onclick = () => modal.close();
    }

    // 5. FIX: Re-bind the Save Button
    // Cloning the button removes all OLD event listeners from previous popups
    const newSaveBtn = saveBtn.cloneNode(true);

    // To this (safety check):
    if (saveBtn) {
        const newSaveBtn = saveBtn.cloneNode(true);
        saveBtn.parentNode.replaceChild(newSaveBtn, saveBtn);
        newSaveBtn.onclick = function() {
            console.log("Saving restaurant: " + element.dataset.name);
            
            const formData = new FormData();
            formData.append('name', element.dataset.name);
            formData.append('link', element.dataset.link);
            formData.append('rating', element.dataset.rating);
            formData.append('short_desc', element.dataset.shortDesc);
            formData.append('long_desc', element.dataset.longDesc);
            formData.append('station', element.dataset.station);
            formData.append('closed_on', element.dataset.closedOn);
            formData.append('fee', element.dataset.fee);
            formData.append('main_pic', element.dataset.mainPic);
            formData.append('open_hours', hiddenHours ? hiddenHours.innerHTML : "");
            formData.append('time', element.dataset.travelTime);

            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        console.log("Sending fetch request to /analysis/save_restaurant/..."); // NEW CHECKPOINT

        fetch("/analysis/save_restaurant/", { 
            method: 'POST',
            body: formData,
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(response => {
            console.log("Response received with status:", response.status); // NEW CHECKPOINT
            return response.json();
        })
        .then(data => {
            console.log("Data returned from server:", data); // NEW CHECKPOINT
            saveMsg.textContent = data.message;
            saveMsg.style.display = 'inline';
        })
        .catch(err => {
            console.error("CRITICAL FETCH ERROR:", err); // THIS WILL SHOW WHY IT FAILED
        });
    };
        // 6. Final step: display the popup
        modal.showModal();
    };

/* --- Global Search Form Logic --- */
document.addEventListener('DOMContentLoaded', function() {
    const searchBtn = document.getElementById('searchbutton');
    if (!searchBtn) return;

    const tokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
    const token = tokenEl ? tokenEl.value : "";
    const spinner = document.getElementById('spinner');
    const buttontext = document.getElementById('buttontext');

    function sendSearchData() {
        const checkedBoxes = document.querySelectorAll('input[name="additions"]:checked');
        const selectedAdditions = Array.from(checkedBoxes).map(cb => cb.value);

        const data = {
            amount: document.getElementById('amount').value,
            specialty: document.querySelector('input[name="specialty"]:checked')?.value || '',
            additions: selectedAdditions,
            sorting: document.querySelector('input[name="sorting"]:checked')?.value || '',
            address: document.getElementById('address').value,
            day: document.getElementById('day-select').value,
        };

        // UI Feedback during request
        searchBtn.disabled = true;
        if (buttontext) buttontext.style.display = 'none';
        if (spinner) spinner.style.display = 'inline';

        fetch('/analysis/rest_search/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token,
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            }
        })
        .catch(error => console.error("Search Error:", error))
        .finally(() => {
            searchBtn.disabled = false;
            if (buttontext) buttontext.style.display = 'inline';
            if (spinner) spinner.style.display = 'none';
        });
    }

    searchBtn.addEventListener('click', sendSearchData);
});
}
