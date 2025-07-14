document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("token");

  const form = document.getElementById("form-rutina");
  const respuesta = document.getElementById("respuesta");
  const ejerciciosContainer = document.getElementById("ejercicios-container");
  const btnAgregar = document.getElementById("agregar-ejercicio");

  const estudianteConsultaEmail = document.getElementById("email-consulta");
  const btnConsultar = document.getElementById("consultar-rutinas");
  const tablaRutinas = document.getElementById("tabla-rutinas");

  let ejerciciosDisponibles = [];
  let rutinaEditandoId = null;

  async function cargarEjerciciosDisponibles() {
    const res = await fetch("/ejercicios", {
      headers: { "Authorization": "Bearer " + token }
    });
    ejerciciosDisponibles = await res.json();
  }

  function crearSelectorEjercicio() {
    const div = document.createElement("div");
    div.className = "grupo-ejercicio";

    const select = document.createElement("select");
    select.innerHTML = `<option value="">-- Selecciona ejercicio --</option>`;
    ejerciciosDisponibles.forEach(ej => {
      select.innerHTML += `<option value="${ej.nombre}" data-tipo="${ej.tipo}">${ej.nombre} (${ej.tipo})</option>`;
    });

    const configDiv = document.createElement("div");
    select.addEventListener("change", () => {
      const tipo = select.selectedOptions[0].dataset.tipo;
      configDiv.innerHTML = "";

      if (tipo === "tiempo") {
        configDiv.innerHTML = `
          <label>Duración (min):</label>
          <input type="number" min="1" name="duracion_min" required>
        `;
      } else if (tipo === "repeticiones") {
        configDiv.innerHTML = `
          <label>Series:</label>
          <input type="number" min="1" name="series" required>
          <label>Repeticiones:</label>
          <input type="number" min="1" name="repeticiones" required>
        `;
      }
    });

    const btnQuitar = document.createElement("button");
    btnQuitar.textContent = "❌ Quitar";
    btnQuitar.type = "button";
    btnQuitar.onclick = () => div.remove();

    div.appendChild(select);
    div.appendChild(configDiv);
    div.appendChild(btnQuitar);
    ejerciciosContainer.appendChild(div);
  }

  btnAgregar.addEventListener("click", crearSelectorEjercicio);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const estudiante_email = document.getElementById("estudiante_email").value.trim();
    const nombre = document.getElementById("nombre_rutina").value.trim();
    const descripcion = document.getElementById("descripcion").value.trim();
    const dia = document.getElementById("dia").value;

    if (!estudiante_email || !nombre || !descripcion || !dia) {
      respuesta.textContent = "❌ Completa todos los campos.";
      respuesta.style.color = "red";
      return;
    }

    const ejercicios = [];
    document.querySelectorAll(".grupo-ejercicio").forEach(div => {
      const nombre = div.querySelector("select").value;
      const tipo = div.querySelector("select").selectedOptions[0]?.dataset.tipo;
      if (!nombre || !tipo) return;

      if (tipo === "tiempo") {
        const duracion = Number(div.querySelector('input[name="duracion_min"]').value);
        if (duracion > 0) ejercicios.push({ nombre, tipo, duracion_min: duracion });
      } else if (tipo === "repeticiones") {
        const series = Number(div.querySelector('input[name="series"]').value);
        const repeticiones = Number(div.querySelector('input[name="repeticiones"]').value);
        if (series > 0 && repeticiones > 0) {
          ejercicios.push({ nombre, tipo, series, repeticiones });
        }
      }
    });

    const payload = {
      estudiante_email,
      nombre,
      descripcion,
      dia,
      ejercicios
    };

    const url = rutinaEditandoId ? `/rutinas/${rutinaEditandoId}` : "/rutinas";
    const method = rutinaEditandoId ? "PUT" : "POST";

    const res = await fetch(url, {
      method,
      headers: {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const r = await res.json();
    if (res.ok) {
      respuesta.textContent = rutinaEditandoId
        ? "✅ Rutina editada correctamente"
        : "✅ Rutina asignada correctamente";
      respuesta.style.color = "green";
      form.reset();
      ejerciciosContainer.innerHTML = "";
      rutinaEditandoId = null;
      if (estudianteConsultaEmail.value === estudiante_email) {
        await consultarRutinas(estudiante_email);
      }
    } else {
      respuesta.textContent = `❌ ${r.error || "Error al guardar rutina"}`;
      respuesta.style.color = "red";
    }
  });

  async function consultarRutinas(email) {
    tablaRutinas.innerHTML = "";
    const res = await fetch(`/rutinas-estudiante?estudiante_email=${email}`, {
      headers: { "Authorization": "Bearer " + token }
    });
    const data = await res.json();

    if (!res.ok || !Array.isArray(data.rutinas)) {
      tablaRutinas.innerHTML = "<tr><td colspan='6'>Error al cargar rutinas</td></tr>";
      return;
    }

    if (data.rutinas.length === 0) {
      tablaRutinas.innerHTML = "<tr><td colspan='6'>No hay rutinas para este estudiante</td></tr>";
      return;
    }

    data.rutinas.forEach(rutina => {
      const tr = document.createElement("tr");
      const ejerciciosTexto = rutina.ejercicios.map(ej => {
        return ej.tipo === "tiempo"
          ? `${ej.nombre} (${ej.duracion_min} min)`
          : `${ej.nombre} (${ej.series}x${ej.repeticiones})`;
      }).join(", ");

      tr.innerHTML = `
        <td>${rutina.nombre}</td>
        <td>${rutina.descripcion}</td>
        <td>${rutina.dia}</td>
        <td>${ejerciciosTexto}</td>
        <td>
          <button class="editar-btn" data-id="${rutina._id}">✏️</button>
          <button class="eliminar-btn" data-id="${rutina._id}">🗑️</button>
        </td>
      `;

      tablaRutinas.appendChild(tr);
    });

    document.querySelectorAll(".eliminar-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        if (!confirm("¿Eliminar esta rutina?")) return;
        const id = btn.dataset.id;
        const res = await fetch(`/rutinas/${id}`, {
          method: "DELETE",
          headers: { "Authorization": "Bearer " + token }
        });

        const r = await res.json();
        if (res.ok) {
          await consultarRutinas(estudianteConsultaEmail.value.trim());
        } else {
          alert(r.error || "Error al eliminar rutina");
        }
      });
    });

    document.querySelectorAll(".editar-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.id;
        const rutina = data.rutinas.find(r => r._id === id);
        if (!rutina) return;

        document.getElementById("estudiante_email").value = rutina.estudiante_email;
        document.getElementById("nombre_rutina").value = rutina.nombre;
        document.getElementById("descripcion").value = rutina.descripcion;
        document.getElementById("dia").value = rutina.dia;

        ejerciciosContainer.innerHTML = "";
        rutina.ejercicios.forEach(ej => {
          crearSelectorEjercicio();
          const grupo = ejerciciosContainer.lastChild;
          const select = grupo.querySelector("select");
          select.value = ej.nombre;
          select.dispatchEvent(new Event("change"));

          if (ej.tipo === "tiempo") {
            grupo.querySelector('input[name="duracion_min"]').value = ej.duracion_min;
          } else if (ej.tipo === "repeticiones") {
            grupo.querySelector('input[name="series"]').value = ej.series;
            grupo.querySelector('input[name="repeticiones"]').value = ej.repeticiones;
          }
        });

        rutinaEditandoId = id;
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });
  }

  btnConsultar.addEventListener("click", (e) => {
    e.preventDefault();
    const email = estudianteConsultaEmail.value.trim();
    if (!email) return;
    consultarRutinas(email);
  });

  await cargarEjerciciosDisponibles();
});
