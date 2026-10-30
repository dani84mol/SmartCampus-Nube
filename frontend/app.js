const BACKEND_URL = window.BACKEND_URL || "http://localhost:8000";

let globalRooms = [];

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

// --- GESTIÓN DE AULAS CORREGIDA ---
async function loadRooms() {
  const container = document.getElementById("rooms-list");
  try {
    const res = await fetch(`${BACKEND_URL}/rooms`);
    globalRooms = await res.json();

    // 1. Renderizar tarjetas de aulas si el contenedor existe
    if (container) {
      if (!globalRooms.length) {
        container.innerHTML = "<p>No hay aulas registradas.</p>";
      } else {
        container.innerHTML = globalRooms.map(room => {
          const equipStr = (room.equipamiento || []).join(', ');
          return `
            <div class="room-item">
              <div class="room-header">
                <div>
                  <strong>${room.nombre}</strong> <small>(${room.edificio})</small><br>
                  <span class="room-meta">Capacidad: ${room.capacidad} personas</span>
                </div>
                <div class="room-actions">
                  <button onclick="editRoom(${room.id}, '${escapeHtml(room.nombre)}', '${escapeHtml(room.edificio)}', ${room.capacidad}, '${escapeHtml(equipStr)}')" class="btn-sm">Editar</button>
                  <button onclick="deleteRoom(${room.id})" class="btn-sm btn-danger">Eliminar</button>
                </div>
              </div>
              <div class="room-equipment">
                ${(room.equipamiento || []).map(eq => `<span class="badge">${eq.trim()}</span>`).join('')}
              </div>
            </div>
          `;
        }).join('');
      }
    }

    // 2. Actualizar siempre el select de reservas
    updateBookingRoomSelect();

  } catch (err) {
    if (container) {
      container.innerHTML = "<p class='msg-error'>Error al cargar las aulas.</p>";
    }
  }
}

function updateBookingRoomSelect() {
  const select = document.getElementById("booking-room");
  if (!select) return;

  if (!globalRooms || !globalRooms.length) {
    select.innerHTML = '<option value="">No hay aulas disponibles</option>';
    return;
  }

  const currentValue = select.value;

  let optionsHTML = '<option value="">Selecciona un Aula...</option>';
  optionsHTML += globalRooms.map(r => 
    `<option value="${r.id}">${escapeHtml(r.nombre)} (${escapeHtml(r.edificio)})</option>`
  ).join('');

  select.innerHTML = optionsHTML;

  if (currentValue) {
    select.value = currentValue;
  }
}

function updateBookingRoomSelect() {
  const select = document.getElementById("booking-room");
  if (!globalRooms.length) {
    select.innerHTML = '<option value="">No hay aulas disponibles</option>';
    return;
  }
  
  const currentVal = select.value;
  select.innerHTML = '<option value="">Selecciona un Aula...</option>' + 
    globalRooms.map(r => `<option value="${r.id}">${r.nombre} (${r.edificio})</option>`).join('');
  
  if (currentVal) select.value = currentVal;
}

async function handleRoomSubmit(event) {
  event.preventDefault();
  const id = document.getElementById("room-id").value;
  const nombre = document.getElementById("room-name").value.trim();
  const edificio = document.getElementById("room-building").value.trim();
  const capacidad = parseInt(document.getElementById("room-capacity").value, 10);
  const rawEq = document.getElementById("room-equipment").value;
  const equipamiento = rawEq ? rawEq.split(',').map(s => s.trim()).filter(Boolean) : [];

  const payload = { nombre, edificio, capacidad, equipamiento };
  const url = id ? `${BACKEND_URL}/rooms/${id}` : `${BACKEND_URL}/rooms`;
  const method = id ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      resetRoomForm();
      loadRooms();
      loadBookings();
    } else {
      const errData = await res.json();
      alert(`Error al guardar el aula: ${errData.detail || "Datos inválidos"}`);
    }
  } catch (err) {
    alert("Error de conexión con el servidor.");
  }
}

function editRoom(id, nombre, edificio, capacidad, equipamientoStr) {
  document.getElementById("room-id").value = id;
  document.getElementById("room-name").value = nombre;
  document.getElementById("room-building").value = edificio;
  document.getElementById("room-capacity").value = capacidad;
  document.getElementById("room-equipment").value = equipamientoStr;

  document.getElementById("room-form-title").textContent = "Editar Aula";
  document.getElementById("room-submit-btn").textContent = "Actualizar Aula";
  document.getElementById("room-cancel-btn").style.display = "inline-block";
}

