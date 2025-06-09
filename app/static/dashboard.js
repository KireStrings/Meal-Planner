    const macrosByDiet = {
      "Anything": { minCarbs: 90, minFat: 40, minProtein: 90 },
      "Keto": { minCarbs: 0, maxCarbs: 41, minFat: 120, minProtein: 68 },
      "Mediterranean": { minCarbs: 45, minFat: 40, minProtein: 45 },
      "Paleo": { minCarbs: 45, minFat: 40, minProtein: 45 },
      "Vegan": { minCarbs: 45, minFat: 40, minProtein: 45 },
      "Vegetarian": { minCarbs: 45, minFat: 40, minProtein: 45 }
    };

    let selectedDiet = "Anything";

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

      // Generate click handler
      document.querySelector(".generate-btn").addEventListener("click", async () => {
        const calories = document.querySelector("input[name='calories']").value;
        const meals = parseInt(document.querySelector("select[name='meals']").value);
        const health = document.querySelector('input[name="health"]:checked').value;
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
        const resultsContainer = document.getElementById("recipe-results");
        resultsContainer.innerHTML = "";

        const makeSection = (title, recipes) => {
          const section = document.createElement("div");
          section.className = "meal-section";
          section.innerHTML = `<h3>${title} <span class="refresh-btn" title="Refresh">🔄</span></h3>`;

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
                  <span>1 serving</span>
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
          const section = makeSection(title, data[mealKey]);
          if (section) resultsContainer.appendChild(section);
        });
      });
    });