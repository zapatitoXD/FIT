document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("token");

  const form = document.getElementById("form-alimento");
  const respuesta = document.getElementById("respuesta");
  const tabla = document.getElementById("tabla-alimentos");
  const buscador = document.getElementById("buscador");

  let listaAlimentos = [];

  async function cargarAlimentos() {
    try {
      const res = await fetch("/entrenador_alimentos", {
        headers: {
          "Authorization": "Bearer " + token
        }
      });

      const data = await res.json();
      if (res.ok && Array.isArray(data)) {
        listaAlimentos = data;
        mostrarAlimentos(listaAlimentos);
      } else {
        tabla.innerHTML = "<tr><td colspan='5'>No se pudieron cargar alimentos</td></tr>";
      }
    } catch (err) {
      console.error("Error al cargar alimentos:", err);
      tabla.innerHTML = "<tr><td colspan='5'>Error al conectar con el servidor</td></tr>";
    }
  }

  function mostrarAlimentos(alimentos) {
    tabla.innerHTML = "";
    if (alimentos.length === 0) {
      tabla.innerHTML = "<tr><td colspan='5'>No hay resultados</td></tr>";
      return;
    }

    alimentos.forEach(alimento => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${alimento.nombre}</td>
        <td>${alimento.porcion_estandar} ${alimento.unidad}</td>
        <td>${alimento.calorias}</td>
        <td>
          Prot: ${alimento.macros?.proteina ?? 0}, 
          Gras: ${alimento.macros?.grasa ?? 0}, 
          Carb: ${alimento.macros?.carbohidratos ?? 0}
        </td>
        <td>
          <button data-id="${alimento._id}" class="eliminar-btn">🗑️</button>
        </td>
      `;
      tabla.appendChild(tr);
    });

    document.querySelectorAll(".eliminar-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        if (!confirm("¿Eliminar este alimento?")) return;
        const id = btn.dataset.id;

        try {
          const res = await fetch(`/entrenador_alimentos/${id}`, {
            method: "DELETE",
            headers: {
              "Authorization": "Bearer " + token
            }
          });

          const r = await res.json();
          if (res.ok) {
            await cargarAlimentos();
          } else {
            respuesta.textContent = `❌ ${r.error || "Error al eliminar"}`;
            respuesta.style.color = "red";
          }
        } catch (err) {
          respuesta.textContent = "❌ Error de red al eliminar";
          respuesta.style.color = "red";
        }
      });
    });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nombre = document.getElementById("nombre").value.trim();
    const unidad = document.getElementById("unidad").value.trim();
    const porcion = Number(document.getElementById("porcion").value);
    const calorias = Number(document.getElementById("calorias").value);
    const proteina = Number(document.getElementById("proteina").value);
    const grasa = Number(document.getElementById("grasa").value);
    const carbohidratos = Number(document.getElementById("carbohidratos").value);

    if (!nombre || !unidad || porcion <= 0 || calorias < 0) {
      respuesta.textContent = "❌ Completa los campos obligatorios correctamente.";
      respuesta.style.color = "red";
      return;
    }

    const payload = {
      nombre,
      unidad,
      porcion_estandar: porcion,
      calorias,
      macros: {
        proteina,
        grasa,
        carbohidratos
      }
    };

    try {
      const res = await fetch("/entrenador/alimentos", {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + token,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const r = await res.json();
      if (res.ok) {
        respuesta.textContent = "✅ Alimento insertado correctamente";
        respuesta.style.color = "green";
        form.reset();
        await cargarAlimentos();
      } else {
        respuesta.textContent = `❌ ${r.error || "Error al insertar"}`;
        respuesta.style.color = "red";
      }
    } catch (err) {
      console.error("Error al insertar:", err);
      respuesta.textContent = "❌ Error de red al insertar";
      respuesta.style.color = "red";
    }
  });

  buscador.addEventListener("input", () => {
    const texto = buscador.value.trim().toLowerCase();
    const filtrados = listaAlimentos.filter(a =>
      a.nombre.toLowerCase().includes(texto)
    );
    mostrarAlimentos(filtrados);
  });

  await cargarAlimentos();
});
