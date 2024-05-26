document.addEventListener("DOMContentLoaded", () => {
  fetchData();
  fetchCrates();
  fetchPlatforms();
});

document.getElementById("platformSelect").addEventListener("change", () => {
  const select = document.getElementById("platformSelect");
  const button = select.nextElementSibling;
  button.disabled = !select.value;
  if (!select.value) {
    hidePortSections();
    updatePlatformDataList([]);
  }
});

document.getElementById("crateSelect").addEventListener("change", () => {
  const select = document.getElementById("crateSelect");
  const button = select.nextElementSibling;
  button.disabled = !select.value;
  if (!select.value) {
    hideCrateView();
  }
});

document.getElementById("platformTypeSelect").addEventListener("change", () => {
  const select = document.getElementById("platformTypeSelect");
  const button = select.nextElementSibling;
  button.disabled = !select.value;
  if (!select.value) {
    updatePlatformDataList([]);
  }
});

document.getElementById("exportSelect").addEventListener("change", () => {
  const select = document.getElementById("exportSelect");
  const button = select.nextElementSibling;
  button.disabled = !select.value;
});

function fetchCrates() {
  fetch("/crates")
    .then((response) => response.json())
    .then((data) => {
      const select = document.getElementById("crateSelect");
      select.innerHTML = "";
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "Select a crate";
      select.appendChild(option);
      data.forEach((label) => {
        const option = document.createElement("option");
        option.value = label;
        option.textContent = label;
        select.appendChild(option);
      });
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Failed to fetch crates.");
    });
}

function showCrate() {
  const name = document.getElementById("crateSelect").value;
  fetch(`/crate?name=${encodeURIComponent(name)}`)
    .then((response) => response.json())
    .then((data) => {
      const view = document.getElementById("crateView");
      view.classList.remove("d-none");
      view.firstElementChild.textContent = JSON.stringify(data, null, 2);
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Failed to fetch crate.");
    });
}

