document.getElementById("uploadButton").addEventListener("click", async () => {
    const csvFileInput = document.getElementById("csvFile");
    const file = csvFileInput.files[0];
  
    if (!file) {
      alert("Por favor, selecciona un archivo CSV");
      return;
    }
  
    try {
      const formData = new FormData();
      formData.append("file", file);
  
      const response = await fetch("http://127.0.0.1:5000/upload_csv", {
        method: "POST",
        body: formData,
      });
  
      if (!response.ok) {
        const errorMessage = await response.text();
        alert(`Error al subir el archivo CSV: ${errorMessage}`);
      } else {
        alert("Archivo CSV subido y procesado con éxito");
      }
    } catch (error) {
      alert(`Error al subir el archivo CSV: ${error.message}`);
    }
  });