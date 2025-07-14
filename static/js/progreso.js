document.addEventListener("DOMContentLoaded", async () => {
    await mostrarGraficoBalance();
    await mostrarGraficoCumplimientoDetallado();
    await mostrarLineaCumplimientoDiario();
    await mostrarGraficoMacronutrientes();  // nuevo gráfico
});

async function mostrarGraficoBalance() {
    const token = localStorage.getItem("token");
    const hoy = new Date().toISOString().split("T")[0];
    const hace7dias = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];

    const res = await fetch(`/balance-calorico?desde=${hace7dias}&hasta=${hoy}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const data = await res.json();
    const labels = Object.keys(data.resumen_diario);
    const consumidas = labels.map(dia => data.resumen_diario[dia].consumidas);
    const quemadas = labels.map(dia => data.resumen_diario[dia].quemadas);

    const ctx = document.getElementById("grafico-balance").getContext("2d");

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Calorías consumidas',
                    data: consumidas,
                    backgroundColor: 'rgba(255, 165, 0, 0.8)'
                },
                {
                    label: 'Calorías quemadas',
                    data: quemadas,
                    backgroundColor: 'rgba(0, 123, 255, 0.7)'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Balance calórico diario (últimos 7 días)'
                }
            },
            scales: {
                x: { title: { display: true, text: 'Fecha' } },
                y: { beginAtZero: true, title: { display: true, text: 'Calorías' } }
            }
        }
    });
}

async function mostrarGraficoCumplimientoDetallado() {
    const token = localStorage.getItem("token");

    const res = await fetch(`/progreso/cumplimiento-detallado`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const datos = await res.json();
    const ctx = document.getElementById("grafico-cumplimiento").getContext("2d");

    const total = datos.total_dias_con_rutina || 0;
    const completas = datos.completas || 0;
    const incompletas = datos.incompletas || 0;
    const noRealizadas = datos.no_realizadas || 0;

    const porcentajeCompletas = datos.porcentaje_completas || 0;
    const porcentajeIncompletas = datos.porcentaje_incompletas || 0;
    const porcentajeNoRealizadas = datos.porcentaje_no_realizadas || 0;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completas', 'Incompletas', 'No realizadas'],
            datasets: [{
                label: 'Cumplimiento de rutinas',
                data: [completas, incompletas, noRealizadas],
                backgroundColor: ['#4caf50', '#ff9800', '#f44336']
            }]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'Cumplimiento de rutinas semanales'
                },
                tooltip: {
                    callbacks: {
                        label: context => `${context.label}: ${context.raw} días`
                    }
                }
            }
        }
    });

    const detalle = document.getElementById("detalle-cumplimiento");
    if (total === 0) {
        detalle.textContent = "⚠️ No hay rutinas asignadas esta semana.";
        detalle.style.color = "gray";
    } else if (completas === total) {
        detalle.textContent = "✅ ¡Felicidades! Cumpliste todas tus rutinas esta semana.";
        detalle.style.color = "green";
    } else {
        detalle.textContent = `Has cumplido ${completas} de ${total} rutinas asignadas (${porcentajeCompletas.toFixed(2)}%).`;
        detalle.style.color = "orange";
    }

    document.getElementById("porcentaje-detallado").innerHTML = `
        <p>
            <strong>Completas:</strong> ${porcentajeCompletas.toFixed(1)}%<br>
            <strong>Incompletas:</strong> ${porcentajeIncompletas.toFixed(1)}%<br>
            <strong>No realizadas:</strong> ${porcentajeNoRealizadas.toFixed(1)}%
        </p>
    `;
}

async function mostrarLineaCumplimientoDiario() {
    const token = localStorage.getItem("token");

    const res = await fetch(`/progreso/cumplimiento-por-dia`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const data = await res.json();
    const fechas = Object.keys(data);
    const porcentajes = fechas.map(fecha => data[fecha].porcentaje);
    const dias = fechas.map(fecha => data[fecha].dia);

    const ctx = document.getElementById("grafico-cumplimiento-linea").getContext("2d");

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dias,
            datasets: [{
                label: 'Porcentaje de cumplimiento diario',
                data: porcentajes,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.4,
                spanGaps: false
            }]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'Cumplimiento diario de rutinas (últimos 7 días)'
                },
                tooltip: {
                    callbacks: {
                        label: context => context.raw !== null ? `${context.raw}%` : 'Sin rutina'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: 'Porcentaje de cumplimiento' }
                }
            }
        }
    });
}

async function mostrarGraficoMacronutrientes() {
    const token = localStorage.getItem("token");
    const hoy = new Date().toISOString().split("T")[0];
    const hace7dias = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];

    const res = await fetch(`/resumen/macros?desde=${hace7dias}&hasta=${hoy}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const data = await res.json();
    const totales = data.totales || {};

    const valores = [
        totales.proteinas || 0,
        totales.carbohidratos || 0,
        totales.grasas || 0
    ];

    const totalGramos = valores.reduce((acc, val) => acc + val, 0);

    const ctx = document.getElementById("grafico-macros").getContext("2d");

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Proteínas', 'Carbohidratos', 'Grasas'],
            datasets: [{
                data: valores,
                backgroundColor: ['#2196f3', '#ffc107', '#ff7043']
            }]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'Distribución de macronutrientes (últimos 7 días)'
                },
                tooltip: {
                    callbacks: {
                        label: context => {
                            const label = context.label || '';
                            const valor = context.raw || 0;
                            const porcentaje = totalGramos > 0 ? (valor / totalGramos * 100).toFixed(1) : 0;
                            return `${label}: ${valor.toFixed(1)} g (${porcentaje}%)`;
                        }
                    }
                }
            }
        }
    });
}
