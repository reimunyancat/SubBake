const VIDEO_EXTS = [".mkv", ".mp4", ".webm"];
const SUB_EXTS = [".smi", ".srt", ".ass", ".ssa", ".vtt", ".sup"];

const drop = document.getElementById("drop");
const picker = document.getElementById("picker");
const picked = document.getElementById("picked");
const startBtn = document.getElementById("start");
const fill = document.getElementById("fill");
const statusEl = document.getElementById("status");
const downloadEl = document.getElementById("download");
const footer = document.getElementById("footer");

let videoFile = null;
let subFile = null;
let polling = null;

function extOf(name) {
  const i = name.lastIndexOf(".");
  return i < 0 ? "" : name.slice(i).toLowerCase();
}

function accept(files) {
  for (const file of files) {
    const ext = extOf(file.name);
    if (VIDEO_EXTS.includes(ext)) videoFile = file;
    else if (SUB_EXTS.includes(ext)) subFile = file;
  }
  const left = videoFile ? videoFile.name : "no video";
  const right = subFile ? subFile.name : "no subtitle";
  picked.textContent = `${left}  +  ${right}`;
  statusEl.textContent =
    videoFile && subFile ? "Ready" : "Pick one video and one subtitle file";
}

drop.addEventListener("click", () => picker.click());
picker.addEventListener("change", (e) => accept(e.target.files));

["dragenter", "dragover"].forEach((ev) =>
  drop.addEventListener(ev, (e) => {
    e.preventDefault();
    drop.classList.add("hover");
  }),
);

["dragleave", "drop"].forEach((ev) =>
  drop.addEventListener(ev, (e) => {
    e.preventDefault();
    drop.classList.remove("hover");
  }),
);

drop.addEventListener("drop", (e) => accept(e.dataTransfer.files));

function stopPolling() {
  if (polling) {
    clearInterval(polling);
    polling = null;
  }
}

function watch(jobId) {
  polling = setInterval(async () => {
    const res = await fetch(`api/jobs/${jobId}`);
    if (!res.ok) {
      stopPolling();
      statusEl.textContent = "The job expired.";
      startBtn.disabled = false;
      return;
    }
    const job = await res.json();
    fill.style.width = `${Math.round(job.progress * 100)}%`;
    statusEl.textContent = job.message;
    if (job.status === "done") {
      stopPolling();
      downloadEl.href = `api/jobs/${jobId}/download`;
      downloadEl.hidden = false;
      startBtn.disabled = false;
    } else if (job.status === "failed") {
      stopPolling();
      statusEl.textContent = `Failed: ${job.error || "unknown error"}`;
      startBtn.disabled = false;
    }
  }, 700);
}

startBtn.addEventListener("click", async () => {
  if (!videoFile || !subFile) {
    statusEl.textContent = "Pick one video and one subtitle file first.";
    return;
  }
  stopPolling();
  downloadEl.hidden = true;
  fill.style.width = "0%";
  startBtn.disabled = true;
  statusEl.textContent = "Uploading...";

  const body = new FormData();
  body.append("video", videoFile);
  body.append("subtitle", subFile);
  body.append("language", document.getElementById("language").value);
  body.append("offset_ms", document.getElementById("offset").value || "0");
  body.append(
    "set_default",
    document.getElementById("setDefault").checked ? "true" : "false",
  );

  const res = await fetch("api/jobs", { method: "POST", body });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    statusEl.textContent = `Failed: ${detail.detail || res.status}`;
    startBtn.disabled = false;
    return;
  }
  const data = await res.json();
  statusEl.textContent = "Queued";
  watch(data.jobId);
});

fetch("api/health")
  .then((r) => r.json())
  .then((info) => {
    if (info.ok) {
      footer.textContent = `${info.ffmpeg} · max ${info.maxUploadMb}MB · files are deleted automatically`;
    } else {
      footer.textContent = "FFmpeg is unavailable on the server.";
      startBtn.disabled = true;
    }
  })
  .catch(() => {});
