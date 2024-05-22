function fetchData() {
  fetch("/data")
    .then((response) => response.json())
    .then((data) => {
      updateTable(data);
      populateTypes(data);
    })
    .catch((error) => handleError("Failed to fetch data."));
}
