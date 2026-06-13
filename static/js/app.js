(function () {
  "use strict";

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");

  const progressSection = document.getElementById("progressSection");
  const progressFill = document.getElementById("progressFill");
  const progressPercent = document.getElementById("progressPercent");
  const progressFilename = document.getElementById("progressFilename");
  const progressStatus = document.getElementById("progressStatus");

  const errorBox = document.getElementById("errorBox");

  const resultBox = document.getElementById("resultBox");
  const resultFilename = document.getElementById("resultFilename");
  const resultType = document.getElementById("resultType");
  const strippedList = document.getElementById("strippedList");
  const downloadBtn = document.getElementById("downloadBtn");

  const historyBody = document.getElementById("historyBody");

  // --- Drag & drop / click-to-upload -------------------------------------

  ["dragenter", "dragover"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer && e.dataTransfer.files;
    if (files && files.length) {
      handleFile(files[0]);
    }
  });

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) {
      handleFile(fileInput.files[0]);
    }
    fileInput.value = "";
  });

  // --- Upload --------------------------------------------------------------

  function handleFile(file) {
    hideError();
    hideResult();
    uploadFile(file);
  }

  function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    progressSection.hidden = false;
    progressFilename.textContent = file.name;
    progressStatus.textContent = "uploading...";
    setProgress(0);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload");

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        setProgress(pct);
        if (pct >= 100) {
          progressStatus.textContent = "processing...";
        }
      }
    });

    xhr.onload = () => {
      let data = null;
      try {
        data = JSON.parse(xhr.responseText);
      } catch (err) {
        data = null;
      }

      if (xhr.status >= 200 && xhr.status < 300 && data) {
        setProgress(100);
        progressStatus.textContent = "done";
        showResult(data);
        loadHistory();
      } else {
        const message = (data && data.error) || `Upload failed (HTTP ${xhr.status})`;
        showError(message);
      }

      window.setTimeout(() => {
        progressSection.hidden = true;
      }, 500);
    };

    xhr.onerror = () => {
      showError("Network error during upload. Is the server running?");
      progressSection.hidden = true;
    };

    xhr.send(formData);
  }

  function setProgress(pct) {
    progressFill.style.width = pct + "%";
    progressPercent.textContent = pct + "%";
  }

  // --- Error / result display ----------------------------------------------

  function showError(message) {
    errorBox.textContent = "[error] " + message;
    errorBox.hidden = false;
  }

  function hideError() {
    errorBox.hidden = true;
    errorBox.textContent = "";
  }

  function hideResult() {
    resultBox.hidden = true;
    downloadBtn.hidden = true;
  }

  function showResult(data) {
    resultFilename.textContent = data.original_name || "-";
    resultType.textContent = data.file_type || "-";

    strippedList.innerHTML = "";
    const fields = data.stripped_fields || [];
    fields.forEach((field) => {
      const li = document.createElement("li");
      li.textContent = field;
      strippedList.appendChild(li);
    });

    if (data.download_url) {
      downloadBtn.href = data.download_url;
      downloadBtn.setAttribute("download", "");
      downloadBtn.hidden = false;
    } else {
      downloadBtn.hidden = true;
    }

    resultBox.hidden = false;
  }

  // --- History ---------------------------------------------------------------

  function loadHistory() {
    fetch("/history")
      .then((res) => {
        if (!res.ok) {
          throw new Error("failed to load history");
        }
        return res.json();
      })
      .then(renderHistory)
      .catch(() => {
        historyBody.innerHTML =
          '<tr><td colspan="5" class="empty-row">could not load history</td></tr>';
      });
  }

  function renderHistory(jobs) {
    historyBody.innerHTML = "";

    if (!jobs || !jobs.length) {
      historyBody.innerHTML =
        '<tr><td colspan="5" class="empty-row">no jobs yet</td></tr>';
      return;
    }

    jobs.forEach((job) => {
      const row = document.createElement("tr");

      const nameCell = document.createElement("td");
      nameCell.textContent = job.original_name || "-";
      nameCell.title = job.original_name || "";

      const typeCell = document.createElement("td");
      typeCell.textContent = job.file_type || "-";

      const strippedCell = document.createElement("td");
      if (job.status === "failed") {
        strippedCell.textContent = "failed";
        strippedCell.classList.add("status-failed");
      } else {
        strippedCell.textContent = String(job.stripped_count);
      }

      const timeCell = document.createElement("td");
      timeCell.textContent = formatTimestamp(job.timestamp);

      const actionCell = document.createElement("td");
      if (job.status === "completed") {
        const link = document.createElement("a");
        link.href = "/download/" + job.job_id;
        link.textContent = "download";
        link.className = "history-action";
        actionCell.appendChild(link);
      }

      const delBtn = document.createElement("button");
      delBtn.textContent = "delete";
      delBtn.className = "delete-btn";
      delBtn.title = "Delete this job and its files";
      delBtn.addEventListener("click", () => deleteJob(job.job_id));
      actionCell.appendChild(delBtn);

      row.appendChild(nameCell);
      row.appendChild(typeCell);
      row.appendChild(strippedCell);
      row.appendChild(timeCell);
      row.appendChild(actionCell);

      historyBody.appendChild(row);
    });
  }

  function formatTimestamp(ts) {
    if (!ts) return "-";
    const date = new Date(ts);
    if (isNaN(date.getTime())) return ts;
    return date.toLocaleString();
  }

  function deleteJob(jobId) {
    fetch("/job/" + jobId, { method: "DELETE" })
      .then((res) => {
        if (!res.ok) {
          throw new Error("failed to delete job");
        }
        return res.json();
      })
      .then(() => loadHistory())
      .catch(() => {
        showError("Could not delete job " + jobId);
      });
  }

  // --- Init --------------------------------------------------------------

  loadHistory();
})();
