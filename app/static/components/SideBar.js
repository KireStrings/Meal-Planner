/** @type HTMLInputElement */
const searchInput = document.querySelector('.search-bar input[type="search"]');
if (searchInput) {
    searchInput.addEventListener('search', function () {
        const query = encodeURIComponent(searchInput.value.trim());
        if (query) {
            window.location.href = `/search?q=${query}`;
        }
    });
}
