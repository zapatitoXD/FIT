document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");

  const form = document.getElementById("form-usuario");
  const tabla = document.getElementById("tabla-usuarios");
  const respuesta = document.getElementById("respuesta");
  let modoEdicion = false;
  let idEditar = null;

  async function cargarUsuarios() {
    try {
      const res = await fetch("/admin/usuarios", {
        headers: { "Authorization": "Bearer " + token }
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Error al cargar usuarios");

      tabla.innerHTML = "";

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
          <td>
            <button class="btn-editar" data-id="${u._id}">Editar</button>
            <button class="btn-eliminar" data-id="${u._id}">Eliminar</button>
          </td>
        `;
        tabla.appendChild(tr);
      });
    } catch (err) {
      console.error(err);
      tabla.innerHTML = `<tr><td colspan="8">Error al cargar usuarios</td></tr>`;
    }
  }

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const formData = new FormData(form);
    const usuario = Object.fromEntries(formData.entries());

    // Convertir edad a número
    if (usuario.edad) usuario.edad = parseInt(usuario.edad);

    const url = modoEdicion ? `/admin/usuarios/${idEditar}` : "/registro";
    const method = modoEdicion ? "PUT" : "POST";

    try {
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + token
        },
        body: JSON.stringify(usuario)
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Error");

      respuesta.textContent = modoEdicion ? "Usuario actualizado" : "Usuario registrado";
      form.reset();
      modoEdicion = false;
      idEditar = null;
      form.querySelector("button[type='submit']").textContent = "Registrar usuario";
      cargarUsuarios();
    } catch (err) {
      respuesta.textContent = err.message;
    }
  });

  tabla.addEventListener("click", async e => {
    const id = e.target.dataset.id;
    if (e.target.classList.contains("btn-eliminar")) {
      if (confirm("¿Estás seguro de eliminar este usuario?")) {
        try {
          const res = await fetch(`/admin/usuarios/${id}`, {
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token }
          });

          const data = await res.json();
          if (!res.ok) throw new Error(data.error || "Error");

          respuesta.textContent = "Usuario eliminado correctamente";
          cargarUsuarios();
        } catch (err) {
          respuesta.textContent = err.message;
        }
      }
    }

    if (e.target.classList.contains("btn-editar")) {
      try {
        const res = await fetch(`/admin/usuarios/${id}`, {
          headers: { "Authorization": "Bearer " + token }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Error al cargar usuario");

        // Llenar formulario
        for (const campo in data) {
          if (form.elements[campo]) {
            form.elements[campo].value = data[campo];
          }
        }

        modoEdicion = true;
        idEditar = id;
        form.querySelector("button[type='submit']").textContent = "Guardar cambios";
        respuesta.textContent = "Editando usuario...";
      } catch (err) {
        respuesta.textContent = err.message;
      }
    }
  });

  // Cargar usuarios al iniciar
  cargarUsuarios();
});
