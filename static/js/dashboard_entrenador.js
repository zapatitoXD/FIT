document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("token");
  const bienvenida = document.getElementById("bienvenida");

  try {
    const res = await fetch("/perfil", {
      headers: {
        "Authorization": "Bearer " + token
      }
    });

    const data = await res.json();
    if (res.ok && data.rol === "entrenador") {
      bienvenida.textContent = `Bienvenido, ${data.nombre}`;
    } else {
      alert("Acceso no autorizado");
      window.location.href = "/login";
    }
  } catch (err) {
    console.error("Error al verificar sesión", err);
    alert("Sesión no válida");
    window.location.href = "/login";
  }

  document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  });
});
