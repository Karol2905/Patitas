const API_URL = (window.API_URL || "").replace(/\/$/, "");

const MOTIVOS = [
  { valor: "Consulta general", detalle: "Revisión por síntomas o malestar" },
  { valor: "Vacunación", detalle: "Aplicación o refuerzo de vacunas" },
  { valor: "Control y seguimiento", detalle: "Revisión de un tratamiento o resultados de exámenes" },
  { valor: "Primera consulta", detalle: "Primera visita de la mascota a la clínica" },
];

const NOMBRES_DIA = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
const NOMBRES_MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const SEMANAS_MAXIMAS = 4;

const estado = {
  motivo: null,
  fecha: null,
  hora: null,
  semana: 0,
};

const elementos = {
  formulario: document.getElementById("form-cita"),
  motivos: document.getElementById("opciones-motivo"),
  dias: document.getElementById("dias"),
  horas: document.getElementById("horas"),
  semanaAnterior: document.getElementById("semana-anterior"),
  semanaSiguiente: document.getElementById("semana-siguiente"),
  mensaje: document.getElementById("mensaje-form"),
  botonAgendar: document.getElementById("boton-agendar"),
  pasos: document.querySelectorAll("#pasos li"),
  resumenMotivo: document.getElementById("resumen-motivo"),
  resumenFecha: document.getElementById("resumen-fecha"),
  resumenHora: document.getElementById("resumen-hora"),
};

function hoy() {
  const fecha = new Date();
  fecha.setHours(0, 0, 0, 0);
  return fecha;
}

function sumarDias(fecha, dias) {
  const nueva = new Date(fecha);
  nueva.setDate(nueva.getDate() + dias);
  return nueva;
}

