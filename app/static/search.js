document.addEventListener('DOMContentLoaded', function() {
    const input = document.querySelector('input[name="ingredients"]');
    const suggestionBox = document.createElement('div');
    suggestionBox.className = 'autocomplete-suggestions';
    suggestionBox.style.display = 'none';
    input.parentNode.appendChild(suggestionBox);

    input.addEventListener('input', function() {
        const query = input.value.split(',').pop().trim();
        if (query.length < 2) {
            suggestionBox.innerHTML = '';
            suggestionBox.style.display = 'none';
            return;
        }
        fetch(`/autocomplete?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                suggestionBox.innerHTML = '';
                data.results.forEach(item => {
                    const div = document.createElement('div');
                    div.textContent = item.name;
                    div.onclick = function() {
                        let parts = input.value.split(',').map(part => part.trim());
                        parts[parts.length - 1] = item.name;
                        input.value = parts.join(', ');
                        suggestionBox.innerHTML = '';
                        suggestionBox.style.display = 'none';
                    };
                    suggestionBox.appendChild(div);
                });
                suggestionBox.style.display = data.results.length ? 'block' : 'none';
            });
    });

    document.addEventListener('click', function(e) {
        if (!suggestionBox.contains(e.target) && e.target !== input) {
            suggestionBox.innerHTML = '';
            suggestionBox.style.display = 'none';
        }
    });
});