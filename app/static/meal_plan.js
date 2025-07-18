document.addEventListener("DOMContentLoaded", () => {
  const removeButtons = document.querySelectorAll(".remove-plan-btn");

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
});