async function deleteRoom(id) {
  if (!confirm("¿Seguro que deseas eliminar esta aula? Se borrarán sus reservas asociadas.")) return;

  try {
    const res = await fetch(`${BACKEND_URL}/rooms/${id}`, { method: "DELETE" });
    if (res.ok || res.status === 204) {
      loadRooms();
      loadBookings();
    } else {
      alert("Error al eliminar el aula.");
    }
  } catch (err) {
    alert("Error de conexión.");
  }
}

function resetRoomForm() {
  document.getElementById("room-form").reset();
  document.getElementById("room-id").value = "";
  document.getElementById("room-form-title").textContent = "Añadir Nueva Aula";
  document.getElementById("room-submit-btn").textContent = "Guardar Aula";
  document.getElementById("room-cancel-btn").style.display = "none";
}

// --- GESTIÓN DE RESERVAS ---
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
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          ${bookings.map(b => `
            <tr>
              <td><strong>${b.aula_nombre}</strong></td>
              <td>${b.usuario}</td>
              <td>${b.fecha}</td>
              <td>${b.hora_inicio.slice(0,5)} - ${b.hora_fin.slice(0,5)}</td>
              <td>
                <button onclick="editBooking(${b.id}, ${b.aula_id}, '${escapeHtml(b.usuario)}', '${b.fecha}', '${b.hora_inicio.slice(0,5)}', '${b.hora_fin.slice(0,5)}')" class="btn-sm">Editar</button>
                <button onclick="deleteBooking(${b.id})" class="btn-sm btn-danger">Eliminar</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } catch (err) {
    container.innerHTML = "<p class='msg-error'>Error al cargar las reservas.</p>";
  }
}

async function handleBookingSubmit(event) {
  event.preventDefault();
  const id = document.getElementById("booking-id").value;
  const aula_id = parseInt(document.getElementById("booking-room").value, 10);
  const usuario = document.getElementById("booking-user").value.trim();
  const fecha = document.getElementById("booking-date").value;
  const hora_inicio = document.getElementById("booking-start").value;
  const hora_fin = document.getElementById("booking-end").value;

  if (hora_fin <= hora_inicio) {
    alert("La hora de fin debe ser posterior a la hora de inicio.");
    return;
  }

  const payload = {
    aula_id,
    usuario,
    fecha,
    hora_inicio: hora_inicio.length === 5 ? `${hora_inicio}:00` : hora_inicio,
    hora_fin: hora_fin.length === 5 ? `${hora_fin}:00` : hora_fin
  };

  const url = id ? `${BACKEND_URL}/bookings/${id}` : `${BACKEND_URL}/bookings`;
  const method = id ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      resetBookingForm();
      loadBookings();
    } else {
      const errData = await res.json();
      alert(`No se pudo procesar la reserva: ${errData.detail || "Conflicto de horario"}`);
    }
  } catch (err) {
    alert("Error de conexión con el servidor.");
  }
}

function editBooking(id, aula_id, usuario, fecha, hora_inicio, hora_fin) {
  document.getElementById("booking-id").value = id;
  document.getElementById("booking-room").value = aula_id;
  document.getElementById("booking-user").value = usuario;
  document.getElementById("booking-date").value = fecha;
  document.getElementById("booking-start").value = hora_inicio;
  document.getElementById("booking-end").value = hora_fin;

  document.getElementById("booking-form-title").textContent = "Editar Reserva";
  document.getElementById("booking-submit-btn").textContent = "Actualizar Reserva";
  document.getElementById("booking-cancel-btn").style.display = "inline-block";
}

async function deleteBooking(id) {
  if (!confirm("¿Seguro que deseas cancelar esta reserva?")) return;

  try {
    const res = await fetch(`${BACKEND_URL}/bookings/${id}`, { method: "DELETE" });
    if (res.ok || res.status === 204) {
      loadBookings();
    } else {
      alert("Error al eliminar la reserva.");
    }
  } catch (err) {
    alert("Error de conexión.");
  }
}

function resetBookingForm() {
  document.getElementById("booking-form").reset();
  document.getElementById("booking-id").value = "";
  document.getElementById("booking-form-title").textContent = "Añadir Nueva Reserva";
  document.getElementById("booking-submit-btn").textContent = "Guardar Reserva";
  document.getElementById("booking-cancel-btn").style.display = "none";
}

function escapeHtml(str) {
  return str.replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  loadRooms();
  loadBookings();
});