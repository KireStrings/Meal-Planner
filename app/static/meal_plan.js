let weekOffset = 0;

function getWeekDates(offset = 0) {
  const today = new Date();
  const day = today.getDay(); // Sunday = 0
  const sunday = new Date(today);
  sunday.setDate(today.getDate() - day + offset * 7);
  return [...Array(7)].map((_, i) => {
    const date = new Date(sunday);
    date.setDate(sunday.getDate() + i);
    return date;
  });
}

function renderWeek() {
  const weekDates = getWeekDates(weekOffset);
  const grid = document.getElementById('meal-grid');
  grid.innerHTML = '';

  weekDates.forEach(date => {
    const cell = document.createElement('div');
    cell.className = 'meal-cell';
    cell.textContent = "Meal info";
    grid.appendChild(cell);
  });

  const start = weekDates[0];
  const end = weekDates[6];
  const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
  document.getElementById('date-range').textContent = 
    `${start.toLocaleDateString('en-GB', options)} - ${end.toLocaleDateString('en-GB', options)}`;
}

document.getElementById('prev-week').addEventListener('click', () => {
  weekOffset--;
  renderWeek();
});

document.getElementById('next-week').addEventListener('click', () => {
  weekOffset++;
  renderWeek();
});

renderWeek();
