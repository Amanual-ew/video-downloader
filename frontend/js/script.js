const infoBtn = document.getElementById("infoBtn");
const videoUrl = document.getElementById("videoUrl");
const result = document.getElementById("result");


/* ==========================================
   GET VIDEO INFO
========================================== */

infoBtn.addEventListener("click", getVideoInfo);

async function getVideoInfo() {

    const url = videoUrl.value.trim();

    if (!url) {
        result.innerHTML = `<p class="error">Please paste a video URL.</p>`;
        return;
    }

    result.innerHTML = `<p class="status">🔄 Getting video information...</p>`;

    try {

        const response = await fetch("/video-info", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();

        if (!data.success) {
            result.innerHTML = `<p class="error">❌ ${data.error}</p>`;
            return;
        }

        let qualityOptions = `
            <option value="best">Best Quality</option>
        `;

        data.qualities.forEach(quality => {
            qualityOptions += `
                <option value="${quality}">${quality}p</option>
            `;
        });

        result.innerHTML = `
            <img src="${data.thumbnail}" alt="Video thumbnail">
            <h2>${data.title}</h2>
            <p>Duration: ${data.duration || "Unknown"} seconds</p>

            <div class="download-settings">
                <label>Video Quality</label>
                <select id="quality">${qualityOptions}</select>

                <label>File Name</label>
                <input type="text" id="filename" value="${data.title}">

                <button id="downloadBtn">Download Video</button>

                <div id="progressContainer" class="progress-container">
                    <div id="progressBar" class="progress-bar">0%</div>
                </div>

                <div id="downloadStatus" class="download-status">🟢 Ready</div>
                <div id="downloadDetails" class="download-details"></div>
            </div>
        `;

        document
            .getElementById("downloadBtn")
            .addEventListener("click", () => startDownload(url));

    } catch (error) {
        console.error(error);
        result.innerHTML = `<p class="error">❌ Could not connect to server.</p>`;
    }
}


/* ==========================================
   START DOWNLOAD
========================================== */

async function startDownload(url) {

    const quality = document.getElementById("quality").value;
    const filename = document.getElementById("filename").value.trim();

    const progressContainer = document.getElementById("progressContainer");
    const progressBar = document.getElementById("progressBar");
    const status = document.getElementById("downloadStatus");
    const button = document.getElementById("downloadBtn");

    if (!filename) {
        status.textContent = "❌ Please enter a file name.";
        return;
    }

    progressContainer.style.display = "block";
    progressBar.style.width = "0%";
    progressBar.textContent = "0%";

    button.disabled = true;
    status.textContent = "⏳ Starting download...";

    try {

        const response = await fetch("/start-download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                url: url,
                quality: quality,
                filename: filename
            })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error);
        }

        console.log("Download ID:", data.download_id);
        monitorProgress(data.download_id);

    } catch (error) {
        console.error(error);
        status.textContent = "❌ Download failed.";
        button.disabled = false;
    }
}


/* ==========================================
   MONITOR PROGRESS
========================================== */

async function monitorProgress(downloadId) {

    const progressBar = document.getElementById("progressBar");
    const status = document.getElementById("downloadStatus");
    const details = document.getElementById("downloadDetails");
    const button = document.getElementById("downloadBtn");

    try {

        const response = await fetch(`/download-progress/${downloadId}`);
        const data = await response.json();

        console.log("Progress:", data);

        const percent = Number(data.progress) || 0;
        progressBar.style.width = `${percent}%`;
        progressBar.textContent = `${percent}%`;

        if (data.status === "downloading") {
            status.textContent = "⬇️ Downloading...";
            details.textContent = `Speed: ${data.speed || "Calculating..."}`;
            setTimeout(() => monitorProgress(downloadId), 500);
            return;
        }

        if (data.status === "processing") {
            progressBar.style.width = "99%";
            progressBar.textContent = "99%";
            status.textContent = "⚙️ Processing video...";
            details.textContent = "Merging video and audio...";
            setTimeout(() => monitorProgress(downloadId), 500);
            return;
        }

        if (data.status === "completed") {
            progressBar.style.width = "100%";
            progressBar.textContent = "100%";
            status.textContent = "✅ Download completed!";
            details.textContent = "Preparing your file...";

            const link = document.createElement("a");
            link.href = `/download-file/${downloadId}`;
            link.download = data.filename;
            document.body.appendChild(link);
            link.click();
            link.remove();

            details.textContent = "✅ Video saved successfully.";
            button.disabled = false;
            return;
        }

        if (data.status === "error") {
            status.textContent = "❌ Download failed.";
            details.textContent = data.error;
            button.disabled = false;
            return;
        }

        status.textContent = "⏳ Preparing download...";
        setTimeout(() => monitorProgress(downloadId), 500);

    } catch (error) {
        console.error(error);
        status.textContent = "❌ Could not get download status.";
        button.disabled = false;
    }
}