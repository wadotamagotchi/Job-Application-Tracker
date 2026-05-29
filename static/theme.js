(function () {
    const storageKey = "job-tracker-theme";
    const toggle = document.querySelector("[data-theme-toggle]");
    const label = document.querySelector("[data-theme-label]");

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;

        if (label) {
            label.textContent = theme === "dark" ? "Light" : "Dark";
        }

        if (toggle) {
            toggle.setAttribute("aria-pressed", theme === "dark");
        }
    }

    const savedTheme = localStorage.getItem(storageKey);
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme = savedTheme || (prefersDark ? "dark" : "light");

    applyTheme(initialTheme);

    if (toggle) {
        toggle.addEventListener("click", function () {
            const currentTheme = document.documentElement.dataset.theme || "light";
            const nextTheme = currentTheme === "dark" ? "light" : "dark";

            localStorage.setItem(storageKey, nextTheme);
            applyTheme(nextTheme);
        });
    }
})();
