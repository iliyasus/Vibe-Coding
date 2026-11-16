(() => {
  const storageKey = "mineshield:favorites:v1";
  const status = document.querySelector("[data-favorites-status]");
  const buttons = [...document.querySelectorAll("[data-favorite-toggle]")];
  const favoriteCards = [...document.querySelectorAll("[data-favorite-player-card]")];
  const favoriteGrid = document.querySelector("[data-favorites-grid]");
  const emptyState = document.querySelector("[data-favorites-empty]");
  const noScriptNotice = document.querySelector("[data-favorites-no-script]");
  let favorites = new Set();
  let storageAvailable = true;

  function showStorageError(message) {
    status.textContent = message;
    status.hidden = false;
  }

  try {
    const saved = localStorage.getItem(storageKey);
    if (saved !== null) {
      const parsed = JSON.parse(saved);
      if (!Array.isArray(parsed) || parsed.some((id) => !Number.isSafeInteger(id) || id < 1)) {
        throw new Error("Некорректный формат избранного");
      }
      favorites = new Set(parsed);
    }
  } catch {
    storageAvailable = false;
    showStorageError("Не удалось прочитать избранное. Проверьте настройки хранения данных сайта в браузере.");
  }

  function updateButton(button) {
    const playerId = Number(button.dataset.favoriteToggle);
    const isFavorite = favorites.has(playerId);
    button.setAttribute("aria-pressed", String(isFavorite));
    button.setAttribute(
      "aria-label",
      `${isFavorite ? "Убрать из избранного" : "Добавить в избранное"}: ${button.dataset.playerName}`,
    );
    button.textContent = button.classList.contains("profile-favorite")
      ? `${isFavorite ? "★ Убрать из избранного" : "☆ Добавить в избранное"}`
      : isFavorite ? "★" : "☆";
    button.disabled = !storageAvailable;
  }

  function updatePage() {
    buttons.forEach(updateButton);
    document.querySelectorAll("[data-favorite-count]").forEach((counter) => {
      counter.textContent = String(favorites.size);
    });

    if (favoriteGrid && emptyState) {
      let visibleCount = 0;
      favoriteCards.forEach((card) => {
        card.hidden = !favorites.has(Number(card.dataset.favoritePlayerCard));
        if (!card.hidden) visibleCount += 1;
      });
      favoriteGrid.hidden = false;
      emptyState.hidden = visibleCount > 0;
    }

    if (noScriptNotice) noScriptNotice.hidden = true;
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const playerId = Number(button.dataset.favoriteToggle);
      if (favorites.has(playerId)) favorites.delete(playerId);
      else favorites.add(playerId);

      try {
        localStorage.setItem(storageKey, JSON.stringify([...favorites]));
        updatePage();
      } catch {
        if (favorites.has(playerId)) favorites.delete(playerId);
        else favorites.add(playerId);
        storageAvailable = false;
        showStorageError("Не удалось сохранить избранное. Проверьте настройки хранения данных сайта в браузере.");
        updatePage();
      }
    });
  });

  updatePage();
})();
