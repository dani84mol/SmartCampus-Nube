const BACKEND_URL = window.BACKEND_URL || "http://localhost:8000";

async function checkHealth() {
  const statusEl = document.getElementById("backend-status");
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    const data = await res.json();
    if (data.status === "ok") {
      statusEl.textContent = `Online (BD: ${data.database})`;
      statusEl.className = "status-badge status-ok";
    } else {
      statusEl.textContent = `Aviso: ${data.database}`;
      statusEl.className = "status-badge status-error";
    }
  } catch (err) {
    statusEl.textContent = "Offline (No accesible)";
    statusEl.className = "status-badge status-error";
  }
}

async function loadRooms() {
  const container = document.getElementById("rooms-list");
  try {
    const res = await fetch(`${BACKEND_URL}/rooms`);
    const rooms = await res.json();
    if (!rooms.length) {
      container.innerHTML = "<p>No hay aulas registradas.</p>";
      return;
    }
    container.innerHTML = rooms.map(room => `
      <div class="room-item">
        <strong>${room.nombre}</strong> <small>(${room.edificio})</small><br>
        <span class="room-meta">Capacidad: ${room.capacidad} personas</span>
        <div class="room-equipment">
          ${(room.equipamiento || []).map(eq => `<span class="badge">${eq}</span>`).join('')}
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = "<p class='msg-error'>Error al cargar las aulas.</p>";
  }
}

async function loadBookings() {
  const container = document.getElementById("bookings-list");
  try {
    const res = await fetch(`${BACKEND_URL}/bookings`);
    const bookings = await res.json();
    if (!bookings.length) {
      container.innerHTML = "<p>No hay reservas activas.</p>";
      return;
    }
    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Aula</th>
            <th>Usuario</th>
            <th>Fecha</th>
            <th>Horario</th>
          </tr>
        </thead>
        <tbody>
          ${bookings.map(b => `
            <tr>
              <td><strong>${b.aula_nombre}</strong></td>
              <td>${b.usuario}</td>
              <td>${b.fecha}</td>
              <td>${b.hora_inicio.slice(0,5)} -${b.hora_fin.slice(0,5)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = "<p class='msg-error'>Error al cargar las reservas.</p>";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  loadRooms();
  loadBookings();
});