document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");

  document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  });

  window.listarUsuarios = async (rol) => {
    let url = "/admin/usuarios";
    if (rol) url += `?rol=${rol}`;

    try {
      const res = await fetch(url, {
        headers: {
          "Authorization": "Bearer " + token
        }
      });
      const data = await res.json();
      const resultado = document.getElementById("resultado");

      resultado.innerHTML = "";

      if (res.ok && Array.isArray(data.usuarios)) {
        if (data.usuarios.length === 0) {
          resultado.innerHTML = "<tr><td colspan='8'>No hay usuarios</td></tr>";
          return;
        }

        data.usuarios.forEach(u => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${u.nombre}</td>
            <td>${u.email}</td>
            <td>${u.rol}</td>
            <td>${u.codigo_universitario || "-"}</td>
            <td>${u.sexo || "-"}</td>
            <td>${u.edad || "-"}</td>
            <td>${u.carrera || "-"}</td>
            <td>${u.fecha_creacion}</td>
          `;
          resultado.appendChild(tr);
        });
      } else {
        resultado.innerHTML = `<tr><td colspan="8">${data.error || "Error al listar usuarios"}</td></tr>`;
      }
    } catch (err) {
      console.error("Error:", err);
      document.getElementById("resultado").innerHTML = "<tr><td colspan='8'>Error de red</td></tr>";
    }
  };

  window.exportar = async (tipo) => {
    let url = `/admin/exportar/${tipo}`;
    if (["comidas", "progreso"].includes(tipo)) {
      const desde = prompt("Desde (YYYY-MM-DD):");
      const hasta = prompt("Hasta (YYYY-MM-DD):");
      if (!desde || !hasta) return;
      url += `?desde=${desde}&hasta=${hasta}`;
    }

    try {
      const res = await fetch(url, {
        headers: {
          "Authorization": "Bearer " + token
        }
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.error || "Error al exportar");
        return;
      }

      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `${tipo}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("Error:", err);
      alert("Error de red");
    }
  };
});
