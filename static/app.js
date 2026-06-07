const spotifyUrl = document.getElementById("spotifyUrl");
const convertButton = document.getElementById("convertButton");
const status = document.getElementById("status");
const resultCard = document.getElementById("resultCard");
const artistLabel = document.getElementById("artist");
const trackLabel = document.getElementById("track");
const lyricsField = document.getElementById("lyrics");
const downloadLink = document.getElementById("downloadLink");

convertButton.addEventListener("click", async () => {
  const url = spotifyUrl.value.trim();
  if (!url) {
    status.textContent = "Please enter a Spotify track URL.";
    return;
  }

  status.textContent = "Processing conversion... this can take a minute.";
  resultCard.hidden = true;
  artistLabel.textContent = "";
  trackLabel.textContent = "";
  lyricsField.textContent = "";
  downloadLink.href = "#";

  try {
    const response = await fetch("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ spotify_url: url }),
    });

    const data = await response.json();
    if (!response.ok) {
      status.textContent = data.error || "Conversion failed.";
      return;
    }

    artistLabel.textContent = data.artist;
    trackLabel.textContent = data.track;
    lyricsField.textContent = data.lyrics || "No lyrics found.";
    downloadLink.href = data.download_url;
    downloadLink.textContent = "Download MP3";
    resultCard.hidden = false;
    status.textContent = "Conversion complete.";
  } catch (error) {
    status.textContent = `Error: ${error.message}`;
  }
});
