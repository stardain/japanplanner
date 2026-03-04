/* 



*/

window.openDetails = function(element) {
    const modal = document.getElementById('restaurantModal');
    const name = document.getElementById('modalRestName');
    const rating = document.getElementById('modalRating');
    const shortDesc = document.getElementById('modalShortDesc');
    const longDesc = document.getElementById('modalLongDesc');
    const time = document.getElementById('modalTime');
    const station = document.getElementById('modalStation');
    const openHours = document.getElementById('modalOpenHours');
    const closedOn = document.getElementById('modalClosedOn');
    const fee = document.getElementById('modalFee');
    const image = document.getElementById('modalImage');

    const card = element.closest('.restaurant-card');
    const hiddenHours = card.querySelector('.hidden-hours');

    if (hiddenHours) {
        // Copy the HTML from the card into the modal
        openHours.innerHTML = hiddenHours.innerHTML;
    } else {
        openHours.innerHTML = "<li>Information not available</li>";
    }

    if (modal) {
        // наполняют консты выше, которые эту инфу кладут в попап
        name.textContent = element.dataset.name || "Японский Дракон";
        rating.textContent = (element.dataset.rating || "3") + " / 4";
        shortDesc.textContent = element.dataset.shortDesc || "просто ресторан нечего сказать абсолютно";
        longDesc.textContent = element.dataset.longDesc || "просто ресторан нечего сказать абсолютно";
        time.textContent = (element.dataset.travelTime || "30") + " минут в пути";
        station.textContent = element.dataset.station || "левая станция";
        closedOn.textContent = element.dataset.closedOn || "закрыт всегда";
        fee.textContent = element.dataset.fee || "50 рублей на чаевые";
        image.src = element.dataset.mainPic;

        modal.showModal();
    } else {
        console.error("Popup elements missing from HTML!");
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('restaurantModal');
    const closeBtn = document.getElementById('modalCloseButton');
    if (closeBtn) {
        closeBtn.onclick = () => modal.close();
    }
});

//

document.addEventListener('DOMContentLoaded', function() {

const token = document.querySelector('[name=csrfmiddlewaretoken]').value;

function sendData() {
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

    searchbutton.disabled = true;
    buttontext.style.display = 'none';
    spinner.style.display = 'inline';

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
        console.log("Success:", data);
        if (data.redirect_url) {
            // This actually moves the user to the next page
            window.location.href = data.redirect_url;
        }
    })
    .catch(error => console.error("Error:", error))
    .finally(() => {
        // --- STEP B: RESET BUTTON (Happens on Success OR Error) ---
        searchbutton.disabled = false;
        buttontext.style.display = 'inline';
        spinner.style.display = 'none';
    });
}

    const btn = document.getElementById('searchbutton');
    if (btn) {
        searchbutton.addEventListener('click', sendData);
        console.log("EventListener attached!");
    } else {
        console.error("Button not found!");
    }

});