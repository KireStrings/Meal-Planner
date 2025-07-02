document.addEventListener('DOMContentLoaded', function() {
    /**
     *
     * @param input {HTMLInputElement}
     * @param getSuggestions {(query: string) => Promise<string[]> | string[]}
     * @param minCharacters {number} Minimum number of characters to trigger suggestions
     */
    function initAutoComplete(input, getSuggestions, minCharacters = 2) {
        function addSuggestionsToInput(input, data) {
            suggestionBox.innerHTML = '';
            data.forEach(item => {
                const div = document.createElement('div');
                div.textContent = item.name ?? item;
                div.onclick = function () {
                    let parts = input.value.split(',').map(part => part.trim());
                    parts[parts.length - 1] = item.name ?? item;
                    input.value = parts.join(', ');
                    suggestionBox.innerHTML = '';
                    suggestionBox.style.display = 'none';
                };
                suggestionBox.appendChild(div);
            });
            suggestionBox.style.display = data.length ? 'block' : 'none';
        }

        const suggestionBox = document.createElement('div');
        suggestionBox.className = 'autocomplete-suggestions';
        suggestionBox.style.display = 'none';
        input.parentNode.appendChild(suggestionBox);


        input.addEventListener('input', function() {
            const query = input.value.split(',').pop().trim();
            if (query.length < minCharacters) {
                suggestionBox.innerHTML = '';
                suggestionBox.style.display = 'none';
                return;
            }
            let suggestions = getSuggestions(query);
            if (suggestions instanceof Promise) {
                console.log('suggestions: ', suggestions);
                suggestions.then(data => {
                    console.log('data: ', data);
                    addSuggestionsToInput(input, data);
                });
            } else {
                addSuggestionsToInput(input, suggestions);
            }
        });

        document.addEventListener('click', function(e) {
            if (!suggestionBox.contains(e.target) && e.target !== input) {
                suggestionBox.innerHTML = '';
                suggestionBox.style.display = 'none';
            }
        });
    }

    const ingredientsInput = document.querySelector('input[name="includeIngredients"]');
    initAutoComplete(ingredientsInput, function(query) {
        return fetch(`/autocomplete?q=${encodeURIComponent(query)}`)
            .then(async response => (await response.json()).results)
    });
    const notIngredientsInput = document.querySelector('input[name="excludeIngredients"]');
    initAutoComplete(notIngredientsInput, function(query) {
        return fetch(`/autocomplete?q=${encodeURIComponent(query)}`)
            .then(async response => (await response.json()).results)
    });

    const cuisineInput = document.querySelector('input[name="cuisine"]');
    initAutoComplete(cuisineInput, function(query) {
        const cuisineSuggestions = [
            'African', 'Asian', 'American', 'British', 'Cajun', 'Caribbean', 'Chinese', 'Eastern European', 'European',
            'French', 'German', 'Greek', 'Indian', 'Irish', 'Italian', 'Japanese', 'Jewish', 'Korean',
            'Latin American', 'Mediterranean', 'Mexican', 'Middle Eastern', 'Nordic', 'Southern', 'Spanish', 'Thai', 'Vietnamese'
        ];
        return cuisineSuggestions.filter(c => c.toLowerCase().includes(query.toLowerCase()));
    }, 0);

    const intoleranceInput = document.querySelector('input[name="intolerances"]');
    initAutoComplete(intoleranceInput, function(query) {
        const intoleranceSuggestions = [
            'Dairy', 'Egg', 'Gluten', 'Grain',
            'Peanut', 'Seafood', 'Sesame', 'Shellfish',
            'Soy', 'Sulfite', 'Tree Nut', 'Wheat'
        ];
        return intoleranceSuggestions.filter(c => c.toLowerCase().includes(query.toLowerCase()));
    }, 0);
});