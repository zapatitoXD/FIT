document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
    const rutinaContainer = document.getElementById("rutina-container");
    const respuestaProgreso = document.getElementById("respuesta-progreso");

    const res = await fetch("/rutina-dia", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (res.ok) {
        const data = await res.json();
        const rutina = data.rutina;

        rutina.ejercicios.forEach((ej, i) => {
            const div = document.createElement("div");
            div.classList.add("ejercicio");

            let camposExtra = "";
            if (ej.tipo === "tiempo") {
                camposExtra = `
                    <input type="number" id="ej-${i}-duracion" placeholder="Minutos" min="1" value="${ej.duracion_min || ''}" disabled>
                `;
            } else if (ej.tipo === "repeticiones") {
                camposExtra = `
                    <input type="number" id="ej-${i}-series" placeholder="Series" min="1" value="${ej.series || ''}" disabled>
                    <input type="number" id="ej-${i}-reps" placeholder="Repeticiones" min="1" value="${ej.repeticiones || ''}" disabled>
                `;
            }

            div.innerHTML = `
                <label>
                    <input type="checkbox" id="ej-${i}-completado"> ${ej.nombre} (${ej.tipo})
                </label>
                ${camposExtra}
            `;
            rutinaContainer.appendChild(div);

            // Habilitar/Deshabilitar campos al marcar checkbox
            const checkbox = document.getElementById(`ej-${i}-completado`);
            checkbox.addEventListener("change", () => {
                if (ej.tipo === "tiempo") {
                    document.getElementById(`ej-${i}-duracion`).disabled = !checkbox.checked;
                } else if (ej.tipo === "repeticiones") {
                    document.getElementById(`ej-${i}-series`).disabled = !checkbox.checked;
                    document.getElementById(`ej-${i}-reps`).disabled = !checkbox.checked;
                }
            });
        });

        document.getElementById("registrar-progreso").addEventListener("click", async () => {
            const ejercicios_realizados = [];

            rutina.ejercicios.forEach((ej, i) => {
                const completado = document.getElementById(`ej-${i}-completado`).checked;
                if (!completado) return;

                const ejercicio = {
                    nombre: ej.nombre,
                    tipo: ej.tipo,
                    completado: true
                };

                if (ej.tipo === "tiempo") {
                    const duracion = Number(document.getElementById(`ej-${i}-duracion`).value);
                    if (!isNaN(duracion) && duracion > 0) {
                        ejercicio.duracion_min = duracion;
                    } else {
                        return;
                    }
                } else if (ej.tipo === "repeticiones") {
                    const series = Number(document.getElementById(`ej-${i}-series`).value);
                    const repeticiones = Number(document.getElementById(`ej-${i}-reps`).value);
                    if (!isNaN(series) && series > 0 && !isNaN(repeticiones) && repeticiones > 0) {
                        ejercicio.series = series;
                        ejercicio.repeticiones = repeticiones;
                    } else {
                        return;
                    }
                }

                ejercicios_realizados.push(ejercicio);
            });

            if (ejercicios_realizados.length === 0) {
                alert("Marca al menos un ejercicio completado con valores válidos.");
                return;
            }

            const resp = await fetch("/rutina-dia/progreso", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ ejercicios_realizados })
            });

            const resultado = await resp.json();

            if (resp.ok) {
                respuestaProgreso.textContent = `✅ ${resultado.mensaje}. Calorías quemadas: ${resultado.calorias_quemadas}`;
                respuestaProgreso.style.color = "green";
                setTimeout(() => {
                    window.location.href = "/dashboard"; // Ajusta la ruta si es necesario
                }, 5000);
            } else {
                respuestaProgreso.textContent = `❌ ${resultado.error}`;
                respuestaProgreso.style.color = "red";
            }
        });
    } else {
        rutinaContainer.textContent = "No hay rutina asignada para hoy.";
    }
});
