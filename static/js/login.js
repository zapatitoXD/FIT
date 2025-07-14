document.getElementById("login-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const errorMsg = document.getElementById("error-msg");

  errorMsg.textContent = "";

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      errorMsg.textContent = data.error || "Error desconocido";
      return;
    }

    localStorage.setItem("token", data.token);

    // 🔁 Redirigir según el rol del usuario
    const rol = data.usuario.rol;

    switch (rol) {
      case "estudiante":
        window.location.href = "/dashboard";
        break;
      case "entrenador":
        window.location.href = "/entrenador";
        break;
      case "admin":
        window.location.href = "/dashboard-admin";
        break;
      default:
        errorMsg.textContent = "Rol no reconocido.";
    }

  } catch (err) {
    console.error("Error de red:", err);
    errorMsg.textContent = "Error al conectar con el servidor";
  }
});
