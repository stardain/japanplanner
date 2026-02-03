window.openDetails = function(element) {
    const modal = document.getElementById('restaurantModal');
    const name = document.getElementById('modalRestName');
    const rating = document.getElementById('modalRating');
    const specialty = document.getElementById('modalSpecialty');
    const openhours = document.getElementById('modalOpenHours');
    const station = document.getElementById('modalStation');
    const time = document.getElementById('modalTime');
    const desc = document.getElementById('modalDescription');
    const image = document.getElementById('modalImage');

    if (modal) {
        // наполняют консты выше, которые эту инфу кладут в попап
        name.textContent = element.dataset.name || "Японский Дракон";
        time.textContent = (element.dataset.time || "30") + " минут в пути";
        rating.textContent = (element.dataset.rating || "3") + " / 4";
        specialty.textContent = element.dataset.specialty || "хорош во всём";
        openhours.textContent = element.dataset.openhours || "открыт всегда";
        station.textContent = element.dataset.station || "центр токио хз что за станция";
        desc.textContent = element.dataset.desc || "просто ресторан нечего сказать абсолютно";
        image.src = element.dataset.image;

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