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

    if (modal) {
        // наполняют консты выше, которые эту инфу кладут в попап
        name.textContent = element.dataset.name || "Японский Дракон";
        rating.textContent = (element.dataset.rating || "3") + " / 4";
        shortDesc.textContent = element.dataset.shortDesc || "просто ресторан нечего сказать абсолютно";
        longDesc.textContent = element.dataset.longDesc || "просто ресторан нечего сказать абсолютно";
        time.textContent = (element.dataset.time || "30") + " минут в пути";
        station.textContent = element.dataset.station || "левая станция";
        openHours.textContent = element.dataset.openHours || "открыт всегда";
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

