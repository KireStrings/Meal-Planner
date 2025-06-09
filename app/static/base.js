// Success/Error/Warning popup
const popup = document.querySelectorAll(".flashes .popup");
if (popup) {
    for (const popupElement of popup) {
        popupElement.style.display = "block";
        setTimeout(() => popupElement.style.display = "", 3000);
    }
}