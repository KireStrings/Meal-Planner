    document.addEventListener("DOMContentLoaded", function () {
      // Diet toggles
      const buttons = document.querySelectorAll(".diet");
      buttons.forEach(btn => {
        btn.addEventListener("click", () => {
          buttons.forEach(b => b.classList.remove("selected"));
          btn.classList.add("selected");
        });
      });

      // Success popup
      const popup = document.getElementById("successPopup");
      if (popup) {
        popup.style.display = "block";
        setTimeout(() => popup.style.display = "none", 3000);
      }

      // Generate click handler
      document.querySelector(".generate-btn").addEventListener("click", async () => {
        const selectedDiet = document.querySelector(".diet.selected").innerText;
        const calories     = document.querySelector("input[name='calories']").value;
        const meals        = document.querySelector("select[name='meals']").value;
        const minCarbs     = document.querySelector("input[name='minCarbs']").value;
        const minFat       = document.querySelector("input[name='minFat']").value;
        const minProtein   = document.querySelector("input[name='minProtein']").value;

        const res = await fetch("/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            diet:        selectedDiet,
            calories:    calories,
            meals:       meals,
            minCarbs:    minCarbs,
            minFat:      minFat,
            minProtein:  minProtein
          })
        });

        const data = await res.json();
        console.log("Received recipes:", data); 
        const resultsContainer = document.getElementById("recipe-results");
        resultsContainer.innerHTML = "";

        if (data.results && data.results.length) {
          data.results.forEach(recipe => {
            /* append recipe cards… */
          });
        } else {
          resultsContainer.innerHTML = "<p>No recipes found. Try different values.</p>";
        }
      });
    });