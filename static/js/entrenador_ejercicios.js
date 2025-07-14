document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");
  const form = document.getElementById("form-ejercicio");
  const tabla = document.getElementById("tabla-ejercicios");
  const mensaje = document.getElementById("mensaje");

  async function cargarEjercicios() {
    const res = await fetch("/ejercicios", {
      headers: {
        "Authorization": "Bearer " + token
      }
    });

    const data = await res.json();
    tabla.innerHTML = "";

    if (res.ok && Array.isArray(data)) {
      if (data.length === 0) {
        tabla.innerHTML = "<tr><td colspan='4'>No hay ejercicios registrados</td></tr>";
        return;
      }

      data.forEach(ejercicio => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${ejercicio.nombre}</td>
          <td>${ejercicio.tipo}</td>
          <td>${ejercicio.calorias_quemadas} ${ejercicio.tipo === "tiempo" ? "cal/min" : "cal/rep"}</td>
          <td><button data-id="${ejercicio._id}" class="eliminar-btn">🗑️</button></td>
        `;
        tabla.appendChild(tr);
      });

      document.querySelectorAll(".eliminar-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          if (!confirm("¿Eliminar este ejercicio?")) return;
          const id = btn.dataset.id;

          const res = await fetch(`/ejercicios/${id}`, {
            method: "DELETE",
            headers: {
              "Authorization": "Bearer " + token
            }
          });

          const r = await res.json();
          if (res.ok) {
            mensaje.textContent = "✅ Ejercicio eliminado correctamente.";
            mensaje.style.color = "green";
            cargarEjercicios();
          } else {
            mensaje.textContent = `❌ ${r.error || "Error al eliminar"}`;
            mensaje.style.color = "red";
          }
        });
      });
    } else {
      tabla.innerHTML = "<tr><td colspan='4'>Error al cargar ejercicios</td></tr>";
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const nombre = document.getElementById("nombre").value.trim();
    const tipo = document.getElementById("tipo").value;
    const calorias = Number(document.getElementById("calorias").value);

    if (!nombre || !tipo || calorias <= 0) {
      mensaje.textContent = "❌ Todos los campos son obligatorios.";
      mensaje.style.color = "red";
      return;
    }

    const payload = {
      nombre,
      tipo,
      calorias_quemadas: calorias
    };

    const res = await fetch("/ejercicios", {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const r = await res.json();
    if (res.ok) {
      mensaje.textContent = "✅ Ejercicio registrado correctamente.";
      mensaje.style.color = "green";
      form.reset();
      cargarEjercicios();
    } else {
      mensaje.textContent = `❌ ${r.error || "Error al registrar"}`;
      mensaje.style.color = "red";
    }
  });

  cargarEjercicios();
});
