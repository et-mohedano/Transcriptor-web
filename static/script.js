document.getElementById("uploadForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const fileInput = document.getElementById("video");
  if (!fileInput.files.length) return alert("Selecciona un video.");

  const formData = new FormData();
  formData.append("video", fileInput.files[0]);

  const progressContainer = document.getElementById("progress-container");
  const progressBar = document.getElementById("progress");
  const statusText = document.getElementById("status-text");
  const resultDiv = document.getElementById("result");
  const transcriptionBox = document.getElementById("transcriptionBox");

  progressContainer.classList.remove("hidden");
  resultDiv.classList.add("hidden");
  progressBar.style.width = "0%";
  statusText.textContent = "📤 Subiendo video...";

  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
        return;
      }

      let progress = 10;
      progressBar.style.width = progress + "%";

      const interval = setInterval(() => {
        fetch("/progress")
          .then((r) => r.json())
          .then((progressData) => {
            statusText.textContent = progressData.message;

            if (progressData.status === "processing" && progress < 90) progress += 10;
            if (progressData.status === "done") progress = 100;
            progressBar.style.width = progress + "%";

            if (progressData.status === "done") {
              clearInterval(interval);
              statusText.textContent = "✅ Transcripción lista";
              resultDiv.classList.remove("hidden");

              // Cargar texto transcripto automáticamente
              fetch("/download")
                .then((r) => r.text())
                .then((text) => {
                  transcriptionBox.value = text;
                });
            }

            if (progressData.status === "error") {
              clearInterval(interval);
              statusText.textContent = progressData.message;
              progressBar.style.backgroundColor = "#dc3545";
            }
          });
      }, 1500);
    })
    .catch((err) => {
      alert("Error subiendo archivo: " + err);
    });
});

// Botón para copiar texto
document.getElementById("copyButton").addEventListener("click", () => {
  const textArea = document.getElementById("transcriptionBox");
  textArea.select();
  document.execCommand("copy");

  const btn = document.getElementById("copyButton");
  btn.textContent = "✅ Copiado!";
  btn.style.background = "#28a745";

  setTimeout(() => {
    btn.textContent = "📋 Copiar texto";
    btn.style.background = "#17a2b8";
  }, 1500);
});
