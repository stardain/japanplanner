/* 
1. кнопка отправки
2. сохранения всех выборов в фильтрах + адреса

будущее -- кнопка сохранения
*/

const token = document.querySelector('[name=csrfmiddlewaretoken]').value;

const checkedBoxes = document.querySelectorAll('input[name="additions"]:checked');
const selectedAdditions = Array.from(checkedBoxes).map(cb => cb.value);

function sendData() {
    const data = {

        amount: document.getElementByID('amount').value,
        specialty: document.querySelector('input[name="specialty"]:checked')?.value || '',
        additions: selectedAdditions,
        sorting: document.querySelector('input[name="sorting"]:checked')?.value || '',
        address: document.getElementByID('address').value,
        day: document.getElementByID('day-select').value,

    };

    btn.disabled = true;
    btnText.style.display = 'none';
    spinner.style.display = 'inline';

    fetch('/rest_search/', {
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
        btn.disabled = false;
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    });
}