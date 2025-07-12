document.addEventListener('DOMContentLoaded', function() {
    const sortSelect = document.getElementById('sortRecipesBy');
    console.log(sortSelect);
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const selectedValue = this.value;
            const url = new URL(window.location.href);
            url.searchParams.set('sort', selectedValue);
            window.location.href = url.toString();
        });
    }
});