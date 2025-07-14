document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
    const container = document.getElementById("alimentos-container");
    const respuesta = document.getElementById("respuesta");
    const form = document.getElementById("form-comidas");
    const comidasContainer = document.getElementById("comidas-hoy");

    // Cargar alimentos del catálogo
    const alimentos = await fetch("/alimentos", {
        headers: { "Authorization": `Bearer ${token}` }
    }).then(r => r.json());

    const datalist = document.createElement("datalist");
    datalist.id = "sugerencias-alimentos";
    alimentos.forEach(a => {
        const option = document.createElement("option");
        option.value = a.nombre;
        datalist.appendChild(option);
    });
    document.body.appendChild(datalist);

    let contador = 0;

    function crearFilaCatalogo() {
        const div = document.createElement("div");
        div.classList.add("fila-alimento");
        div.innerHTML = `
            <input type="text" list="sugerencias-alimentos" class="input-nombre" id="alimento-${contador}" placeholder="Nombre del alimento" required>
            <input type="number" class="input-porcion" id="porcion-${contador}" placeholder="Cantidad (g/ml)" min="1" required>
            <button type="button" class="borrar-fila">❌</button>
        `;
        container.appendChild(div);
        contador++;
    }

    function crearFilaPersonalizada() {
        const div = document.createElement("div");
        div.classList.add("fila-alimento");
        div.innerHTML = `
            <input type="text" class="input-nombre" placeholder="Nombre del alimento personalizado" required>
            <input type="number" class="input-porcion" placeholder="Cantidad (g/ml)" min="1" required>
            <input type="text" class="unidad" placeholder="Unidad (g/ml)" required>
            <input type="number" class="calorias" placeholder="Calorías" step="0.1" min="0" required>
            <input type="number" class="proteinas" placeholder="Proteínas (g)" step="0.1" min="0" required>
            <input type="number" class="grasas" placeholder="Grasas (g)" step="0.1" min="0" required>
            <input type="number" class="carbs" placeholder="Carbohidratos (g)" step="0.1" min="0" required>
            <button type="button" class="borrar-fila">❌</button>
        `;
        container.appendChild(div);
        contador++;
    }

    // Botones para agregar alimentos
    document.getElementById("agregar-catalogo").addEventListener("click", crearFilaCatalogo);
    document.getElementById("agregar-personalizado").addEventListener("click", crearFilaPersonalizada);

    // Botón de borrar fila
    container.addEventListener("click", e => {
        if (e.target.classList.contains("borrar-fila")) {
            e.target.parentElement.remove();
        }
    });

    // Insertar una fila por defecto
    crearFilaCatalogo();

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const filas = document.querySelectorAll(".fila-alimento");
        let errores = 0;

        for (const fila of filas) {
            const nombre = fila.querySelector(".input-nombre").value.trim();
            const porcion = Number(fila.querySelector(".input-porcion").value);

            if (!nombre || isNaN(porcion) || porcion <= 0) continue;

            const unidad = fila.querySelector(".unidad");
            const payload = { alimento: nombre, porcion };

            if (unidad) {
                const calorias = Number(fila.querySelector(".calorias").value);
                const proteinas = Number(fila.querySelector(".proteinas").value);
                const grasas = Number(fila.querySelector(".grasas").value);
                const carbs = Number(fila.querySelector(".carbs").value);
                const unidadValor = unidad.value.trim();

                if (!unidadValor || isNaN(calorias) || isNaN(proteinas) || isNaN(grasas) || isNaN(carbs)) {
                    respuesta.textContent = "❌ Faltan datos en alimento personalizado";
                    respuesta.style.color = "red";
                    return;
                }

                payload.unidad = unidadValor;
                payload.calorias = calorias;
                payload.macros = {
                    proteinas,
                    grasas,
                    carbohidratos: carbs
                };
            }

            const res = await fetch("/comidas", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const resultado = await res.json();
            if (!res.ok) {
                errores++;
                respuesta.textContent = `❌ ${resultado.error || 'Error al registrar una comida'}`;
                respuesta.style.color = "red";
                return;
            }
        }

        if (errores === 0) {
            respuesta.textContent = "✅ Comidas registradas correctamente";
            respuesta.style.color = "green";
            form.reset();
            container.innerHTML = "";
            crearFilaCatalogo();
            await cargarComidasHoy();
        }
    });

    // Mostrar comidas registradas hoy
    // Mostrar comidas registradas hoy
async function cargarComidasHoy() {
    comidasContainer.innerHTML = "Cargando...";
    const res = await fetch("/comidas", {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const data = await res.json();

    // Obtener la fecha local actual (YYYY-MM-DD)
    const hoyLocal = new Date();
    hoyLocal.setMinutes(hoyLocal.getMinutes() - hoyLocal.getTimezoneOffset());
    const fechaHoy = hoyLocal.toISOString().slice(0, 10);

    const comidasHoy = data.filter(c => c.fecha.startsWith(fechaHoy));

    if (comidasHoy.length === 0) {
        comidasContainer.textContent = "No se han registrado comidas hoy.";
        return;
    }

    comidasContainer.innerHTML = "";
    comidasHoy.forEach(comida => {
        const div = document.createElement("div");
        div.classList.add("comida-item");
        div.innerHTML = `
            <strong>${comida.alimento}</strong> - ${comida.porcion} ${comida.unidad}
            (${comida.calorias} kcal)
            <button data-id="${comida._id}" class="btn-editar">✏️</button>
            <button data-id="${comida._id}" class="btn-eliminar">🗑️</button>
        `;
        comidasContainer.appendChild(div);
    });

    // Eliminar comida
    document.querySelectorAll(".btn-eliminar").forEach(btn => {
        btn.addEventListener("click", async () => {
            const id = btn.dataset.id;
            if (!confirm("¿Eliminar esta comida?")) return;

            const res = await fetch(`/comidas/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });
            const r = await res.json();
            if (res.ok) {
                await cargarComidasHoy();
            } else {
                respuesta.textContent = `❌ ${r.error || "Error al eliminar"}`;
                respuesta.style.color = "red";
            }
        });
    });

    // Editar porción
    document.querySelectorAll(".btn-editar").forEach(btn => {
        btn.addEventListener("click", async () => {
            const id = btn.dataset.id;
            const nueva = prompt("Nueva porción (gramos):");
            const valor = Number(nueva);
            if (!nueva || isNaN(valor) || valor <= 0) return;

            const res = await fetch(`/comidas/${id}`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ porcion: valor })
            });

            const r = await res.json();
            if (res.ok) {
                await cargarComidasHoy();
            } else {
                respuesta.textContent = `❌ ${r.error || "Error al editar"}`;
                respuesta.style.color = "red";
            }
        });
    });
}


    await cargarComidasHoy();
});
