document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");

  if (!token) {
    alert("No estás autenticado.");
    window.location.href = "/login";
    return;
  }

  const payload = JSON.parse(atob(token.split(".")[1]));
  const nombre = payload.nombre || "Estudiante";

  document.getElementById("saludo").textContent = `Bienvenido, ${nombre}`;

  // Simulación de conteos
  document.getElementById("comidas-count").textContent = "3";
  document.getElementById("rutina-count").textContent = "5";
  document.getElementById("progreso-texto").textContent = "¡Vas bien!";
});