function aTextoISO(fecha) {
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

function desdeTextoISO(texto) {
  const [anio, mes, dia] = texto.split("-").map(Number);
  return new Date(anio, mes - 1, dia);
}

function fechaLegible(texto) {
  const fecha = desdeTextoISO(texto);
  return `${NOMBRES_DIA[fecha.getDay()]} ${fecha.getDate()} de ${NOMBRES_MES[fecha.getMonth()]} de ${fecha.getFullYear()}`;
}

function horariosDelDia() {
  const horarios = [];
  for (let minutos = 8 * 60; minutos <= 17 * 60 + 30; minutos += 30) {
    const hora = String(Math.floor(minutos / 60)).padStart(2, "0");
    const minuto = String(minutos % 60).padStart(2, "0");
    horarios.push(`${hora}:${minuto}`);
  }
  return horarios;
}

function yaPaso(fechaTexto, hora) {
  if (fechaTexto !== aTextoISO(hoy())) {
    return false;
  }
  const [h, m] = hora.split(":").map(Number);
  const ahora = new Date();
  return h * 60 + m <= ahora.getHours() * 60 + ahora.getMinutes();
}

function crearElemento(etiqueta, clase, texto) {
  const elemento = document.createElement(etiqueta);
  if (clase) {
    elemento.className = clase;
  }
  if (texto !== undefined) {
    elemento.textContent = texto;
  }
  return elemento;
}

function pintarMotivos() {
  elementos.motivos.replaceChildren();
  MOTIVOS.forEach((motivo) => {
    const boton = crearElemento("button", "motivo");
    boton.type = "button";
    boton.setAttribute("aria-pressed", String(estado.motivo === motivo.valor));
    if (estado.motivo === motivo.valor) {
      boton.classList.add("seleccionado");
    }

    const textos = crearElemento("span");
    textos.append(
      crearElemento("span", "motivo-titulo", motivo.valor),
      crearElemento("span", "motivo-detalle", motivo.detalle),
    );
    const marca = crearElemento("span", "motivo-marca", estado.motivo === motivo.valor ? "Elegido" : "Elegir");

    boton.append(textos, marca);
    boton.addEventListener("click", () => {
      estado.motivo = motivo.valor;
      pintarMotivos();
      actualizarResumen();
    });
    elementos.motivos.append(boton);
  });
}

function pintarDias() {
  elementos.dias.replaceChildren();
  const inicio = sumarDias(hoy(), estado.semana * 7);
  const primerDia = hoy();

  for (let i = 0; i < 7; i += 1) {
    const fecha = sumarDias(inicio, i);
    const texto = aTextoISO(fecha);
    const boton = crearElemento("button", "dia");
    boton.type = "button";
    boton.disabled = fecha.getDay() === 0 || fecha < primerDia;
    boton.setAttribute("aria-label", fechaLegible(texto));
    if (estado.fecha === texto) {
      boton.classList.add("seleccionado");
    }

    boton.append(
      crearElemento("span", "dia-nombre", NOMBRES_DIA[fecha.getDay()]),
      crearElemento("span", "dia-numero", `${fecha.getDate()}.${fecha.getMonth() + 1}.`),
      crearElemento("span", "dia-punto"),
    );
    boton.addEventListener("click", () => seleccionarFecha(texto));
    elementos.dias.append(boton);
  }

  elementos.semanaAnterior.disabled = estado.semana === 0;
  elementos.semanaSiguiente.disabled = estado.semana >= SEMANAS_MAXIMAS - 1;
}

async function horasOcupadas(fechaTexto) {
  if (!API_URL) {
    return new Set();
  }
  try {
    const respuesta = await fetch(`${API_URL}/citas?fecha=${encodeURIComponent(fechaTexto)}`);
    if (!respuesta.ok) {
      return new Set();
    }
    const citas = await respuesta.json();
    return new Set(citas.filter((cita) => cita.estado === "ACTIVA").map((cita) => cita.hora));
  } catch {
    return new Set();
  }
}

async function pintarHoras() {
  const fechaTexto = estado.fecha;
  if (!fechaTexto) {
    elementos.horas.replaceChildren(crearElemento("p", "vacio", "Selecciona un día para ver los horarios."));
    return;
  }

  elementos.horas.replaceChildren(crearElemento("p", "vacio", "Consultando horarios..."));
  const ocupadas = await horasOcupadas(fechaTexto);
  if (fechaTexto !== estado.fecha) {
    return;
  }

  const botones = horariosDelDia().map((hora) => {
    const boton = crearElemento("button", "hora", hora);
    boton.type = "button";
    boton.disabled = ocupadas.has(hora) || yaPaso(fechaTexto, hora);
    if (estado.hora === hora && !boton.disabled) {
      boton.classList.add("seleccionado");
    }
    boton.addEventListener("click", () => {
      estado.hora = hora;
      pintarHoras();
      actualizarResumen();
    });
    return boton;
  });

  if (botones.every((boton) => boton.disabled)) {
    elementos.horas.replaceChildren(crearElemento("p", "vacio", "No hay horarios disponibles para este día."));
    return;
  }
  elementos.horas.replaceChildren(...botones);
}

function seleccionarFecha(texto) {
  estado.fecha = texto;
  estado.hora = null;
  pintarDias();
  pintarHoras();
  actualizarResumen();
}

function marcarPaso(actual) {
  elementos.pasos.forEach((paso) => {
    const numero = Number(paso.dataset.paso);
    paso.classList.toggle("activo", numero === actual);
    paso.classList.toggle("completo", numero < actual);
  });
}

function actualizarResumen() {
  const pintar = (elemento, valor) => {
    elemento.textContent = valor || "Sin seleccionar";
    elemento.classList.toggle("pendiente", !valor);
  };
  pintar(elementos.resumenMotivo, estado.motivo);
  pintar(elementos.resumenFecha, estado.fecha ? fechaLegible(estado.fecha) : null);
  pintar(elementos.resumenHora, estado.hora);

  if (!estado.motivo) {
    marcarPaso(1);
  } else if (!estado.fecha || !estado.hora) {
    marcarPaso(2);
  } else {
    marcarPaso(3);
  }
}

function mostrarMensaje(tipo, titulo, detalles = []) {
  elementos.mensaje.className = `mensaje mensaje-${tipo}`;
  elementos.mensaje.replaceChildren(crearElemento("strong", null, titulo));
  if (detalles.length > 0) {
    const lista = crearElemento("ul");
    detalles.forEach((detalle) => lista.append(crearElemento("li", null, detalle)));
    elementos.mensaje.append(lista);
  }
  elementos.mensaje.hidden = false;
  elementos.mensaje.scrollIntoView({ behavior: "smooth", block: "center" });
}

function ocultarMensaje() {
  elementos.mensaje.hidden = true;
  elementos.mensaje.replaceChildren();
}

function datosDelFormulario() {
  const formulario = new FormData(elementos.formulario);
  const texto = (nombre) => (formulario.get(nombre) || "").toString().trim();
  return {
    motivo: estado.motivo,
    fecha: estado.fecha,
    hora: estado.hora,
    mascota: texto("mascota"),
    especie: texto("especie"),
    dueno: texto("dueno"),
    correo: texto("correo"),
    telefono: texto("telefono"),
    acepta_tratamiento_datos: formulario.get("acepta_tratamiento_datos") === "on",
  };
}

function faltantesDeSeleccion() {
  const faltantes = [];
  if (!estado.motivo) {
    faltantes.push("Selecciona el motivo de la visita");
  }
  if (!estado.fecha) {
    faltantes.push("Selecciona el día de la cita");
  }
  if (!estado.hora) {
    faltantes.push("Selecciona la hora de la cita");
  }
  return faltantes;
}

function reiniciar() {
  elementos.formulario.reset();
  estado.motivo = null;
  estado.fecha = null;
  estado.hora = null;
  estado.semana = 0;
  pintarMotivos();
  pintarDias();
  pintarHoras();
  actualizarResumen();
}

async function enviarCita(evento) {
  evento.preventDefault();
  ocultarMensaje();

  const faltantes = faltantesDeSeleccion();
  if (faltantes.length > 0) {
    mostrarMensaje("error", "Falta información para agendar la cita", faltantes);
    return;
  }

  if (!API_URL) {
    mostrarMensaje("error", "No se encontró la dirección de la API", ["Revisa que exista el archivo config.js"]);
    return;
  }

  const datos = datosDelFormulario();
  elementos.botonAgendar.disabled = true;

  try {
    const respuesta = await fetch(`${API_URL}/citas`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });
    const cuerpo = await respuesta.json().catch(() => ({}));

    if (respuesta.status === 201) {
      reiniciar();
      marcarPaso(4);
      mostrarMensaje("exito", "Cita confirmada", [
        `${datos.mascota}: ${datos.motivo}`,
        `${fechaLegible(datos.fecha)} a las ${datos.hora}`,
        `Enviaremos un recordatorio a ${datos.correo}`,
      ]);
      if (typeof window.cargarCitas === "function") {
        window.cargarCitas();
      }
    } else if (respuesta.status === 400) {
      mostrarMensaje("error", "Revisa los datos de la cita", cuerpo.errores || []);
    } else if (respuesta.status === 409) {
      mostrarMensaje("error", "Ese horario acaba de ser tomado", ["Elige otra hora para el mismo día o cambia de día."]);
      estado.hora = null;
      pintarHoras();
      actualizarResumen();
    } else {
      mostrarMensaje("error", "No pudimos agendar la cita", ["Intenta de nuevo en unos minutos."]);
    }
  } catch {
    mostrarMensaje("error", "No hay conexión con el servidor", ["Revisa tu conexión a internet e intenta de nuevo."]);
  } finally {
    elementos.botonAgendar.disabled = false;
  }
}

