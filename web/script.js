document.addEventListener("DOMContentLoaded", () => {
  const plantButton = document.querySelector('.action.primary');
  const backButton = document.querySelector('.back-button');
  const actionsBlock = document.querySelector('.actions-block');
  const mainMenu = document.querySelector('.main-menu');
  const plantMenu = document.querySelector('.plant-menu');
  const title = document.querySelector('.actions-title');

  function showPlantMenu() {
    mainMenu.classList.add('hidden');
    plantMenu.classList.remove('hidden');
    backButton.classList.remove('hidden');
    title.textContent = 'Choose a Seed';
  }

  function showMainMenu() {
    mainMenu.classList.remove('hidden');
    plantMenu.classList.add('hidden');
    backButton.classList.add('hidden');
    title.textContent = 'Actions';
  }

  plantButton.addEventListener('click', showPlantMenu);
  backButton.addEventListener('click', showMainMenu);

  function renderHearts(vida) {
    const container = document.getElementById('hearts-container');
    container.innerHTML = '';

    const totalSlots = 16;

    for (let i = 0; i < totalSlots; i++) {
      const img = document.createElement('img');

      if (vida >= i + 1) {
        img.src = 'assets/full_h.svg';
      } else if (vida > i && vida < i + 1) {
        img.src = 'assets/half_h.svg';
      } else {
        img.src = 'assets/empty_h.svg';
      }

      img.alt = 'heart';
      container.appendChild(img);
    }
  }

  renderHearts(12.5);
});