function fetchPlatforms() {
  fetch("/platforms")
    .then((response) => response.json())
    .then((data) => {
      const platformSelect = document.getElementById("platformSelect");
      Object.entries(data).forEach(([platform, port]) => {
        const option = document.createElement("option");
        option.label = platform;
        option.value = port;
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
  const updateTypeSelection = (data) => {
    const types = new Set(data);
    const platformTypeSelect = document.getElementById("platformTypeSelect");
    platformTypeSelect.innerHTML = "";
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "Select an ontological type";
    platformTypeSelect.appendChild(option);
    types.forEach((type) => {
      const option = document.createElement("option");
      option.value = type;
      option.textContent = type;
      platformTypeSelect.appendChild(option);
    });
  };

  const platform_url = document.getElementById("platformSelect").value;
  fetch(`http://localhost:${platform_url}/data/types`, {
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
    .then((zip) => processROCrates(zip))
    .then((jsonString) => {
      const data = JSON.parse(jsonString);
      updateTypeSelection(data);
      showPortSections();
      fetchCrates();
    })
    .catch((error) => {
      console.error("Error:", error);
      handleError("Failed to fetch or process data.");
    });
}

function fetchPlatformData() {
  const platform_url = document.getElementById("platformSelect").value;
  const selectedType = document.getElementById("platformTypeSelect").value;
  if (selectedType) {
    fetch(
      `http://localhost:${platform_url}/data/ontology?type=${encodeURIComponent(
        selectedType
      )}&format=ROC`,
      {
        method: "GET",
        headers: {
          Accept: "application/zip",
        },
      }
    )
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
      .then((zip) => processROCrates(zip))
      .then((jsonString) => {
        const data = JSON.parse(jsonString);
        updatePlatformDataList(data);
        fetchCrates();
      })
      .catch((error) => {
        console.error("Error:", error);
        handleError("Failed to fetch filtered data.");
      });
  } else {
    alert("Please select a type to filter by!");
  }
}

function processROCrates(zip) {
  // TODO use the JS ROCrate library instead
  return new Promise((resolve, reject) => {
    let filename;
    if ("ro-crate-metadata.json" in zip.files) {
      zip.files["ro-crate-metadata.json"]
        .async("string")
        .then((json) => {
          const data = JSON.parse(json);
          data["@graph"].forEach((item) => {
            if (item["@type"] === "RESPONSE") {
              filename = item["@id"];
            }
          });
          if (filename && filename in zip.files) {
            resolve(zip.files[filename].async("string"));
          } else {
            reject(new Error("Missing types file"));
          }
        })
        .catch((error) => {
          reject(error);
        });
    } else {
      reject(new Error("Missing manifest"));
    }
  });
}

function populateExportSamples(data) {
  const samplesList = data.filter((item) => item.type.includes("Sample"));
  const select = document.getElementById("exportSelect");
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
            <strong>title:</strong> ${item.title}
          `;
    li.appendChild(span);
    const button = document.createElement("button");
    button.className = "btn btn-outline-secondary btn-sm";
    button.textContent = "Import Data";
    button.onclick = () => {
      importData(item);
    };
    li.appendChild(button);
    list.appendChild(li);
  });
}

function importData(item) {
  const port = document.getElementById("platformSelect").value;
  fetch(`data/import?port=${port}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(item),
  })
    .then((response) => {
      if (response.ok) {
        fetchData();
        hideMetadata();
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

function exportData() {
  const selected_id = document.getElementById("exportSelect").value;
  const port = document.getElementById("platformSelect").value;
  fetch(`/data/export?port=${port}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(selected_id),
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error("Failed to export data.");
      }
    })
    .then((data) => {
      fetchCrates();
      alert("Successfully exported data.");
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("An error occurred during data export.");
    });
}

function resetData() {
  fetch("/data/reset").then(
    () => {
      fetchData();
      fetchCrates();
      hideMetadata();
      hideCrateView();
      hideError();
    },
    () => handleError("Failed to reset data.")
  );
}

function populateTypes(data) {
  const types = new Set(data.map((item) => item.type));
  const typeSelect = document.getElementById("typeSelect");
  typeSelect.innerHTML = "";
  const option = document.createElement("option");
  option.value = "";
  option.textContent = "All";
  typeSelect.appendChild(option);
  types.forEach((type) => {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = type;
    typeSelect.appendChild(option);
  });
}

function refreshData() {
  fetchFilteredData();
  hideMetadata();
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
      .catch((error) => {
        console.error("Error:", error);
        handleError("Failed to fetch filtered data.");
      });
  } else {
    fetchData();
  }
}

function updateTable(data) {
  const createMetadataButton = (item) => {
    const resetOtherMetadataButtons = () => {
      const buttons = document.getElementsByClassName("metadata-toggler");
      Array.from(buttons).forEach((b) => {
        if (b !== button) b.innerHTML = "+";
      });
    };

    const metadata = document
      .getElementById("metadata")
      .getElementsByTagName("pre")[0];
    const context = document
      .getElementById("context")
      .getElementsByTagName("pre")[0];

    const button = document.createElement("button");
    button.innerHTML = "+";
    button.className = "btn btn-outline-secondary metadata-toggler";
    button.addEventListener("click", () => {
      const infoSection = document.getElementById("infoSection");
      metadata.textContent = "";
      if (button.innerHTML == "+") {
        resetOtherMetadataButtons();
        button.innerHTML = "-";
        metadata.textContent = JSON.stringify(item["metadata"], null, 2);
        context.textContent = JSON.stringify(item["@context"] || {}, null, 2);
        infoSection.classList.remove("d-none");
      } else {
        button.innerHTML = "+";
        metadata.textContent = "";
        context.textContent = "";
        infoSection.classList.add("d-none");
      }
    });
    return button;
  };

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
    const button = createMetadataButton(item);
    cellMetadata.appendChild(button);
    cellMetadata.className = "text-center";
  });
}

function hideMetadata() {
  const infoSection = document.getElementById("infoSection");
  infoSection.classList.add("d-none");
}

function hideCrateView() {
  const view = document.getElementById("crateView");
  view.classList.add("d-none");
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

function showPortSections() {
  const portSections = document.getElementById("portSections");
  portSections.classList.remove("d-none");
}

function hidePortSections() {
  const portSections = document.getElementById("portSections");
  portSections.classList.add("d-none");
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
