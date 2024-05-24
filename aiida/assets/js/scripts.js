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

  fetch(`/data/run_simulation?id=${encodeURIComponent(selectedObjectId)}`, {
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
    })
    .catch((error) => {
      console.log(error);
      handleError("Failed to fetch or process data.");
    });
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
