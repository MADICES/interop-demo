document.addEventListener("DOMContentLoaded", () => {
  fetchPlatforms();
  fetchData();
});

document.getElementById("platformSelect").addEventListener("change", () => {
  const selectedPlatform = platformSelect.value;
  const connectButton = document.getElementById("connectButton");
  connectButton.disabled = !selectedPlatform;
  if (!selectedPlatform) {
    hideFilterSection();
    updatePlatformDataList([]);
  }
});

document.getElementById("platformTypeSelect").addEventListener("change", () => {
  const selectedType = platformTypeSelect.value;
  const fetchButton = document.getElementById("fetchButton");
  fetchButton.disabled = !selectedType;
  if (!selectedType) {
    updatePlatformDataList([]);
  }
});

function fetchPlatforms() {
  fetch("/platforms")
    .then((response) => response.json())
    .then((data) => {
      const platformSelect = document.getElementById("platformSelect");
      data.forEach((platform) => {
        const option = document.createElement("option");
        option.value = platform;
        option.textContent = platform;
        platformSelect.appendChild(option);
      });
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Failed to fetch RDM platforms.");
    });
}

function fetchPlatformTypes() {
  fetch("http://localhost:5002/data/types", {
    method: "GET",
    headers: {
      Accept: "application/zip",
    },
  })
    .then((response) => {
      if (response.ok) {
        return response.blob();
      }
      throw new Error("Network response was not ok.");
    })
    .then((blob) => {
      const jsZip = new JSZip();
      return jsZip.loadAsync(blob);
    })
    .then((zip) => {
      const filename = "response.json";
      if (filename in zip.files) {
        return zip.files[filename].async("string");
      }
      throw new Error("File not found in zip");
    })
    .then((jsonString) => {
      const data = JSON.parse(jsonString);
      updateTypeSelection(data);
      showFilterSection();
    })
    .catch((error) => {
      handleError("Failed to fetch or process data.");
    });
}

function updateTypeSelection(data) {
  const types = new Set(data);
  const platformTypeSelect = document.getElementById("platformTypeSelect");
  platformTypeSelect.innerHTML = '<option value="">Select a type</option>';
  types.forEach((type) => {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = type;
    platformTypeSelect.appendChild(option);
  });
}

function fetchPlatformData() {
  const selectedType = document.getElementById("platformTypeSelect").value;
  if (selectedType) {
    fetch(
      `http://localhost:5002/data/filter?type=${encodeURIComponent(
        selectedType
      )}&format=ROC`
    )
      .then((response) => response.json())
      .then((data) => {
        updatePlatformDataList(data);
      })
      .catch((error) => {
        handleError("Failed to fetch filtered data.");
      });
  } else {
    alert("Please select a type to filter by!");
  }
}

function updatePlatformDataList(data) {
  const list = document.getElementById("platformDataList");
  list.innerHTML = "";
  data.forEach((item) => {
    const li = document.createElement("li");
    li.className =
      "list-group-item d-flex justify-content-between align-items-center";
    const span = document.createElement("span");
    span.innerHTML = `
            <strong>ID:</strong> ${item.id}
            <strong>Ontology:</strong> ${item.ontology}
          `;
    li.appendChild(span);
    const button = document.createElement("button");
    button.className = "btn btn-outline-secondary btn-sm";
    button.textContent = "Import Data";
    button.onclick = () => {
      importData(item);
      // button.disabled = true;
    };
    li.appendChild(button);
    list.appendChild(li);
  });
}

function importData(item) {
  fetch("data/import", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(item),
  })
    .then((response) => {
      if (response.ok) {
        fetchData();
      } else {
        response.json().then((data) => {
          alert(data.message);
        });
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("An error occurred while importing data.");
    });
}

function fetchData() {
  fetch("/data")
    .then((response) => response.json())
    .then((data) => {
      updateTable(data);
      populateTypes(data);
    })
    .catch((error) => handleError("Failed to fetch data."));
}

function resetData() {
  fetch("/data/reset").then(
    () => {
      fetchData();
      hideError();
    },
    () => handleError("Failed to reset data.")
  );
}

function populateTypes(data) {
  const types = new Set(data.map((item) => item.ontology));
  const typeSelect = document.getElementById("typeSelect");
  typeSelect.innerHTML = '<option value="all">All</option>';
  types.forEach((type) => {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = type;
    typeSelect.appendChild(option);
  });
}

function fetchFilteredData() {
  const selectedType = document.getElementById("typeSelect").value;
  if (selectedType) {
    fetch(`/data/filter?type=${encodeURIComponent(selectedType)}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.length > 0) {
          updateTable(data);
          hideError();
        } else {
          handleError("No data found for the selected type.");
        }
      })
      .catch((error) => handleError("Failed to fetch filtered data."));
  } else {
    alert("Please select a type to filter by!");
  }
}

function updateTable(data) {
  const tableBody = document
    .getElementById("dataTable")
    .getElementsByTagName("tbody")[0];
  tableBody.innerHTML = "";
  data.forEach((item) => {
    const row = tableBody.insertRow();
    const cellId = row.insertCell(0);
    const cellType = row.insertCell(1);
    const cellTitle = row.insertCell(2);
    const cellOnt = row.insertCell(3);
    const cellMetadata = row.insertCell(4);
    cellId.textContent = item.id;
    cellType.textContent = item.type;
    cellTitle.textContent = item.title;
    cellOnt.textContent = item.ontology;
    cellMetadata.textContent = JSON.stringify(item.metadata);
  });
}

function uploadROCrate() {
  const formData = new FormData();
  const fileInput = document.getElementById("fileInput1");
  const resultDiv = document.getElementById("result1");

  if (fileInput.files.length > 0) {
    formData.append("file", fileInput.files[0]);

    fetch("/upload_rocrate", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        resultDiv.textContent = JSON.stringify(data, null, 2);
      })
      .catch((error) => {
        console.error("Error:", error);
        resultDiv.textContent = "Failed to upload and process the file.";
      });
  } else {
    resultDiv.textContent = "Please select a file to upload.";
  }
}

function showFilterSection() {
  const filterSection = document.getElementById("filterSection");
  filterSection.classList.remove("d-none");
}

function hideFilterSection() {
  const filterSection = document.getElementById("filterSection");
  filterSection.classList.add("d-none");
}

function handleError(message) {
  const errorElement = document.getElementById("error");
  errorElement.textContent = message;
  errorElement.style.display = "block";
}

function hideError() {
  const errorElement = document.getElementById("error");
  errorElement.style.display = "none";
}
