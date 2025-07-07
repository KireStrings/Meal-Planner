const macrosByDiet = {
  "Anything": { minCarbs: 90, minFat: 40, minProtein: 90 },
  "Keto": { minCarbs: 0, maxCarbs: 41, minFat: 120, minProtein: 68 },
  "Mediterranean": { minCarbs: 45, minFat: 40, minProtein: 45 },
  "Paleo": { minCarbs: 45, minFat: 40, minProtein: 45 },
  "Vegan": { minCarbs: 45, minFat: 40, minProtein: 45 },
  "Vegetarian": { minCarbs: 45, minFat: 40, minProtein: 45 }
};

let selectedDiet = "Anything";
let latestMealPlan = {}; // Store the last generated meal plan for saving

document.addEventListener("DOMContentLoaded", function () {
  const buttons = document.querySelectorAll(".diet");

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      selectedDiet = btn.innerText;
      const macros = macrosByDiet[selectedDiet];
      document.getElementById("carbs-val").innerText = macros.minCarbs + (macros.maxCarbs ? ` (max: ${macros.maxCarbs})` : "");
      document.getElementById("fat-val").innerText = macros.minFat;
      document.getElementById("protein-val").innerText = macros.minProtein;
    });
  });

  document.querySelector(".generate-btn").addEventListener("click", async () => {
    const calories = document.querySelector("input[name='calories']").value;
    const meals = parseInt(document.querySelector("select[name='meals']").value);
    const health = document.querySelector('input[name="health"]:checked')?.value || "balanced";
    const macros = macrosByDiet[selectedDiet];

    const res = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        diet: selectedDiet,
        calories,
        meals,
        minCarbs: macros.minCarbs,
        minFat: macros.minFat,
        minProtein: macros.minProtein,
        maxCarbs: macros.maxCarbs || null,
        healthPreference: health
      })
    });

    const data = await res.json();
    latestMealPlan = data; // Save the plan for saving later
    const resultsContainer = document.getElementById("recipe-results");
    resultsContainer.innerHTML = "";

    const makeSection = (title, recipes, mealKey) => {
      const section = document.createElement("div");
      section.className = "meal-section";
      section.innerHTML = `<h3>${title}</h3>`;

      if (!recipes || recipes.length === 0 || recipes.error) {
        section.innerHTML += `<p style="color: red;">No suitable ${title} recipe found for your preferences.</p>`;
        return section;
      }

      const totalCalories = recipes.reduce((sum, r) => {
        const cals = r.nutrition?.nutrients?.find(n => n.name === "Calories")?.amount || 0;
        return sum + cals;
      }, 0);

      section.innerHTML += `<span>~ ${Math.round(totalCalories)} Calories</span><br><br>`;

      recipes.forEach(r => {
        section.innerHTML += `
          <div class="meal-item">
            <img src="${r.image}" alt="${r.title}">
            <div>
              <a href="${r.sourceUrl}" target="_blank">${r.title}</a><br>
              <span>1 serving</span><br>
              <button class="save-recipe-btn" data-recipe='${JSON.stringify({
                id: r.id,
                title: r.title,
                image: r.image,
                sourceUrl: r.sourceUrl,
                nutrition: r.nutrition || null
              })}'>💾 Save</button>
            </div>
          </div>
        `;
      });

      return section;
    };

    const mealKeys = Object.keys(data);
    if (mealKeys.length === 0) {
      resultsContainer.innerHTML = "<p>No meals found.</p>";
      return;
    }

    mealKeys.forEach(mealKey => {
      const title = mealKey.charAt(0).toUpperCase() + mealKey.slice(1);
      const section = makeSection(title, data[mealKey], mealKey);
      if (section) resultsContainer.appendChild(section);
    });

    // Add "Save Meal Plan" button
    const savePlanBtn = document.createElement("button");
    savePlanBtn.textContent = "💾 Save Meal Plan";
    savePlanBtn.className = "save-mealplan-btn";
    savePlanBtn.style.marginTop = "20px";
    resultsContainer.appendChild(savePlanBtn);
  });

  // Delegate button clicks
  document.getElementById("recipe-results").addEventListener("click", async (e) => {
    // Save individual recipe
    if (e.target.classList.contains("save-recipe-btn")) {
      const recipeData = JSON.parse(e.target.dataset.recipe);

      try {
        const saveRes = await fetch("/save_recipe", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(recipeData)
        });

        if (saveRes.ok) {
          e.target.textContent = "Saved!";
          e.target.disabled = true;
        } else {
          const errorData = await saveRes.json();
          alert(`Failed to save recipe: ${errorData.error || "Unknown error"}`);
        }
      } catch (err) {
        console.error("Error saving recipe:", err);
        alert("An error occurred while saving the recipe.");
      }
    }

    // Save entire meal plan
    if (e.target.classList.contains("save-mealplan-btn")) {
      try {
        const planTitle = prompt("Enter a title for this meal plan:");
        if (!planTitle) return;

        const response = await fetch("/save_mealplan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: planTitle,
            plan: latestMealPlan
          })
        });

        if (response.ok) {
          e.target.textContent = "Meal Plan Saved!";
          e.target.disabled = true;
        } else {
          const errorData = await response.json();
          alert(`Failed to save meal plan: ${errorData.error || "Unknown error"}`);
        }
      } catch (err) {
        console.error("Error saving meal plan:", err);
        alert("An error occurred while saving the meal plan.");
      }
    }
  });
});
