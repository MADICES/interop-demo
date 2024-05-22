function fetchData() {
  fetch("/data")
    .then((response) => response.json())
    .then((data) => {
      updateTable(data);
      populateTypes(data);
      populateSelectSimulation(data);
    })
    .catch((error) => handleError("Failed to fetch data."));
}

function populateSelectSimulation(data) {
  const samplesList = data.filter((item) => item.type.includes("Sample"));
  const sampleSelect = document.getElementById("sampleSelect");
  sampleSelect.innerHTML = "";
  const option = document.createElement("option");
  option.value = "";
  option.textContent = "Select a sample";
  sampleSelect.appendChild(option);
  samplesList.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id; // Store item as a string in the value
    option.textContent = item.id + " - " + item.title;
    sampleSelect.appendChild(option);
  });
}

function startSimulation() {
  const selectedObjectId = document.getElementById("sampleSelect").value;

  if (!selectedObjectId) {
    alert("Please select an object to link with the simulation.");
    return;
  }

  fetch(`/data/start_simulation?id=${encodeURIComponent(selectedObjectId)}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error("Failed to start simulation.");
      }
    })
    .then((response) => {
      fetchData();
      displayNewObject(response);
    })
    .catch((error) => {
      handleError("Failed to fetch or process data.");
    });
}

function displayNewObject(newObject) {
  const displayArea = document.getElementById("sim_message");
  displayArea.classList.remove("d-none");
  displayArea.textContent =
    "Updated Object with new simulation: " + JSON.stringify(newObject, null, 2);

  let exportButton = document.getElementById("exportButton");
  if (!exportButton) {
    exportButton = document.createElement("button");
    exportButton.id = "exportButton";
    exportButton.textContent = "Export Data";
    exportButton.className = "btn btn-success mt-3";
    exportButton.onclick = () => exportData(newObject);
    displayArea.parentNode.insertBefore(exportButton, displayArea.nextSibling);
  }
}

function exportData(newObject) {
  fetch("/api/export", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(newObject),
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error("Failed to export data.");
      }
    })
    .then((data) => alert("Successfully exported data."))
    .catch((error) => {
      console.error("Error:", error);
      alert("An error occurred during data export.");
    });
}
