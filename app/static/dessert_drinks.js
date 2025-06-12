document.getElementById("generateExtras").addEventListener("click", async () => {
    const types = [...document.querySelectorAll("input[name='extraType']:checked")].map(cb => cb.value);
    const maxDessert = document.getElementById("maxDessertCalories").value;
    const maxDrink = document.getElementById("maxDrinkCalories").value;
    const number = document.getElementById("numResults").value;

    const response = await fetch("/extras", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        types,
        maxDessertCalories: parseInt(maxDessert),
        maxDrinkCalories: parseInt(maxDrink),
        number: parseInt(number)
    })
    });

    const data = await response.json();
    const resultsDiv = document.getElementById("extrasResults");
    resultsDiv.innerHTML = "";

    types.forEach(type => {
    const section = document.createElement("div");
    section.className = "result-section";
    section.innerHTML = `<h3>${type[0].toUpperCase() + type.slice(1)}s</h3>`;

    const items = data[type] || [];
    if (items.length === 0) {
        section.innerHTML += `<p style="color:red;">No ${type}s found within calorie limit.</p>`;
    } else {
        items.forEach(recipe => {
        section.innerHTML += `
            <div class="result-item">
            <img src="${recipe.image}" alt="${recipe.title}">
            <div>
                <a href="${recipe.sourceUrl}" target="_blank">${recipe.title}</a><br>
                <span>Calories: ${Math.round(
                recipe.nutrition?.nutrients?.find(n => n.name === "Calories")?.amount || 0
                )}</span>
            </div>
            </div>
        `;
        });
    }
    resultsDiv.appendChild(section);
    });
});