elementos.semanaAnterior.addEventListener("click", () => {
  estado.semana = Math.max(0, estado.semana - 1);
  pintarDias();
});

elementos.semanaSiguiente.addEventListener("click", () => {
  estado.semana = Math.min(SEMANAS_MAXIMAS - 1, estado.semana + 1);
  pintarDias();
});

elementos.formulario.addEventListener("submit", enviarCita);

document.addEventListener("DOMContentLoaded", () => {
  pintarMotivos();
  pintarDias();
  pintarHoras();
  actualizarResumen();
});

const tablaCitas = {
  cuerpo: document.querySelector("#tabla-citas tbody"),
  filtro: document.getElementById("filtro-fecha"),
  limpiar: document.getElementById("limpiar-filtro"),
  vacio: document.getElementById("citas-vacio"),
  mensaje: document.getElementById("mensaje-citas"),
};

function avisoCitas(tipo, texto) {
  tablaCitas.mensaje.className = `mensaje mensaje-${tipo}`;
  tablaCitas.mensaje.replaceChildren(crearElemento("strong", null, texto));
  tablaCitas.mensaje.hidden = false;
}

function ocultarAvisoCitas() {
  tablaCitas.mensaje.hidden = true;
  tablaCitas.mensaje.replaceChildren();
}

