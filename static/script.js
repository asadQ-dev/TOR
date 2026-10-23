const playerDialog = document.getElementById("player-dialog");
const playerName = document.getElementById("player-name");
const playerIdentityName = document.getElementById("player-identity-name");
const closeButton = playerDialog.querySelector(".dialog-close");
const playerDetails = document.getElementById("player-details");
const playerStatus = document.getElementById("player-dialog-note");
const retryButton = document.getElementById("player-retry");
let activeRequest;
let selectedPlayer;

const metricFields = [
    {key: "tor", id: "player-tor", digits: 2, unit: ""},
    {key: "avg_ev", id: "avg-ev", digits: 1, unit: " mph"},
    {key: "max_ev", id: "max-ev", digits: 1, unit: " mph"},
    {key: "avg_bs", id: "avg-bs", digits: 1, unit: " mph"},
    {key: "max_bs", id: "max-bs", digits: 1, unit: " mph"},
    {key: "hard_hits", id: "hard-hits", digits: 0, unit: ""},
    {key: "hard_hit_rate", id: "hard-hit-rate", digits: 1, unit: "%", scale: 100},
];

async function loadPlayerDetails(name) {
    activeRequest?.abort();
    const controller = new AbortController();
    activeRequest = controller;
    playerDetails.hidden = true;
    retryButton.hidden = true;
    playerDetails.setAttribute("aria-busy", "true");
    playerStatus.textContent = "Loading player metrics...";

    try {
        const response = await fetch(`/api/player/${encodeURIComponent(name)}`, {
            signal: controller.signal,
        });
        if (!response.ok) {
            throw new Error(`Player request failed (HTTP ${response.status}).`);
        }
        const data = await response.json();
        if (activeRequest !== controller) return;
        if (!data || data.player !== name || data.error) {
            throw new Error("The server did not return details for this player.");
        }
        for (const field of metricFields) {
            const value = data[field.key];
            if (value !== null && (typeof value !== "number" || !Number.isFinite(value))) {
                throw new Error(`Invalid metric returned by server: ${field.key}`);
            }
        }
        for (const field of metricFields) {
            const value = data[field.key];
            document.getElementById(field.id).textContent = value === null
                ? "Unavailable"
                : (value * (field.scale ?? 1)).toFixed(field.digits) + field.unit;
        }
        playerStatus.textContent = "Player metrics loaded.";
        playerDetails.hidden = false;
    } catch (error) {
        if (controller.signal.aborted || activeRequest !== controller) return;
        console.error("Unable to load player details:", error);
        playerStatus.textContent = "Unable to load player metrics. Please try again.";
        retryButton.hidden = false;
    } finally {
        if (activeRequest === controller) {
            playerDetails.setAttribute("aria-busy", "false");
        }
    }
}

document.querySelectorAll(".player-button").forEach((button) => {
    button.addEventListener("click", () => {
        playerName.textContent = button.dataset.player;
        playerIdentityName.textContent = button.dataset.player;
        selectedPlayer = button.dataset.player;
        playerDialog.showModal();
        loadPlayerDetails(selectedPlayer);
    });
});

closeButton.addEventListener("click", () => {
    playerDialog.close();
});

retryButton.addEventListener("click", () => loadPlayerDetails(selectedPlayer));

playerDialog.addEventListener("close", () => {
    if (playerDialog.open) return;
    activeRequest?.abort();
    activeRequest = undefined;
});
