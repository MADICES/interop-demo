document.getElementById("sampleSelect").addEventListener("change", () => {
  const select = document.getElementById("sampleSelect");
  const button = select.nextElementSibling;
  button.disabled = !select.value;
});

function fetchData() {
  fetch("/data")
    .then((response) => response.json())
    .then((data) => {
      updateTable(data);
      populateTypes(data);
      populateExportSamples(data);
      populateSelectSimulation(data);
    })
    .catch((error) => {
      console.error("Error:", error);
      handleError("Failed to fetch data.");
    });
}

function populateSelectSimulation(data) {
  const samplesList = data.filter((item) => item.type.includes("Sample"));
  const select = document.getElementById("sampleSelect");
  select.nextElementSibling.disabled = true;
  select.innerHTML = "";
  const option = document.createElement("option");
  option.value = "";
  option.textContent = "Select a sample";
  select.appendChild(option);
  samplesList.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id; // Store item as a string in the value
    option.textContent = item.id + " - " + item.title;
    select.appendChild(option);
  });
}

function runSimulation() {
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
