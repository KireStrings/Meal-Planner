document.addEventListener("DOMContentLoaded", () => {
  const removeButtons = document.querySelectorAll(".remove-plan-btn");
  const renameButtons = document.querySelectorAll(".rename-plan-btn");

  // Remove meal plan logic
  removeButtons.forEach(button => {
    button.addEventListener("click", async () => {
      const planId = button.getAttribute("data-plan-id");
      const planTitle = button.getAttribute("data-plan-title");

      const confirmed = confirm(`Are you sure you want to remove "${planTitle}"?`);
      if (!confirmed) return;

      try {
        const response = await fetch(`/unsave_plan/${planId}`, {
          method: "DELETE",
        });

        if (response.ok) {
          alert(`✅ "${planTitle}" removed successfully.`);
          // Remove the meal plan card from the DOM
          button.closest(".card").remove();
        } else {
          const error = await response.json();
          alert("❌ Failed to remove meal plan: " + (error.error || "Unknown error."));
        }
      } catch (err) {
        console.error("Error removing meal plan:", err);
        alert("❌ An error occurred while removing the meal plan.");
      }
    });
  });

  // Rename meal plan logic
  renameButtons.forEach(button => {
    button.addEventListener("click", async () => {
      const planId = button.getAttribute("data-plan-id");
      const oldTitle = button.getAttribute("data-plan-title");

      const newTitle = prompt(`Rename "${oldTitle}" to:`, oldTitle);
      if (newTitle === null) return; // Cancelled
      if (newTitle.trim() === "") {
        alert("❌ Meal plan name cannot be empty.");
        return;
      }
      if (newTitle.trim() === oldTitle.trim()) {
        alert("⚠️ New name is the same as the old name.");
        return;
      }

      try {
        const response = await fetch(`/rename_plan/${planId}`, {
          method: "POST",  // or PUT depending on your backend
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ title: newTitle.trim() })
        });

        if (response.ok) {
          alert(`✅ Meal plan renamed to "${newTitle.trim()}" successfully.`);

          // Update UI: change button data attribute and title text
          button.setAttribute("data-plan-title", newTitle.trim());

          // Find the card header span with class 'mealplan-title' and update text
          const cardHeader = button.closest(".card-header");
          const titleSpan = cardHeader.querySelector(".mealplan-title");
          if (titleSpan) {
            titleSpan.textContent = newTitle.trim();
          }
        } else {
          const error = await response.json();
          alert("❌ Failed to rename meal plan: " + (error.error || "Unknown error."));
        }
      } catch (err) {
        console.error("Error renaming meal plan:", err);
        alert("❌ An error occurred while renaming the meal plan.");
      }
    });
  });
});