function filaCita(cita) {
  const activa = cita.estado === "ACTIVA";
  const fila = crearElemento("tr", activa ? null : "cita-cancelada");

  const valores = [
    fechaLegible(cita.fecha),
    cita.hora,
    cita.mascota,
    cita.especie,
    cita.dueno,
    cita.correo,
    cita.telefono,
  ];
  valores.forEach((valor) => fila.append(crearElemento("td", null, valor ?? "")));

  const celdaEstado = crearElemento("td");
  celdaEstado.append(
    crearElemento("span", `estado ${activa ? "estado-activa" : "estado-cancelada"}`, activa ? "Activa" : "Cancelada"),
  );
  fila.append(celdaEstado);

  const celdaAccion = crearElemento("td");
  if (activa) {
    const boton = crearElemento("button", "boton-cancelar", "Cancelar");
    boton.type = "button";
    boton.addEventListener("click", () => cancelarCita(cita.id, boton));
    celdaAccion.append(boton);
  }
  fila.append(celdaAccion);

  return fila;
}

async function cargarCitas() {
  if (!API_URL) {
    avisoCitas("error", "No hay una URL de la API configurada en config.js");
    return;
  }

  const fecha = tablaCitas.filtro.value;
  const url = fecha ? `${API_URL}/citas?fecha=${encodeURIComponent(fecha)}` : `${API_URL}/citas`;

  try {
    const respuesta = await fetch(url);
    if (!respuesta.ok) {
      throw new Error(`HTTP ${respuesta.status}`);
    }
    const citas = await respuesta.json();
    tablaCitas.cuerpo.replaceChildren(...citas.map(filaCita));
    tablaCitas.vacio.hidden = citas.length > 0;
  } catch {
    tablaCitas.cuerpo.replaceChildren();
    tablaCitas.vacio.hidden = true;
    avisoCitas("error", "No se pudieron cargar las citas. Intenta de nuevo.");
  }
}

async function cancelarCita(id, boton) {
  boton.disabled = true;
  ocultarAvisoCitas();

  try {
    const respuesta = await fetch(`${API_URL}/citas/${encodeURIComponent(id)}`, { method: "DELETE" });
    if (respuesta.status === 200) {
      avisoCitas("exito", "La cita fue cancelada");
    } else if (respuesta.status === 404) {
      avisoCitas("error", "La cita ya no existe");
    } else {
      throw new Error(`HTTP ${respuesta.status}`);
    }
    await cargarCitas();
    pintarHoras();
  } catch {
    avisoCitas("error", "No se pudo cancelar la cita. Intenta de nuevo.");
    boton.disabled = false;
  }
}

tablaCitas.filtro.addEventListener("change", () => {
  ocultarAvisoCitas();
  cargarCitas();
});

tablaCitas.limpiar.addEventListener("click", () => {
  tablaCitas.filtro.value = "";
  ocultarAvisoCitas();
  cargarCitas();
});

window.cargarCitas = cargarCitas;

document.addEventListener("DOMContentLoaded", cargarCitas);
