/* 



*/

alert("JS is alive!");

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

document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('searchbutton'); // Ensure your HTML button ID is 'button'
    if (btn) {
        btn.addEventListener('click', sendData);
        console.log("EventListener attached to the button!");
    }
});