document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");
  const tabla = document.getElementById("tabla-estudiantes");
  const form = document.getElementById("form-busqueda");
  const inputNombre = document.getElementById("buscar-nombre");
  const inputCarrera = document.getElementById("buscar-carrera");

  async function cargarEstudiantes(nombre = "", carrera = "") {
    let url = "/entrenador_estudiantes";
    const params = new URLSearchParams();

    if (nombre.trim()) params.append("nombre", nombre.trim());
    if (carrera.trim()) params.append("carrera", carrera.trim());

    if ([...params].length > 0) url += `?${params.toString()}`;

    try {
      const res = await fetch(url, {
        headers: {
          "Authorization": "Bearer " + token
        }
      });

      const data = await res.json();
      tabla.innerHTML = "";

      if (res.ok && Array.isArray(data)) {
        if (data.length === 0) {
          tabla.innerHTML = "<tr><td colspan='5'>No se encontraron estudiantes</td></tr>";
          return;
        }

        data.forEach(est => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${est.nombre}</td>
            <td>${est.email}</td>
            <td>${est.codigo_universitario || "-"}</td>
            <td>${est.carrera || "-"}</td>
            <td>${est.edad || "-"}</td>
          `;
          tabla.appendChild(tr);
        });
      } else {
        tabla.innerHTML = "<tr><td colspan='5'>Error al cargar estudiantes</td></tr>";
      }
    } catch (err) {
      console.error("Error:", err);
      tabla.innerHTML = "<tr><td colspan='5'>Error de red</td></tr>";
    }
  }

  form.addEventListener("submit", e => {
    e.preventDefault();
    cargarEstudiantes(inputNombre.value, inputCarrera.value);
  });

const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  });
}


  // Cargar todos al inicio
  cargarEstudiantes();
});
