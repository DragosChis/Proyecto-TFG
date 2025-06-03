var cadenamensajes = []; // Array para almacenar los elementos del chat en orden cronológico

var jdnchat = (function() {
  // Elementos principales del DOM
  const chatToggle = document.getElementById('jdnchat-chatbot-toggle');         // Botón para abrir el chat
  const chatbotContainer = document.getElementById('jdnchat-chatbot-container'); // Contenedor principal del chatbot
  const closeChat = document.getElementById('jdnchat-chatbot-close');           // Botón para cerrar el chat
  const resetButton = document.getElementById('jdnchat-reset-button');           // Botón para reiniciar el chat
  const chatLog = document.getElementById('jdnchat-chat-log');                   // Elemento donde se muestran los mensajes
  const userInput = document.getElementById('jdnchat-user-input');               // Campo de texto donde el usuario escribe su mensaje
  const sendButton = document.getElementById('jdnchat-send-button');             // Botón para enviar el mensaje del usuario
  const suggestionBox = document.getElementById('jdnchat-suggestion-box');       // Caja para mostrar sugerencias de autocompletado
  const resetModal = document.getElementById("jdnchat-reset-modal");             // Modal de confirmación para reiniciar
  const confirmResetBtn = document.getElementById("confirmResetBtn");            // Botón de confirmación dentro del modal
  const cancelResetBtn = document.getElementById("cancelResetBtn");              // Botón para cancelar el reinicio dentro del modal

  // Variables de estado
  let chatHistory = [];                    // Historial de texto de la conversación (para IA o registros)
  let esperandoRespuestaLibre = false;     // Indica si el siguiente input es respuesta libre a una pregunta
  let siguienteAfterLibre = null;          // ID de la siguiente pregunta tras una respuesta libre
  let keywords = [];                       // Lista de palabras clave para autocompletado
  let soporteActivo = false;               // Bandera para saber si está activo el flujo de soporte
  let soporteCounter = 0;                  // Contador interno para el flujo de soporte
  let esperandoFormularioSoporte = false;  // Indica si se debe mostrar el formulario de soporte pronto
  let productosActivo = false;             // Bandera para saber si está activo el flujo de productos/presupuesto
  let productosCounter = 0;                // Contador interno para el flujo de productos/presupuesto
  let esperandoFormularioProductos = false;// Indica si se debe mostrar el formulario de productos pronto
  let formSubmitCount = 0;                 // Lleva cuenta de cuántos formularios se han enviado para evitar duplicados
  let tipoConsultaSeleccionada = "";       // Guarda el tipo de consulta que seleccionó el usuario (comercial, soporte, etc.)
  let jdnchatBubbleDiv = null;             // Referencia a la burbuja flotante de notificación (para mostrarse/ocultarse)
  let jdnchatBubbleTimeout = null;         // Timeout asociado a la burbuja flotante (para limpiarlo si es necesario)
  let wrapperPreguntaPendiente = null;     // Elemento DOM de la última pregunta pendiente (para “volver a la pregunta”)
  let preguntaPendienteIA = null;          // Objeto de la pregunta que está esperando respuesta de la IA
  let initialScrollStart = 0;              // Posición inicial de scroll para detectar cuándo mostrar/ocultar el botón “volver”
  let initialScrollEnd = 0;                // Extremo inferior inicial de la vista para observador de scroll
  let volverListenerAttached = false;      // Indica si ya se ha asociado el listener de scroll para el botón “volver a pregunta”

  // Variables para el flujo jerárquico (manejo de secciones y sub-flujos)
  let currentSection = null;               // Sección actual del chatbot (ej. Soporte, Comercial, Digitalizar)
  let currentFlow = null;                  // Flujo actual dentro de la sección (objeto con preguntas y opciones)
  let currentPregunta = null;              // Pregunta actual que se muestra en el flujo
  let stateStack = [];                     // Pila de estados previos (para función “borrarMensaje” y retroceder)
  let currentSectionData = null;           // Datos JSON cargados para la sección activa
  let digitalOptionsSelected = [];         // IDs de opciones seleccionadas en el flujo “Digitalizar mi negocio”
  let digitalFlows = [];                   // Cola de flujos pendientes en el modo multi-selección digital
  let digitalFlowsTexts = [];              // Cola de textos de las opciones seleccionadas (para historial)
  let digitalMultiIndex = 0;               // Índice interno para recorrer la cola de flujos digitales
  let isMultiDigital = false;              // Indica si actualmente estamos en modo multi-selección digital


  // Inicializa el chatbot, añadiendo event listeners y cargando palabras clave
function init() {
  console.log("Estoy en init");
  
  // Mostrar el chatbot al pulsar el icono de toggling
  if (chatToggle && chatbotContainer) {
    chatToggle.addEventListener('click', () => {
      chatbotContainer.classList.add('visible');    // Hacer visible el contenedor del chatbot
      chatToggle.style.display = 'none';            // Ocultar el botón de abrir chat
      if (!chatLog.hasChildNodes()) {               // Si no hay mensajes en el log, mostramos bienvenida
        mostrarMensajeBienvenida();
      }
    });
  }

  // Cerrar el chatbot al pulsar el botón de cerrar
  if (closeChat && chatbotContainer) {
    closeChat.addEventListener('click', () => {
      chatbotContainer.classList.remove('visible'); // Ocultar el contenedor del chatbot
      if (chatToggle) {
        chatToggle.style.display = 'block';         // Volver a mostrar el botón de abrir chat
      }
    });
  }

  // Mostrar/ocultar el modal de confirmación para reiniciar el chat
  resetButton.addEventListener('click', () => {
    if (resetModal.style.display === "flex") {
      ocultarModalReset();                          // Oculta el modal si ya está abierto
    } else {
      mostrarModalReset();                          // Muestra el modal si está cerrado
    }
  });

  // Confirmar reinicio: cerrar modal y resetear chat
  confirmResetBtn.addEventListener('click', () => {
    resetModal.style.display = "none";              // Ocultar modal de confirmación
    resetearChat();                                 // Reiniciar completamente el chat
  });

  // Cancelar reinicio: simplemente cerrar modal
  cancelResetBtn.addEventListener('click', () => {
    resetModal.style.display = "none";
  });

  // Cerrar el modal si se hace clic fuera de él
  document.addEventListener('click', function(event) {
    const modal = document.getElementById('jdnchat-reset-modal');
    const resetBtn = document.getElementById('jdnchat-reset-button');
    // Si el modal está abierto y el clic no es ni en el modal ni en el botón de reinicio, cerramos el modal
    if (modal.style.display === 'flex' && !modal.contains(event.target) && !resetBtn.contains(event.target)) {
      modal.style.display = 'none';
    }
  });

  // Ocultar mensaje informativo cuando el usuario hace scroll hacia abajo en el chat
  const infoMsg = document.getElementById('jdnchat-sistema-info');
  if (infoMsg && chatLog) {
    chatLog.addEventListener('scroll', () => {
      // Si el scroll vertical supera 30px, ocultamos el mensaje; si vuelve arriba, lo mostramos
      if (chatLog.scrollTop > 30) {
        infoMsg.classList.add('oculto');
      } else {
        infoMsg.classList.remove('oculto');
      }
    });
  }

  // Cargar lista de palabras clave desde el servidor para autocompletado
  fetch('http://localhost:5000/keywords')
    .then(response => response.json())
    .then(data => {
      // Si el servidor devuelve un objeto con 'keywords', lo usamos; si no, asumimos que la respuesta es el array directo
      keywords = data.keywords ? data.keywords : data;
    })
    .catch(error => console.error('Error fetching keywords:', error));

  // Asociar eventos al campo de entrada del usuario para autocompletado y atajos de teclado
  userInput.addEventListener('input', onInputChange);          // Al escribir, mostramos sugerencias
  userInput.addEventListener('keydown', onKeyDown);             // Para capturar tab y otras teclas
  userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();                                   // Evitar comportamiento predeterminado de Enter
      sendButton.click();                                        // Simular clic en el botón de enviar
      suggestionBox.textContent = "";                            // Limpiar sugerencia al enviar
    }
  });

  // Enviar mensaje al pulsar el botón de enviar
  sendButton.addEventListener('click', sendMessage);
}

  
  function addBotLogo(wrapper) {
    // Solo agrega el avatar si la burbuja pertenece al bot
    if (!wrapper.classList.contains('bot')) return;

    // Crear elemento <img> para el avatar
    const avatar = document.createElement('img');
    avatar.src   = 'img/logochat.png';      // Ruta al logo del bot (ajustar si es necesario)
    avatar.alt   = 'Bot Avatar';            // Texto alternativo para accesibilidad
    avatar.classList.add('jdnchat-bot-avatar'); // Clase para aplicar estilos al avatar

    // Insertar el avatar al principio de la burbuja de mensaje
    wrapper.insertBefore(avatar, wrapper.firstChild);
}

// Muestra un mensaje de bienvenida con opciones iniciales (sin botón "Atrás")
function mostrarMensajeBienvenida() {
    console.log("Estoy en mostrarMensajeBienvenida");
    const welcomeHTML = `
    <p style="margin:0;">¡Hola! ¿En qué podemos ayudarte?</p>
    <button class="jdnchat-chat-option"
      onclick="
        // Evitar múltiples selecciones simultáneas
        let usedButton = this.parentElement.querySelector('.jdnchat-chat-option.used');
        if (usedButton && usedButton !== this) return;

        // Marcar el botón como usado y seleccionado visualmente
        this.classList.add('used');
        var siblings = this.parentElement.querySelectorAll('.jdnchat-chat-option');
        siblings.forEach(s => s.classList.remove('selected'));
        this.classList.add('selected');

        // Llamar a la función para manejar la opción 'comercial'
        jdnchat.handleBotOption('comercial')
      ">
      Información Comercial
    </button>
    <button class="jdnchat-chat-option"
      onclick="
        // Evitar múltiples selecciones simultáneas
        let usedButton = this.parentElement.querySelector('.jdnchat-chat-option.used');
        if (usedButton && usedButton !== this) return;

        // Marcar el botón como usado y seleccionado visualmente
        this.classList.add('used');
        var siblings = this.parentElement.querySelectorAll('.jdnchat-chat-option');
        siblings.forEach(s => s.classList.remove('selected'));
        this.classList.add('selected');

        // Llamar a la función para manejar la opción 'soporte'
        jdnchat.handleBotOption('soporte')
      ">
      Soporte Técnico
    </button>
  `;
    // Mostrar el HTML de bienvenida en el chat (como código HTML)
    displayMessage(false, welcomeHTML, true);

    // Registrar en el historial que se mostró el mensaje de bienvenida
    chatHistory.push("Chatbot: ¡Hola! ¿En qué puedo ayudarte?");
}

// Manejar opciones jerárquicas desde el menú principal
function handleBotOption(opcion) {
    console.log("Estoy en handleBotOption", opcion);

    if (opcion === 'comercial') {
        // Cargar el archivo data.json y mostrar solo las dos primeras secciones (TPV y Digitalizar)
        fetch('data.json?t=' + Date.now())
            .then(res => res.json())
            .then(data => {
                // Obtener primeras dos secciones para mostrar como botones
                const secciones = data.secciones.slice(0, 2); // Ejemplo: TPV y Digitalizar
                const html = secciones.map(sec => `
          <button class="jdnchat-chat-option" onclick="
            // Evitar múltiples selecciones en la misma burbuja
            let usedButton = this.parentElement.querySelector('.jdnchat-chat-option.used');
            if (usedButton && usedButton !== this) return;
            this.classList.add('used');
            var siblings = this.parentElement.querySelectorAll('.jdnchat-chat-option');
            siblings.forEach(s => s.classList.remove('selected'));
            this.classList.add('selected');
            // Llamar a cargarSeccion con el archivo y título de la sección
            jdnchat.cargarSeccion('${sec.archivo}', '${sec.titulo}');
          ">
            ${sec.titulo}
          </button>
        `).join('');
                // Mostrar las opciones de secciones comerciales en el chat
                displayMessage(false, html, true, true);
                // Registrar opciones en el historial (solo título de secciones)
                chatHistory.push("Chatbot: Opciones comerciales - " + secciones.map(s => s.titulo).join(", "));
            })
            .catch(err => {
                console.error(err);
                // Si ocurre un error al cargar, mostrar mensaje de fallo al usuario
                displayMessage(false, "Error cargando opciones comerciales.", false, true);
            });
    }
    else if (opcion === 'soporte') {
        // Cargar el archivo data.json y buscar la sección "Soporte Tecnico"
        fetch('data.json?t=' + Date.now())
            .then(res => res.json())
            .then(data => {
                const sec = data.secciones.find(s => s.titulo === 'Soporte Tecnico');
                if (sec) {
                    // Si existe, cargar la sección de soporte
                    jdnchat.cargarSeccion(sec.archivo, sec.titulo);
                } else {
                    // Si no se encuentra la sección en el JSON, mostrar mensaje de error
                    displayMessage(false, "No se encontró la sección de soporte.", false, true);
                }
            })
            .catch(err => {
                console.error(err);
                // Mostrar mensaje de error si falla la petición fetch
                displayMessage(false, "Error cargando sección de soporte.", false, true);
            });
    }
}

// Exponer la función handleBotOption para que sea accesible desde el HTML inline
window.handleBotOption = handleBotOption;



  // Nueva función para cargar la sección dinámica desde su archivo externo
function cargarSeccion(archivo, tituloSeccion) {
  // Realiza un fetch al archivo JSON de la sección, agregando timestamp para evitar cache
  fetch(`${archivo}?t=${new Date().getTime()}`)
    .then(response => response.json())
    .then(data => {
      currentSectionData = data; // ✅ Aquí guardamos la data completa de ese archivo JSON
      // Buscar dentro del JSON la sección con el título indicado
      const seccionElegida = data.secciones.find(sec => sec.titulo === tituloSeccion);
      if (seccionElegida) {
        currentSection = seccionElegida;   // Guardar la sección seleccionada en el estado
        handleSeccion(tituloSeccion, data); // Lanzar el manejador de sección con los datos cargados
      } else {
        // Si no encuentra la sección en el JSON, mostrar mensaje de error al usuario
        displayMessage(false, "No se encontró la sección solicitada.", false, true);
      }
    })
    .catch(error => {
      console.error(`Error cargando el archivo ${archivo}:`, error);
      // Si el fetch falla (por red, permiso, etc.), avisar al usuario
      displayMessage(false, "Error cargando el módulo. Inténtalo más tarde.", false, true);
    });
}

// Manejar la selección de una sección (ej. "Hablar con comercial")
function handleSeccion(titulo, data = null) {
  console.log("Estoy en handleSeccion");

  // Si ya recibimos datos por parámetro, los usamos; si no, hacemos fetch a data.json
  const fetchData = data
    ? Promise.resolve(data) // Si data ya existe, envolverla en una promesa resuelta
    : fetch('data.json?t=' + new Date().getTime()).then(res => res.json());

  fetchData.then(finalData => {
    // Buscar en el JSON la sección que coincida con el título pasado
    const seccionElegida = finalData.secciones.find(sec => sec.titulo === titulo);
    if (seccionElegida && seccionElegida.inicios) {
      currentSection = seccionElegida; // Guardar la sección actual

      // ← Nuevo bloque: si sólo hay una opción de inicio, lanzamos directamente su flujo
      if (seccionElegida.inicios.length === 1) {
        // Simulamos que el usuario ha seleccionado esa única opción
        chatHistory.push("Usuario seleccionó: " + seccionElegida.inicios[0].opcion);
        jdnchat.handleInicio(0);
        return; // Salir para no dibujar botones si sólo hay un inicio
      }

      // Eliminar cualquier botón "Atrás" de mensajes anteriores antes de mostrar nuevas opciones
      cadenamensajes.forEach(message => {
        const rectifyBtn = message.querySelector('.jdnchat-rectify-btn');
        if (rectifyBtn) {
          rectifyBtn.remove();
        }
      });

      // Crear una nueva burbuja de mensaje del bot con las opciones de inicio
      const hora = obtenerHora(); // Obtener hora actual formateada
      const wrapper = document.createElement('div');
      wrapper.classList.add('jdnchat-message-wrapper', 'bot');
      addBotLogo(wrapper); // Agregar el avatar del bot al wrapper

      const messageDiv = document.createElement('div');
      messageDiv.classList.add('jdnchat-chat-message');

      // Para cada opción de inicio en la sección, crear un botón
      seccionElegida.inicios.forEach((inicio, index) => {
        const btn = document.createElement('button');
        btn.classList.add('jdnchat-chat-option');
        btn.textContent = inicio.opcion;
        btn.onclick = function () {
          // Registrar en historial la opción elegida
          chatHistory.push("Usuario seleccionó: " + inicio.opcion);
          // Evitar selección doble en la misma burbuja
          let usedButton = this.parentElement.querySelector('.jdnchat-chat-option.used');
          if (usedButton && usedButton !== this) return;
          this.classList.add('used'); // Marcar como pulsado
          var siblings = this.parentElement.querySelectorAll('.jdnchat-chat-option');
          siblings.forEach(s => s.classList.remove('selected'));
          this.classList.add('selected'); // Marcar visualmente
          jdnchat.handleInicio(index);   // Llamar a la función para manejar la opción seleccionada
        };
        messageDiv.appendChild(btn);
      });

      // Agregar botón "Atrás" para permitir retroceder si el usuario cambia de opinión
      const rectifyBtn = document.createElement('button');
      rectifyBtn.classList.add('jdnchat-rectify-btn');
      rectifyBtn.innerHTML = '<i class="fa-solid fa-arrow-left"></i>';
      rectifyBtn.onclick = function () {
        jdnchat.borrarMensaje(); // Llamar a la función para borrar el último mensaje y retroceder
      };
      messageDiv.appendChild(rectifyBtn);

      // Añadir la hora en la esquina del mensaje
      const hourSpan = document.createElement('span');
      hourSpan.classList.add('jdnchat-message-hour');
      hourSpan.textContent = hora;
      messageDiv.appendChild(hourSpan);

      // Insertar el messageDiv dentro del wrapper y luego en el chatLog
      wrapper.appendChild(messageDiv);
      chatLog.appendChild(wrapper);
      cadenamensajes.push(wrapper);       // Agregar el wrapper al array de mensajes
      scrollChatToBottom();               // Hacer scroll para mostrar la nueva burbuja

      // Registrar en el historial las opciones disponibles (solo texto)
      const opcionesTexto = seccionElegida.inicios.map(i => i.opcion).join(", ");
      chatHistory.push("Chatbot: Opciones - " + opcionesTexto);
    } else {
      // Si no existe la sección o no tiene inicios definidos, mostrarse mensaje de fallo
      displayMessage(false, "No se encontró la sección solicitada.", false, true);
    }
  })
  .catch(error => console.error('Error buscando sección:', error)); // Loguear en consola posibles errores de fetch
}

// Exponer la función handleSeccion para que pueda llamarse desde HTML inline
window.handleSeccion = handleSeccion;



  // Manejar la selección de una opción de "inicios"
function handleInicio(index) {
  console.log("Estoy en handleInicio, índice:", index);  // Log para depuración, muestra el índice seleccionado
  const inicio = currentSection.inicios[index];          // Obtener el objeto de inicio según el índice

  // ── Multi-selección para Digitalizar mi negocio ───────────────────────────
  if (currentSection.titulo === "Digitalizar mi negocio") {
    // Guardar estado actual para permitir retroceder si el usuario pulsa “Atrás”
    stateStack.push({ currentSection, currentFlow, currentPregunta });

    const hora    = obtenerHora();                               // Obtener hora actual formateada
    const wrapper = document.createElement("div");                // Crear contenedor de mensaje
    wrapper.classList.add("jdnchat-message-wrapper", "bot");      // Añadir clases de estilo
    addBotLogo(wrapper);                                          // Insertar logotipo del bot
    wrapper.setAttribute("data-unified", "true");                 // Marcar como mensaje unificado (para IA)

    const messageDiv = document.createElement("div");             // Crear contenedor interno de texto
    messageDiv.classList.add("jdnchat-chat-message");             // Añadir clase de estilo

    // Intro de la sección Digitalizar, mostrar el texto del mensaje
    const p = document.createElement("p");
    p.textContent = inicio.mensaje;                               // Texto explicativo almacenado en el JSON
    messageDiv.appendChild(p);

    // Checkboxes para múltiples opciones en Digitalizar mi negocio
    inicio.opciones.forEach(op => {
      const label = document.createElement("label");
      label.classList.add("jdnchat-digital-label");               // Clase para estilos específicos de checkboxes

      const cb = document.createElement("input");                 // Crear checkbox
      cb.type  = "checkbox";
      cb.classList.add("jdnchat-digital-checkbox");               // Clase para estilo de checkbox

      // Almacenar información necesaria en data-attributes del checkbox:
      // - next: el ID del flujo a lanzar cuando se envíe
      // - text: el texto legible para el historial
      // - srv: el identificador interno para enviar al backend
      cb.dataset.next = op.siguienteId;
      cb.dataset.text = op.opcion;
      cb.dataset.srv  = op.id;

      // Cuando cambie el estado del checkbox, alternar clase y habilitar/deshabilitar botón
      cb.onchange = () => {
        label.classList.toggle("jdnchat-digital-label--selected", cb.checked);
        const anyChecked = wrapper.querySelectorAll(
          ".jdnchat-digital-checkbox:checked"
        ).length > 0;                                           // Verificar si hay al menos un checkbox marcado
        contBtn.disabled = !anyChecked;                           // Deshabilitar botón si no hay ninguno marcado
      };

      // Permitir que al hacer clic en la etiqueta se marque el checkbox
      label.onclick = e => { if (e.target === label) cb.click(); };

      const span = document.createElement("span");               // Crear span para mostrar la opción
      span.textContent = op.opcion;                               // Texto de la opción

      label.appendChild(cb);                                      // Insertar checkbox dentro de la etiqueta
      label.appendChild(span);                                    // Insertar texto dentro de la etiqueta
      messageDiv.appendChild(label);                              // Añadir etiqueta al contenedor de mensaje
    });

    // Botón “Continuar” para procesar selección múltiple
    const contBtn = document.createElement("button");
    contBtn.id = "continuarDigitalBtn";                           // ID único para localizar el botón
    contBtn.classList.add("jdnchat-btn", "jdnchat-btn--primary"); // Clases para estilo de botón
    contBtn.textContent = "Continuar";                            // Texto del botón
    contBtn.disabled = true;                                       // Inicialmente deshabilitado
    contBtn.style.marginTop = "12px";                              // Espacio superior

    // Al hacer clic en “Continuar”, preparar la cola de flujos y enviar la primera pregunta
    contBtn.onclick = () => {
      const queue = [];                                            // Cola de objetos con id+texto
      const selectedIds = [];                                       // IDs que se enviarán al backend

      wrapper
        .querySelectorAll(".jdnchat-digital-checkbox:checked")     // Seleccionar checkboxes marcados
        .forEach(cb => {
          queue.push({
            id:   cb.dataset.next,                                 // Flujo jerárquico a ejecutar
            text: cb.dataset.text                                  // Texto para historial
          });
          selectedIds.push(cb.dataset.srv);                        // ID interno para backend
        });

      // Guardar en variables globales para utilizar en handlePregunta
      window._digitalQueue       = queue;
      window._digitalSelectedIds = selectedIds;

      // Extraer el siguiente flujo y llamarlo
      const next = window._digitalQueue.shift();
      jdnchat.handlePregunta(next.id, next.text);
    };

    messageDiv.appendChild(contBtn);                               // Añadir botón “Continuar” al mensaje

    // Añadir marca de hora al mensaje
    const hourSpan = document.createElement('span');
    hourSpan.classList.add('jdnchat-message-hour');
    hourSpan.textContent = hora;
    messageDiv.appendChild(hourSpan);

    wrapper.appendChild(messageDiv);                               // Insertar contenido en wrapper
    chatLog.appendChild(wrapper);                                  // Añadir wrapper al chat
    // Activar animación de aparición después de 30ms
    setTimeout(() => wrapper.classList.add('show'), 30);

    cadenamensajes.push(wrapper);                                  // Almacenar wrapper en array de mensajes
    scrollChatToBottom();                                          // Hacer scroll al final

    chatHistory.push("Chatbot: " + inicio.mensaje);                // Añadir texto al historial
    return;                                                        // Salir para no procesar el resto del código
  }

  // === Resto del handleInicio original ===

  // Si el objeto inicio contiene mensaje y opciones, renderizar botones para cada opción
  if (inicio.mensaje && inicio.opciones && inicio.opciones.length > 0) {
    // Guardar estado para permitir retroceder
    stateStack.push({ currentSection, currentFlow, currentPregunta });
    const hora = obtenerHora();
    const wrapper = document.createElement('div');
    wrapper.classList.add('jdnchat-message-wrapper', 'bot');
    addBotLogo(wrapper);                                          // Insertar avatar del bot
    wrapper.setAttribute("data-unified", "true");                 // Marcar el mensaje como unificado para IA

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('jdnchat-chat-message');

    const mensajeP = document.createElement('p');
    mensajeP.textContent = inicio.mensaje;                         // Texto principal del inicio
    messageDiv.appendChild(mensajeP);

    // Generar un botón para cada opción definida en el JSON
    inicio.opciones.forEach(op => {
      const btn = document.createElement('button');
      btn.classList.add('jdnchat-chat-option');
      btn.textContent = op.opcion;
      btn.onclick = function () {
        // Registrar en historial la pregunta y la respuesta seleccionada
        chatHistory.push(`[Pregunta]: ${inicio.mensaje}`);
        chatHistory.push(`Asistente Virtual: ${inicio.mensaje}`);
        chatHistory.push(`[Respuesta]: ${op.opcion}`);
        chatHistory.push(`Cliente: ${op.opcion}`);
        chatHistory.push("Usuario seleccionó: " + op.siguienteId);
        tipoConsultaSeleccionada = op.opcion || "";                 // Guardar texto de la opción

        // Evitar que se pulse otro botón en la misma burbuja
        let usedButton = this.parentElement.querySelector('.jdnchat-chat-option.used');
        if (usedButton && usedButton !== this) return;
        this.classList.add('used');
        var siblings = this.parentElement.querySelectorAll('.jdnchat-chat-option');
        siblings.forEach(s => s.classList.remove('selected'));
        this.classList.add('selected');                              // Marcar el botón visualmente

        jdnchat.handlePregunta(op.siguienteId, op.opcion);          // Llamar a handlePregunta con ID y texto
      };
      messageDiv.appendChild(btn);
    });

    // Quitar botones “Atrás” previos en todos los mensajes
    cadenamensajes.forEach(message => {
      const rectifyBtn = message.querySelector('.jdnchat-rectify-btn');
      if (rectifyBtn) rectifyBtn.remove();
    });

    // Añadir botón “Atrás” para retroceder
    const rectifyBtn = document.createElement('button');
    rectifyBtn.classList.add('jdnchat-rectify-btn');
    rectifyBtn.innerHTML = '<i class="fa-solid fa-arrow-left"></i>';
    rectifyBtn.onclick = function () {
      jdnchat.borrarMensaje();                                      // Llamar a borrarMensaje para retroceder
    };
    messageDiv.appendChild(rectifyBtn);

    // Añadir hora del mensaje
    const hourSpan = document.createElement('span');
    hourSpan.classList.add('jdnchat-message-hour');
    hourSpan.textContent = hora;
    messageDiv.appendChild(hourSpan);

    wrapper.appendChild(messageDiv);
    chatLog.appendChild(wrapper);

    // Activar animación de aparición
    setTimeout(() => wrapper.classList.add('show'), 30);

    cadenamensajes.push(wrapper);                                  // Añadir wrapper al array de mensajes
    scrollChatToBottom();                                          // Scroll automático

    // Añadir mensaje y opciones al historial
    chatHistory.push("Chatbot: " + inicio.mensaje);
    chatHistory.push("Chatbot: Opciones - " + inicio.opciones.map(op => op.opcion).join(", "));
  }
  // Si solo hay mensaje y no hay opciones, mostrar mensaje sin botones y avanzar automáticamente
  else if (inicio.mensaje) {
    stateStack.push({ currentSection, currentFlow, currentPregunta }); // Guardar estado previo
    displayMessage(false, inicio.mensaje, false, true);                // Mostrar el mensaje directamente
    chatHistory.push("Chatbot: " + inicio.mensaje);                     // Guardar en historial

    if (inicio.siguienteId) {
      // Si existe siguienteId, esperar 1 segundo y llamar recursivamente a handlePregunta
      setTimeout(() => {
        jdnchat.handlePregunta(inicio.siguienteId, inicio.opcion);
      }, 1000);
    }
  }
  // Si no hay texto pero hay opciones, renderizar botones con un formato simplificado
  else if (inicio.opciones && inicio.opciones.length > 0) {
    stateStack.push({ currentSection, currentFlow, currentPregunta }); // Guardar estado previo
    const opcionesHTML = inicio.opciones.map(op => {
      // Generar HTML string para cada botón
      return `
        <button class="jdnchat-chat-option" onclick="
          let usedButton = this.parentElement.querySelector('.jdnchat-chat-option.used');
          if (usedButton && usedButton !== this) { return; }
          this.classList.add('used');
          var siblings = this.parentElement.querySelectorAll('.jdnchat-chat-option');
          siblings.forEach(s => s.classList.remove('selected'));
          this.classList.add('selected');
          jdnchat.handlePregunta('${op.siguienteId}', '${op.opcion}')
        ">
          ${op.opcion}
        </button>`;
    }).join(' ');
    displayMessage(false, opcionesHTML, true, true);                     // Mostrar opciones como HTML
    chatHistory.push("Chatbot: Opciones - " + inicio.opciones.map(op => op.opcion).join(", "));
  }
  // Si el objeto inicio tiene un sub-flujo referenciado (inicio.siguiente.flujoId), iniciar dicho flujo
  else if (inicio.siguiente && inicio.siguiente.flujoId) {
    stateStack.push({ currentSection, currentFlow, currentPregunta }); // Guardar estado previo
    const data = currentSectionData;                                   // Datos JSON cargados para la sección
    if (!data || !data.flujos) {
      // Si no existen flujos definidos en los datos JSON, mostrar error
      displayMessage(false, "No se ha cargado correctamente el módulo.", false, true);
      return;
    }
    const flujo = data.flujos[inicio.siguiente.flujoId];               // Obtener flujo por ID
    if (flujo) {
      currentFlow = flujo;                                             // Guardar flujo actual
      if (flujo.mensaje && flujo.mensaje.trim()) {
        displayMessage(false, flujo.mensaje, false, true);             // Mostrar mensaje de introducción del flujo
        chatHistory.push("Chatbot: " + flujo.mensaje);                  // Guardar en historial
      }
      if (flujo.preguntas && flujo.preguntas.length) {
        currentPregunta = flujo.preguntas[0];                           // Establecer primera pregunta del flujo
        mostrarPregunta(currentPregunta);                               // Llamar a mostrar la primera pregunta
      }
    } else {
      // Si no se encuentra el flujo por ID, notificar al usuario
      displayMessage(false, "Flujo no encontrado.", false, true);
      chatHistory.push("Chatbot: Flujo no encontrado.");
    }
  }
  // Caso por defecto cuando ningún patrón anterior coincide: indicar implementación pendiente
  else {
    displayMessage(false, "Pendiente de implementación", false, true);
    chatHistory.push("Chatbot: Pendiente de implementación");
  }
}

// Exponer la función handleInicio para que pueda llamarse desde HTML inline
window.handleInicio = handleInicio;




  // MODIFICACIÓN EN handlePregunta PARA USAR currentSectionData

// Manejar la siguiente pregunta dentro del flujo actual
function handlePregunta(siguienteId, opcionText) {
  console.log("→ handlePregunta:", siguienteId, opcionText);
  console.log("   Cola actual:", window._digitalQueue);

  // ← NUEVO: si el siguienteId coincide con un flujo top-level, reiniciamos el flow anterior
  if (currentSectionData?.flujos?.[siguienteId]) {
    currentFlow = null; // Si existe un flujo en currentSectionData con esta ID, borramos el flujo activo anterior
  }

  // ← NUEVO: atajar el formulario de soporte
  if (siguienteId === "formularioSoporte") {
    mostrarFormularioContacto("soporte"); // Mostrar formulario de contacto para soporte técnico
    return; // Salir para no procesar más lógica
  }

  // Guardamos estado para poder retroceder (borrarMensaje)
  stateStack.push({ currentSection, currentFlow, currentPregunta });

  // ── 0) Inyectar resumen justo **antes** de mostrar el bloque “Gracias por la info…” ──
  // Estos son los IDs terminales de cada subflujo de Digitalizar
  const terminalIds = [
    "res_p2",      // Reservas
    "del_p3",      // Delivery
    "stk_p4",      // Stock y proveedores
    "rds_p6",      // Redes/Web
    "auto_p2",     // Automatización
    "ia_p2"        // IA
  ];
  if (
    currentSection?.titulo === "Digitalizar mi negocio" // Solo en la sección Digitalizar mi negocio
    && terminalIds.includes(siguienteId)                 // Si el siguienteId es uno de los terminales listados
    && window._digitalQueue                              // Y existe la cola de flujos digitales
    && window._digitalQueue.length === 0                  // Y la cola está vacía (último servicio)
  ) {
    // Llamamos a tu endpoint para obtener el resumen offline + precios/herramientas
    const payload = {
      historial: chatHistory.join("\n"),            // Enviar historial completo para context
      servicios: window._digitalSelectedIds         // IDs de servicios que seleccionó el usuario
    };
    fetch("http://localhost:5000/resumen-digital", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        // 1) Mostrar el resumen antes del “Gracias por la info…”
        displayMessage(
          false,
          data.summary.replace(/\n/g, "<br>"),   // Convertir saltos de línea a <br> para HTML
          true,                                  // isHtml = true para interpretar etiquetas <br>
          true
        );

        // 2) Ahora sí, seguimos al bloque de “Gracias por la info…” (mostrarPregunta)
        const preguntaObj = currentFlow
          ?.preguntas.find(q => q.id === siguienteId); // Buscar pregunta terminal en el flujo activo
        if (preguntaObj) {
          mostrarPregunta(preguntaObj); // Mostrar la pregunta terminal tras el resumen
        }
      })
      .catch(err => {
        console.error("Error en /resumen-digital:", err);
        // Fallback: si falla la llamada al servidor, simplemente mostrar la pregunta terminal
        const preguntaObj = currentFlow
          ?.preguntas.find(q => q.id === siguienteId);
        if (preguntaObj) {
          mostrarPregunta(preguntaObj);
        }
      });

    // No procesamos nada más hasta que el resumen y la pregunta se hayan mostrado
    return;
  }

  // ── Formularios especiales ───────────────────────────────────────────────
  if (siguienteId === "formularioDigitalizar") {
    // Si quedan más servicios en la cola, avanzamos al siguiente flujo
    if (window._digitalQueue && window._digitalQueue.length > 0) {
      const next = window._digitalQueue.shift(); // Obtener siguiente elemento de la cola
      console.log("   → Avanzando en la cola a:", next);
      currentFlow = null;                        // Reiniciar flujo para el siguiente servicio
      return jdnchat.handlePregunta(next.id, next.text); // Llamar recursivamente para el siguiente servicio
    }
    console.log("   → Cola vacía: mostrando formularioDigitalizar");
    // Si la cola está vacía, mostrar el formulario de digitalizar al usuario
    const html = `<p>Por favor, rellena tus datos para que te enviemos un resumen de la conversación:</p>` + getFormularioDigitalizarHTML();
    displayMessage(false, html, true, true);
    chatHistory.push("Chatbot: Te dejo el formulario de digitalizar...");
    setTimeout(attachFormularioDigitalizarListeners, 100); // Esperar para enganchar listeners al formulario
    delete window._digitalQueue; // Eliminar la cola para liberar memoria
    return;
  }

  if (siguienteId === "formularioPresupuesto") {
    // Mismo comportamiento que formularioDigitalizar pero para presupuesto
    if (window._digitalQueue && window._digitalQueue.length > 0) {
      const next = window._digitalQueue.shift();
      console.log("   → Cola activa tras presupuesto, avanzo a:", next);
      currentFlow = null;
      return jdnchat.handlePregunta(next.id, next.text);
    }
    // Si no hay más servicios, mostrar el formulario de presupuesto
    const html = `<p>Te dejo un formulario para que me pases tus datos de contacto y del negocio. Así te envío el presupuesto por correo.</p>` + getFormularioProductosHTML();
    displayMessage(false, html, true, true);
    chatHistory.push("Chatbot: Te dejo un formulario para que me pases tus datos...");
    // ← Cambio aquí: 0 ms para asegurar que el formulario existe en el DOM antes de enganchar el listener
    setTimeout(() => attachFormularioProductosListeners(), 0);
    delete window._digitalQueue; // Eliminar la cola de la sesión
    return;
  }

  // ── IDs especiales como volver_inicio y fin_chat ─────────────────────────
  if (siguienteId === 'volver_inicio') {
    resetearChat(); // Reiniciar el chat completamente
    return;
  }

  if (siguienteId === "fin_chat") {
    displayMessage(false, "Gracias por usar nuestro servicio. ¡Hasta pronto!"); // Mensaje de despedida
    return;
  }

  // ── Especiales de flujo jerárquico ───────────────────────────────────────
  if (siguienteId === "pregunta_tpv" && currentSection?.titulo === "Digitalizar mi negocio") {
    // Si la pregunta es 'pregunta_tpv' y estamos en Digitalizar mi negocio, disparar flujo TPV
    const flujoTPV = currentSectionData?.flujos?.digital_tpv;
    if (flujoTPV) {
      currentFlow = flujoTPV;                                    // Guardar el flujo TPV activo
      const pregunta = flujoTPV.preguntas.find(q => q.id === "pregunta_tpv"); // Encontrar la pregunta por ID
      return mostrarPregunta(pregunta);                          // Mostrar la pregunta TPV
    }
  }

  if (siguienteId === "ayudaAdicional") {
    currentFlow = null; // Reiniciar flujo activo para buscar pregunta suelta

    if (!currentSectionData) {
      return displayMessage(false, "Módulo no cargado correctamente. Inténtalo de nuevo.", false, true);
    }

    // Buscar entre todos los flujos de la sección la pregunta con id 'ayudaAdicional'
    const allFlows = Object.values(currentSectionData.flujos || {});
    for (const flujo of allFlows) {
      const pregunta = flujo.preguntas?.find(p => p.id === "ayudaAdicional");
      if (pregunta) return mostrarPregunta(pregunta);
    }

    // Si no se encuentra en ningún flujo, comprobar si existe como pregunta suelta en la sección
    const preguntaSuelta = currentSectionData.preguntas?.find(p => p.id === "ayudaAdicional");
    if (preguntaSuelta) return mostrarPregunta(preguntaSuelta);

    // Si no existe en ningún sitio, mostrar mensaje de error
    return displayMessage(false, "No se encontró la pregunta de ayuda adicional.", false, true);
  }

  // ── Si hay flujo activo, avanzamos dentro de él ───────────────────────────
  if (currentFlow) {
    // Intentar encontrar la siguiente pregunta dentro del flujo actual
    const nextQ = currentFlow.preguntas.find(q => q.id === siguienteId);
    if (nextQ) {
      // Determinar si la pregunta es terminal (todas sus opciones llevan a formularios o ayuda adicional)
      const esTerminal = nextQ.opciones
        && nextQ.opciones.length > 0
        && nextQ.opciones.every(op =>
          op.siguienteId === "formularioPresupuesto" ||
          op.siguienteId === "ayudaAdicional" ||
          op.siguienteId === "formularioDigitalizar"
        );
      if (esTerminal && window._digitalQueue && window._digitalQueue.length > 0) {
        // Si es terminal pero aún quedan servicios en la cola, avanzar al siguiente servicio
        const siguiente = window._digitalQueue.shift();
        console.log("   → Terminal y queda cola, avanzo a:", siguiente);
        currentFlow = null; // Reiniciar flujo para saltar al siguiente
        return jdnchat.handlePregunta(siguiente.id, siguiente.text);
      }
      currentPregunta = nextQ; // Establecer la siguiente pregunta activa
      return mostrarPregunta(nextQ); // Mostrarla
    }
  }

  // ── Si no hay flujo activo, arrancamos uno nuevo ─────────────────────────
  if (!currentFlow) {
    if (!currentSectionData?.flujos) {
      displayMessage(false, "No se ha cargado el módulo correctamente. Inténtalo de nuevo.", false, true);
      return;
    }
    // Intentar iniciar un flujo cuyo ID coincide con siguienteId
    const flujo = currentSectionData.flujos[siguienteId];
    if (flujo) {
      currentFlow = flujo; // Guardar el flujo activo
      if (flujo.mensaje?.trim()) {
        displayMessage(false, flujo.mensaje, false, true);     // Mostrar mensaje de introducción del flujo
        chatHistory.push("Chatbot: " + flujo.mensaje);          // Guardar en historial
      }
      if (flujo.preguntas?.length) {
        currentPregunta = flujo.preguntas[0]; // Establecer primera pregunta del nuevo flujo
        return mostrarPregunta(currentPregunta); // Mostrarla
      }
      return;
    }
  }

  // ── Si llegamos hasta aquí, no hay nada que hacer ────────────────────────
  displayMessage(false, "Flujo no encontrado.", false, true); // Mostrar mensaje genérico de error
  chatHistory.push("Chatbot: Flujo no encontrado.");          // Guardar en historial de depuración
}

window.handlePregunta = handlePregunta; // Exponer la función para uso externo (HTML inline u otros módulos)










// FUNCIÓN REUTILIZABLE PARA MOSTRAR UNA PREGUNTA
function mostrarPregunta(pregunta) {
  const hora = obtenerHora(); // Obtener la hora actual formateada
  const wrapper = document.createElement('div');
  wrapper.classList.add('jdnchat-message-wrapper', 'bot', 'jdnchat-fade-in'); // Clases para el contenedor de mensaje y animación
  addBotLogo(wrapper); // Agregar el avatar del bot al wrapper
  wrapper.setAttribute("data-unified", "true"); // Marcar la burbuja como parte del flujo unificado para IA

  const messageDiv = document.createElement('div');
  messageDiv.classList.add('jdnchat-chat-message'); // Clase para la burbuja de texto

  // Texto de la pregunta
  const preguntaP = document.createElement('p');
  // Reemplazar saltos de línea por <br> para conservar formato
  preguntaP.innerHTML = pregunta.pregunta.replace(/\n/g, "<br>");
  messageDiv.appendChild(preguntaP);

  // ——— NUEVO: respuesta libre ———
  if (pregunta.respuesta_libre) {
    // Activar flag para que sendMessage() capture la siguiente entrada como respuesta libre
    esperandoRespuestaLibre = true;
    siguienteAfterLibre     = pregunta.siguienteId || null; // Guardar siguienteId para continuar después de la respuesta

    // Pista al usuario para que escriba su respuesta en el campo de texto
    const aviso = document.createElement('p');
    aviso.style.fontStyle = 'italic';
    aviso.style.fontSize  = '0.85rem';
    aviso.textContent = '✏️ Por favor escribe tu respuesta en el campo de abajo y pulsa enviar.';
    messageDiv.appendChild(aviso);
  }
  // ——— resto del código solo si NO es respuesta libre ———
  else if (pregunta.opciones && pregunta.opciones.length > 0) {
    // Si existen opciones predefinidas, crear un botón para cada opción
    pregunta.opciones.forEach(op => {
      const btn = document.createElement('button');
      btn.classList.add('jdnchat-chat-option'); // Clase para estilo del botón
      btn.textContent = op.opcion;              // Texto visible en el botón
      btn.onclick = function () {
        // Registrar en historial la interacción: pregunta y respuesta seleccionada
        chatHistory.push(`[Pregunta]: ${pregunta.pregunta}`);
        chatHistory.push(`Asistente Virtual: ${pregunta.pregunta}`);
        chatHistory.push(`[Respuesta]: ${op.opcion}`);
        chatHistory.push(`Cliente: ${op.opcion}`);
        chatHistory.push("Usuario seleccionó: " + op.siguienteId);

        // Evitar que el usuario pulse múltiples opciones simultáneamente
        let usedButton = this.parentElement.querySelector('.jdnchat-chat-option.used');
        if (usedButton && usedButton !== this) return;

        this.classList.add('used'); // Marcar botón como usado
        const siblings = this.parentElement.querySelectorAll('.jdnchat-chat-option');
        siblings.forEach(s => s.classList.remove('selected')); // Limpiar selección previa
        this.classList.add('selected'); // Marcar este botón como seleccionado

        jdnchat.handlePregunta(op.siguienteId, op.opcion); // Llamar a handlePregunta con ID y texto
      };
      messageDiv.appendChild(btn);
    });
  }

  // Elimina botones de rectificación previos en todas las burbujas
  cadenamensajes.forEach(message => {
    const rectifyBtn = message.querySelector('.jdnchat-rectify-btn');
    if (rectifyBtn) rectifyBtn.remove();
  });

  // Añade botón de rectificación para poder retroceder
  const rectifyBtn = document.createElement('button');
  rectifyBtn.classList.add('jdnchat-rectify-btn'); // Clase para el botón “Atrás”
  rectifyBtn.innerHTML = '<i class="fa-solid fa-arrow-left"></i>'; // Ícono de flecha
  rectifyBtn.onclick = function () {
    jdnchat.borrarMensaje(); // Al hacer clic, llamar a la función para eliminar el último mensaje
  };
  messageDiv.appendChild(rectifyBtn);

  // Hora del mensaje
  const hourSpan = document.createElement('span');
  hourSpan.classList.add('jdnchat-message-hour'); // Clase para estilo de hora
  hourSpan.textContent = hora;                    // Mostrar hora obtenida
  messageDiv.appendChild(hourSpan);

  wrapper.appendChild(messageDiv); // Insertar contenido en el contenedor principal
  chatLog.appendChild(wrapper);    // Añadir la burbuja al log del chat

  // ← Activar animación suave tras breve retardo
  setTimeout(() => wrapper.classList.add('show'), 30);

  cadenamensajes.push(wrapper); // Guardar la nueva burbuja en el array de mensajes
  scrollChatToBottom();         // Hacer scroll para mostrar la nueva burbuja

  // Histórico de chat
  chatHistory.push("Chatbot: " + pregunta.pregunta);
  if (!pregunta.respuesta_libre && pregunta.opciones && pregunta.opciones.length > 0) {
    // Si no era respuesta libre y hay opciones, registrar las opciones en historial
    chatHistory.push("Chatbot: Opciones - " + pregunta.opciones.map(o => o.opcion).join(", "));
  } else if (!pregunta.respuesta_libre && pregunta.siguienteId) {
    // Si no es respuesta libre y existe siguienteId, avanzar automáticamente tras 3s
    setTimeout(() => {
      jdnchat.handlePregunta(pregunta.siguienteId, "");
    }, 3000);
  }

  // 🔥 ACTUALIZAR PREGUNTA PENDIENTE (SOLUCIÓN)
  wrapperPreguntaPendiente = wrapper;  // Guardar referencia a la burbuja actual
  preguntaPendienteIA      = pregunta; // Guardar objeto pregunta para “volver a” si es IA

  // 🔥 MOSTRAR BOTÓN DESDE PREGUNTA (incluso sin IA)
  mostrarBotonVolverPregunta(); // Mostrar botón flotante para regresar a esta pregunta
}




  // Autocompletado ghost text
function onInputChange() {
  console.log("Estoy en onInputChange");
  const typed = userInput.value; // Obtener texto escrito por el usuario
  if (!typed || typed.length < 3) {
    // Si no hay texto o es muy corto, limpiar sugerencias
    suggestionBox.textContent = "";
    return;
  }
  // Buscar palabra clave que comience con el texto tecleado (sin diferenciar mayúsculas/minúsculas)
  const match = keywords.find(word => word.toLowerCase().startsWith(typed.toLowerCase()));
  if (match) {
    // Si hay coincidencia, separar la parte ya escrita y la parte sobrante
    const leftover = match.slice(typed.length);
    // Mostrar la sugerencia resaltando la parte sobrante en gris
    suggestionBox.innerHTML = `<span style="color:#000;">${typed}</span><span style="color:#999;">${leftover}</span>`;
  } else {
    // Si no hay coincidencia, limpiar sugerencias
    suggestionBox.textContent = "";
  }
}

// Manejar eventos de teclado en el input del usuario
function onKeyDown(e) {
  if (e.key === 'Tab' && suggestionBox.textContent) {
    // Si el usuario pulsa Tab y hay sugerencia, completar el texto con la sugerencia
    e.preventDefault();
    userInput.value = suggestionBox.textContent;
    suggestionBox.textContent = ""; // Limpiar sugerencia una vez completado
  }
  if (e.key === 'Enter') {
    // Al pulsar Enter, limpiar la sugerencia (para que no interfiera en el envío)
    suggestionBox.textContent = "";
  }
}

// Desplazar el chat hasta el final
function scrollChatToBottom() {
  const lastMsg = chatLog.lastElementChild; // Obtener el último mensaje en el log
  if (lastMsg) {
    // Hacer scroll suave hasta el último mensaje
    lastMsg.scrollIntoView({ behavior: "smooth", block: "start" });
    setTimeout(() => {
      // Ajuste fino: subir 20px para que el encabezado del mensaje quede visible
      chatLog.scrollBy({ top: -20, behavior: "smooth" });
    }, 200);
  }
}

// Limpiar el historial de chat
function clearChatLog() {
  chatLog.innerHTML = ""; // Vaciar todo el contenido del contenedor de mensajes
}

// Obtener la hora actual en formato legible
function obtenerHora() {
  const now = new Date();
  // Formatear la hora en formato de 2 dígitos (HH:MM) en español
  return now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

function mostrarDivisorReinicio() {
  // Crear un divisor visual que indique el inicio de una nueva conversación
  const wrapper = document.createElement('div');
  wrapper.classList.add('jdnchat-divider-wrapper'); // Clase para estilos de divisor
  wrapper.innerHTML = `
    <div class="jdnchat-divider-line"></div>
    <span class="jdnchat-divider-text">Nueva conversación</span>
    <div class="jdnchat-divider-line"></div>`;
  chatLog.appendChild(wrapper);     // Añadir el divisor al final del chat
  scrollChatToBottom();             // Asegurarse de hacer scroll para mostrar el divisor
}

// Función para mostrar un mensaje en el chat
function displayMessage(isUser, text, isHtml = false, addRectify = false) {
  console.log("Estoy en displaymessage");
  const hora = obtenerHora(); // Obtener hora actual formateada
  const wrapper = document.createElement('div');
  // Añadir clases según si es mensaje de usuario o del bot, y clase de animación
  wrapper.classList.add('jdnchat-message-wrapper', isUser ? 'user' : 'bot', 'jdnchat-fade-in');
  addBotLogo(wrapper);         // Insertar el avatar del bot si corresponde

  const messageDiv = document.createElement('div');
  messageDiv.classList.add('jdnchat-chat-message'); // Clase para la burbuja de texto

  if (isHtml) {
    // Si el contenido es HTML, asignarlo directamente
    messageDiv.innerHTML = text;
  } else {
    // Si no es HTML, asignar como texto plano
    messageDiv.textContent = text;
  }

  // Añadir botón "Atrás" si corresponde (solo para mensajes de bot que no sean bienvenida)
  if (!isUser && addRectify && !text.includes("¡Hola! ¿En qué puedo ayudarte?")) {
    // Eliminar cualquier botón "Atrás" previo antes de añadir uno nuevo
    cadenamensajes.forEach(message => {
      const rectifyBtn = message.querySelector('.jdnchat-rectify-btn');
      if (rectifyBtn) {
        rectifyBtn.remove();
      }
    });
    // Crear nuevo botón "Atrás"
    const rectifyBtn = document.createElement('button');
    rectifyBtn.classList.add('jdnchat-rectify-btn');
    rectifyBtn.innerHTML = '<i class="fa-solid fa-arrow-left"></i>'; // Ícono de Flecha
    rectifyBtn.onclick = function () {
      jdnchat.borrarMensaje(); // Llamar a la función para retroceder
    };
    messageDiv.appendChild(rectifyBtn);
  }

  wrapper.appendChild(messageDiv); // Insertar contenido en el wrapper principal

  // Añadir la hora al mensaje
  const hourSpan = document.createElement('span');
  hourSpan.classList.add('jdnchat-message-hour'); // Clase para estilo de hora
  hourSpan.textContent = hora;                    // Mostrar hora obtenida
  messageDiv.appendChild(hourSpan);

  cadenamensajes.push(wrapper); // Guardar la burbuja en el array de mensajes
  console.log("Mensajes acumulados:", cadenamensajes);
  chatLog.appendChild(wrapper); // Añadir la burbuja al log del chat

  // Activar animación de aparición después de unos milisegundos
  setTimeout(() => wrapper.classList.add('show'), 30);

  scrollChatToBottom(); // Hacer scroll para mostrar el mensaje recién añadido
}





  // Función auxiliar para agregar el botón "Atrás" en la nueva última burbuja
function agregarBotonAtrasAlUltimoMensaje() {
  if (cadenamensajes.length > 0) {
    const nuevoUltimo = cadenamensajes[cadenamensajes.length - 1]; // Obtener la última burbuja
    if (nuevoUltimo.classList.contains('bot')) { // Solo si es un mensaje del bot
      const messageDiv = nuevoUltimo.querySelector('.jdnchat-chat-message');
      // Si no hay ya un botón de rectificación y no es el mensaje de bienvenida
      if (!messageDiv.querySelector('.jdnchat-rectify-btn') && !messageDiv.textContent.includes("¡Hola! ¿En qué puedo ayudarte?")) {
        const rectifyBtn = document.createElement('button');
        rectifyBtn.classList.add('jdnchat-rectify-btn'); // Clase para el botón “Atrás”
        rectifyBtn.innerHTML = '<i class="fa-solid fa-arrow-left"></i>'; // Ícono flecha
        rectifyBtn.onclick = function() {
          jdnchat.borrarMensaje(); // Al pulsar, llama a borrarMensaje para retroceder
        };
        messageDiv.appendChild(rectifyBtn); // Añadir el botón al mensaje
      }
    }
  }
}

// Enviar un mensaje al servidor y mostrar la respuesta
async function sendMessage() {
  console.log("Estoy en sendMessage");
  const msg = userInput.value.trim(); // Obtener y limpiar el valor del input
  if (!msg) return; // Si está vacío, no hacer nada

  // ——— Captura de RESPUESTA LIBRE ———
  if (esperandoRespuestaLibre) {
    displayMessage(true, msg);              // Mostrar mensaje de usuario
    chatHistory.push("Usuario: " + msg);    // Guardar en historial

    esperandoRespuestaLibre = false;        // Desactivar flag de respuesta libre
    const nextId = siguienteAfterLibre;     // Obtener ID de la siguiente pregunta
    siguienteAfterLibre = null;             // Limpiar la variable

    jdnchat.handlePregunta(nextId, msg);    // Llamar handlePregunta con la respuesta libre
    userInput.value = '';                   // Limpiar input
    suggestionBox.textContent = '';         // Limpiar sugerencia
    return;                                 // Salir para no procesar más lógica
  }

  // ——— Lógica base ———
  displayMessage(true, msg);                // Mostrar mensaje de usuario en la interfaz
  chatHistory.push("Usuario: " + msg);      // Guardar en historial
  userInput.value = '';                     // Limpiar el campo de texto
  suggestionBox.textContent = "";           // Limpiar la sugerencia de autocompletado

  // Condición para saber si estamos en un área IA
  const seccionIA = chatHistory.some(h =>
    h.includes("TPV") ||
    h.includes("Soporte técnico") ||
    h.includes("Digitalizar mi negocio")
  );
  const sinFlujoActivo = !currentFlow && !currentPregunta; // Verificar si no hay flujo o pregunta activa

  // ——— ESCENARIO 1: No se ha iniciado el flujo, redirigir ———
  if (seccionIA && sinFlujoActivo) {
    // Construir contexto para la IA, indicando que solo debe redirigir al menú
    const contexto = `IMPORTANTE: El usuario ha escrito directamente sin seleccionar ninguna opción del menú jerárquico.

Tu única función es identificar, a partir de su mensaje, cuál de las opciones visibles en el menú es la más adecuada.

NO DEBES resolver el problema. NO DEBES sugerir servicios generales como "Servicios Digitales".

Simplemente responde de forma amable indicando al usuario cuál de las opciones del menú debe pulsar. Usa el nombre exacto de la opción.

Ejemplos:
- Si el usuario dice "mi impresora no funciona", responde: "Para solucionar el problema con tu impresora, haz clic en la opción «Mi impresora no funciona» del menú."
- Si dice "quiero implementar IA", responde: "Para implementar IA, haz clic en la opción «Agentes y uso de la IA» del menú."

Adapta la redirección de forma personalizada, sin explicar nada más.

Ahora responde a esta consulta:`;

    const promptModificado = `${contexto}\n\nConsulta del usuario: ${msg}`;

    try {
      // Enviar petición a endpoint /generate con prompt y historial
      const res = await fetch('http://localhost:5000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptModificado, chat_history: chatHistory })
      });
      const data = await res.json();

      if (data.response) {
        displayMessage(false, data.response, false, true); // Mostrar respuesta de redirección
        chatHistory.push("Chatbot: " + data.response);    // Guardar en historial
      } else {
        displayMessage(false, "No se pudo obtener una respuesta.", false, true);
      }
    } catch (error) {
      console.error("Error:", error);
      displayMessage(false, "Error al procesar la solicitud.", false, true);
    }
    return; // Salir tras procesar escenario 1
  }

  // ——— ESCENARIO 2: Flujo activo, responder libremente y ofrecer volver a pregunta ———
  if (seccionIA && currentFlow && currentPregunta) {
    try {
      // 1) Capturamos la última pregunta de IA para permitir “volver a pregunta”
      wrapperPreguntaPendiente = Array.from(
        document.querySelectorAll('.jdnchat-message-wrapper.bot[data-unified="true"]')
      ).pop();
      preguntaPendienteIA = currentPregunta; // Guardar objeto de la pregunta

      // 2) Enviar entrada del usuario a la IA para obtener respuesta contextual
      const res = await fetch('http://localhost:5000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: msg, chat_history: chatHistory })
      });
      const data = await res.json();
      if (!data.response) {
        displayMessage(false, "No se pudo obtener una respuesta.", false, true);
        return; // Si no hay respuesta de IA, terminar
      }

      // 3) Mostrar la respuesta generada por la IA en el chat
      displayMessage(false, data.response, false, true);
      chatHistory.push("Chatbot: " + data.response); // Guardar en historial

      // 4) Tras mostrar la respuesta, activar botón para volver a la pregunta inicial
      setTimeout(() => {
        mostrarBotonVolverPregunta();
      }, 100);
    } catch (error) {
      console.error("Error:", error);
      displayMessage(false, "Error al procesar la solicitud.", false, true);
    }
    return; // Salir tras procesar escenario 2
  }
}




function borrarMensaje() {
  if (cadenamensajes.length === 0) return; // Si no hay mensajes, no hacer nada

  // Eliminar el último mensaje visual del DOM
  const ultimo = cadenamensajes.pop();
  if (ultimo && ultimo.remove) {
    ultimo.remove();
  }

  // Eliminar también del historial de texto el último "Usuario seleccionó:"
  while (chatHistory.length > 0) {
    const last = chatHistory[chatHistory.length - 1];
    if (last.startsWith("Usuario seleccionó:")) {
      chatHistory.pop(); // Encontrado, eliminar esa línea y salir del bucle
      break;
    } else {
      chatHistory.pop(); // Si no es "Usuario seleccionó:", eliminar igualmente (puede ser IA o pregunta)
    }
  }

  // Restaurar el estado anterior (sección, flujo y pregunta) desde la pila stateStack
  const prev = stateStack.pop();
  if (prev) {
    currentSection = prev.currentSection;
    currentFlow = prev.currentFlow;
    currentPregunta = prev.currentPregunta;
  } else {
    // Si no queda ningún estado previo, reiniciar variables de sección/flujo/pregunta
    currentSection = currentFlow = currentPregunta = null;
  }

  // Restaurar botón y opciones en la nueva última burbuja, si existe
  if (cadenamensajes.length > 0) {
    const nuevoUltimo = cadenamensajes[cadenamensajes.length - 1];
    // Obtener todos los botones de opciones en la última burbuja
    const optionButtons = nuevoUltimo.querySelectorAll('.jdnchat-chat-option');

    optionButtons.forEach(btn => {
      btn.disabled = false;         // Habilitar de nuevo el botón
      btn.classList.remove('used'); // Quitar clase 'used'
      btn.classList.remove('selected'); // Quitar clase 'selected'
    });

    // Añadir botón "Atrás" si no existe en la nueva última burbuja
    const messageDiv = nuevoUltimo.querySelector('.jdnchat-chat-message');
    if (!messageDiv.querySelector('.jdnchat-rectify-btn')) {
      const rectifyBtn = document.createElement('button');
      rectifyBtn.classList.add('jdnchat-rectify-btn');
      rectifyBtn.innerHTML = '<i class="fa-solid fa-arrow-left"></i>'; // Ícono de flecha
      rectifyBtn.onclick = function () {
        jdnchat.borrarMensaje(); // Al pulsar, llamar de nuevo a borrarMensaje
      };
      messageDiv.appendChild(rectifyBtn);
    }

    // 🔥 Si el mensaje eliminado era la pregunta pendiente de IA, actualizar referencias
    if (ultimo === wrapperPreguntaPendiente) {
      wrapperPreguntaPendiente = nuevoUltimo; // Ahora la nueva última burbuja es la pendiente
      preguntaPendienteIA = null; // Limpiar la pregunta pendiente (podría recuperarse si se desea)
    }
  } else {
    // Si ya no quedan mensajes, limpiar referencias y ocultar botón "Volver a pregunta"
    wrapperPreguntaPendiente = null;
    preguntaPendienteIA = null;
    ocultarBotonVolverPregunta();
  }
}






  // Función para mostrar una pregunta de confirmación (mensaje temporal) al usuario
function mostrarFormularioPregunta(modo) {
  let pregunta = "";
  if (modo === "soporte") {
    // Si el modo es soporte, establecemos el texto de pregunta correspondiente
    pregunta = "¿Quieres contactar con uno de nuestros profesionales para dar solución al problema?";
    esperandoFormularioSoporte = true; // Activar flag para mostrar formulario de soporte luego
  } else if (modo === "productos") {
    // Si el modo es productos, establecemos la pregunta adecuada
    pregunta = "¿Quieres que uno de nuestros profesionales se ponga en contacto contigo para continuar con la contratación?";
    esperandoFormularioProductos = true; // Activar flag para mostrar formulario de productos luego
  }
  displayMessage(false, pregunta); // Mostrar la pregunta en el chat
  chatHistory.push("Chatbot: " + pregunta); // Guardar la pregunta en historial
}

// =====================================================================
// NUEVAS FUNCIONES PARA EL FORMULARIO DE PRODUCTOS EN LA MISMA BURBUJA
// =====================================================================

// Función que retorna el HTML del formulario de productos
function getFormularioProductosHTML() {
  return `
      <div class="jdnchat-form-container">
        <form id="jdnchat-formulario" class="jdnchat-formulario">
          <label>Nombre: <span class="jdnchat-obligatorio">*</span>
            <input type="text" name="nombre" placeholder="Inserta tu nombre" required>
          </label>
          <label>Apellidos: <span class="jdnchat-obligatorio">*</span>
            <input type="text" name="apellidos" placeholder="Inserta tus apellidos" required>
          </label>
          <label>Negocio: <span class="jdnchat-obligatorio">*</span>
            <input type="text" name="negocio" placeholder="Inserta el nombre de tu negocio" required>
          </label>
          <label>Ciudad: <span class="jdnchat-obligatorio">*</span>
            <input type="text" name="ciudad" placeholder="Inserta la ciudad" required>
          </label>
          <label>Provincia: <span class="jdnchat-obligatorio">*</span>
            <input type="text" name="provincia" placeholder="Inserta la provincia" required>
          </label>
          <label>Código Postal: <span class="jdnchat-obligatorio">*</span>
            <input type="text" name="cp" placeholder="Inserta el CP" required>
          </label>
          <label>Correo electrónico: <span class="jdnchat-obligatorio">*</span>
            <input type="email" name="email" placeholder="Inserta tu correo electrónico" required>
          </label>
          <label>Número de teléfono (opcional):
            <input type="tel" name="telefono" placeholder="Inserta tu número de teléfono">
          </label>
          <hr class="jdnchat-divider" />
          <div class="checkbox-wrapper-29">
            <label class="checkbox">
              <input type="checkbox" id="productos-privacidad" name="privacidad" class="checkbox__input" required>
              <span class="checkbox__label"></span>
              <span class="checkbox__text">
                Confirmo haber leído la <a href="https://sodire.es/privacy-policy" target="_blank">Política de Privacidad</a>
              </span>
            </label>
          </div>
          <button type="submit">Enviar</button>
        </form>
        <div class="jdnchat-spinner-outside" style="display:none;">
          <img src="img/enviando.gif" alt="Enviando" class="jdnchat-gif-enviando">
        </div>
        <div id="jdnchat-floating-bubble-container" class="jdnchat-floating-bubble-container"></div>
      </div>
    `;
}

// Función que muestra e inserta el formulario de soporte
function mostrarFormularioContacto(tipo) {
  // Construir el HTML del formulario de soporte
  const html = `
    <div class="jdnchat-form-container">
      <form id="formulario-soporte" class="jdnchat-formulario">
        <label>Nombre: <span class="jdnchat-obligatorio">*</span>
          <input type="text" id="soporte-nombre" name="nombre" required placeholder="Tu nombre">
        </label>
        <label>Apellidos: <span class="jdnchat-obligatorio">*</span>
          <input type="text" id="soporte-apellidos" name="apellidos" required placeholder="Tus apellidos">
        </label>
        <label>Email: <span class="jdnchat-obligatorio">*</span>
          <input type="email" id="soporte-email" name="email" required placeholder="Tu email">
        </label>
        <label>Teléfono:
          <input type="tel" name="telefono" placeholder="Tu teléfono (opcional)">
        </label>
        <label>Nombre del local: <span class="jdnchat-obligatorio">*</span>
          <input type="text" id="soporte-local" name="local" required placeholder="Ej. Bar Pepe" />
        </label>
        <label>Resuma su incidencia: <span class="jdnchat-obligatorio">*</span>
          <textarea id="soporte-mensaje" name="mensaje" required placeholder="Describe el problema..."></textarea>
        </label>

        <div class="checkbox-wrapper-29">
          <label class="checkbox">
            <input type="checkbox" id="soporte-privacidad" class="checkbox__input" required>
            <span class="checkbox__label"></span>
            <span class="checkbox__text">
              Confirmo haber leído la <a href="https://sodire.es/privacy-policy" target="_blank">Política de Privacidad</a>
            </span>
          </label>
        </div>
        <button type="submit">Enviar</button>
      </form>
      <div class="jdnchat-spinner-outside" style="display:none;">
        <img src="img/enviando.gif" alt="Enviando" class="jdnchat-gif-enviando">
      </div>
      <div id="jdnchat-floating-bubble-container" class="jdnchat-floating-bubble-container"></div>
    </div>
  `;
  displayMessage(false, html, true, true); // Mostrar el HTML del formulario en el chat

  setTimeout(() => {
    const form = document.getElementById("formulario-soporte");
    if (!form) return;

    form.addEventListener("submit", async function(e) {
      e.preventDefault(); // Prevenir recarga de página al enviar el formulario
      if (formSubmitCount > 0) {
        // Si ya se envió antes, mostrar notificación y no volver a enviar
        showBubbleNotification("Su solicitud ya ha sido enviada.", 5000);
        return;
      }

      // Obtener valores ingresados por el usuario
      const nombre = form.querySelector('#soporte-nombre').value.trim();
      const apellidos = form.querySelector('#soporte-apellidos').value.trim();
      const email = form.querySelector('#soporte-email').value.trim();
      const telefono = form.querySelector('input[name="telefono"]').value.trim();
      const local = form.querySelector('#soporte-local').value.trim();
      const mensaje = form.querySelector('#soporte-mensaje').value.trim();
      const privacidadCheck = form.querySelector('#soporte-privacidad');

      // Validar que todos los campos obligatorios estén completos y la privacidad aceptada
      if (!nombre || !apellidos || !email || !mensaje || !local || !privacidadCheck.checked) {
        displayMessage(false, "Por favor completa todos los campos obligatorios y acepta la política.");
        return;
      }
      console.log("Tipo de consulta seleccionada:", tipoConsultaSeleccionada);
      // Construir objeto con datos para enviar al servidor
      const data = {
        nombre, apellidos, email, telefono, local, mensaje,
        historial: chatHistory.join("\n"),              // Incluir historial para contexto
        tipo_consulta: tipoConsultaSeleccionada        // Incluir tipo de consulta para backend
      };

      try {
        mostrarGifGlobal(); // Mostrar spinner mientras se procesa el envío

        const endpoint = tipo === "soporte"
          ? "http://localhost:5000/enviar-formulario-soporte"
          : "http://localhost:5000/enviar-formulario";

        // Enviar datos al servidor
        await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        displayMessage(false, "Gracias. Nuestro equipo se pondrá en contacto contigo."); // Confirmación al usuario
        formSubmitCount++; // Incrementar contador para prevenir reenvíos
      } catch (err) {
        console.error("Error al enviar formulario:", err);
        displayMessage(false, "Hubo un error al enviar el formulario."); // Mostrar mensaje de fallo
      } finally {
        ocultarGifGlobal(); // Ocultar spinner tras finalizar
      }
    });
  }, 300); // Esperar 300ms para asegurar que el formulario ya esté en el DOM
}




  // Función para asociar los listeners al formulario de productos (presupuesto)
function attachFormularioProductosListeners() {
  // Selecciona **todas** las instancias de formulario que haya en el chat
  document.querySelectorAll('#jdnchat-formulario').forEach(form => {
    // Si ya le pusimos listener, no volvemos a enganchar
    if (form.dataset.listenerAttached === 'true') return;
    form.dataset.listenerAttached = 'true';    // Marcar que ya tiene listener
    form.dataset.submitted = 'false';          // Inicialmente no se ha enviado

    // Añadir evento al enviar el formulario
    form.addEventListener('submit', async function(e) {
      e.preventDefault();   // Prevenir comportamiento por defecto (recargar página)
      e.stopPropagation();  // Evitar que el evento burbujee a otros elementos

      // Si este mismo formulario ya se envió, mostramos notificación y no cerramos nada
      if (form.dataset.submitted === 'true') {
        showBubbleNotification("Su solicitud ya ha sido enviada.", 5000);
        return;
      }

      // ─── Recoge valores de los campos del formulario ─────────────────────────────────
      const nombre    = form.nombre.value.trim();
      const apellidos = form.apellidos.value.trim();
      const negocio   = form.negocio.value.trim();
      const ciudad    = form.ciudad.value.trim();
      const provincia = form.provincia.value.trim();
      const cp        = form.cp.value.trim();
      const email     = form.email.value.trim();
      const telefono  = form.telefono.value.trim();
      const privacidad= form.querySelector('#productos-privacidad').checked;

      // ─── Validación de campos obligatorios ─────────────────────────────────────
      if (!nombre || !apellidos || !negocio || !ciudad ||
          !provincia || !cp || !email || !privacidad) {
        displayMessage(false, "Por favor completa todos los campos obligatorios y acepta la política.");
        return;
      }

      // ── MOSTRAR EL SPINNER del propio formulario mientras se envía la petición ─────────
      const spinnerContainer = form.parentElement.querySelector('.jdnchat-spinner-outside');
      if (spinnerContainer) spinnerContainer.style.display = 'flex'; // Mostrar GIF de carga

      // Construir objeto con los datos a enviar al servidor
      const data = { 
        nombre, 
        apellidos, 
        negocio, 
        ciudad,
        provincia, 
        cp, 
        email, 
        telefono,
        historial: chatHistory.join("\n") // Enviar historial de chat completo
      };

      try {
        // Enviar datos al endpoint correspondiente
        const res = await fetch('http://localhost:5000/enviar-formulario', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        await res.json(); // Esperar a que la respuesta JSON llegue

        // Confirmación al usuario de que el formulario se recibió
        displayMessage(false, "Gracias. Nuestro equipo se pondrá en contacto contigo.");
        form.dataset.submitted = 'true'; // Marcar que ya se envió para evitar duplicados
        form.reset();                   // Limpiar campos del formulario

        // ─── NUEVO: si NO estamos en el flujo de Digitalizar mi negocio ───
        if (currentSection?.titulo !== 'Digitalizar mi negocio') {
          // Invocar ayudaAdicional del flujo comercial si no es digitalización
          return jdnchat.handlePregunta('ayudaAdicional', '');
        }

        // si estamos en el TPV dentro de digitalización...
        const inTPVflow = currentSectionData?.flujos?.digital_tpv === currentFlow;
        if (inTPVflow) {
          // tras el TPV pasamos a ayuda adicional
          return jdnchat.handlePregunta('ayudaAdicional', '');
        }

        // si hay más ítems en la cola digital, seguimos con ellos
        if (window._digitalQueue && window._digitalQueue.length > 0) {
          const next = window._digitalQueue.shift(); // Obtener siguiente elemento de la cola
          currentFlow = null;                         // Reiniciar flujo actual
          return jdnchat.handlePregunta(next.id, next.text);
        }

        // fin del flujo de digitalización principal, vamos a la pregunta TPV
        return jdnchat.handlePregunta('pregunta_tpv', '');

      } catch (err) {
        console.error("Error al enviar formulario:", err);
        displayMessage(false, "Hubo un error al enviar el formulario. Inténtalo de nuevo.");
      } finally {
        // ── OCULTAR EL SPINNER del propio formulario ────────────────────────
        if (spinnerContainer) spinnerContainer.style.display = 'none'; // Ocultar GIF de carga
      }
    });
  });
}




// ——— HTML del formularioDigitalizar ——————————————————
function getFormularioDigitalizarHTML() {
  // Devuelve un string HTML que representa el formulario para el flujo de "Digitalizar mi negocio"
  return `
    <div class="jdnchat-form-container">
      <form id="formulario-digitalizar" class="jdnchat-formulario">
        <label>Nombre: <span class="jdnchat-obligatorio">*</span>
          <input type="text" name="nombre" placeholder="Tu nombre" required>
        </label>
        <label>Apellidos: <span class="jdnchat-obligatorio">*</span>
          <input type="text" name="apellidos" placeholder="Tus apellidos" required>
        </label>
        <label>Negocio: <span class="jdnchat-obligatorio">*</span>
          <input type="text" name="negocio" placeholder="Nombre de tu negocio" required>
        </label>
        <label>Provincia: <span class="jdnchat-obligatorio">*</span>
          <input type="text" name="provincia" placeholder="Tu provincia" required>
        </label>
        <label>Correo electrónico: <span class="jdnchat-obligatorio">*</span>
          <input type="email" name="email" placeholder="Tu email" required>
        </label>
        <label>Teléfono (opcional):
          <input type="tel" name="telefono" placeholder="Tu teléfono">
        </label>
        <div class="checkbox-wrapper-29">
          <label class="checkbox">
            <input type="checkbox" id="digitalizar-privacidad" name="privacidad" class="checkbox__input" required>
            <span class="checkbox__label"></span>
            <span class="checkbox__text">
              Confirmo haber leído la <a href="https://sodire.es/privacy-policy" target="_blank">Política de Privacidad</a>
            </span>
          </label>
        </div>
        <button type="submit">Enviar</button>
      </form>
      <div class="jdnchat-spinner-outside" style="display:none;">
        <img src="img/enviando.gif" alt="Enviando" class="jdnchat-gif-enviando">
      </div>
    </div>
  `;
}

// ——— Listeners para formularioDigitalizar ——————————————————
function attachFormularioDigitalizarListeners() {
  const form = document.getElementById("formulario-digitalizar");
  // Si el formulario no existe en el DOM o ya tiene listener, no hacer nada
  if (!form || form.dataset.listenerAttached === 'true') return;
  form.dataset.listenerAttached = 'true'; // Marcar que ya se le agregó el listener

  // Asignar evento submit para manejar el envío de datos
  form.addEventListener('submit', async function(e) {
    e.preventDefault(); // Prevenir comportamiento por defecto (reload)
    // Si el formulario ya fue enviado anteriormente, mostrar notificación y salir
    if (form.dataset.submitted === 'true') {
      showBubbleNotification("Tu solicitud ya fue enviada.", 5000);
      return;
    }

    // Recoger valores ingresados por el usuario
    const nombre    = form.nombre.value.trim();
    const apellidos = form.apellidos.value.trim();
    const negocio   = form.negocio.value.trim();
    const provincia = form.provincia.value.trim();
    const email     = form.email.value.trim();
    const telefono  = form.telefono.value.trim();
    const privacidad= form.querySelector('#digitalizar-privacidad').checked;

    // Validar que los campos obligatorios y la casilla de privacidad estén completos
    if (!nombre || !apellidos || !negocio || !provincia || !email || !privacidad) {
      displayMessage(false, "Completa todos los campos obligatorios y acepta la política.");
      return;
    }

    // Aquí añadimos los servicios seleccionados que quedaron en la cola digital
    const serviciosSeleccionados = window._digitalSelectedIds || [];

    // Preparar objeto con datos para enviar al backend
    const data = {
      nombre,
      apellidos,
      negocio,
      provincia,
      email,
      telefono,
      historial: chatHistory.join("\n"),   // Incluir historial de la conversación
      servicios: serviciosSeleccionados    // Incluir servicios seleccionados
    };

    try {
      mostrarGifGlobal(); // Mostrar spinner mientras se procesa la solicitud
      // Realizar petición POST al endpoint correspondiente
      const res = await fetch('http://localhost:5000/enviar-formulario-digitalizar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      const json = await res.json();
      // Si la respuesta del servidor no es OK, lanzar excepción
      if (!res.ok) throw new Error(json.error || "Error servidor");
      // Mostrar mensaje de confirmación al usuario
      displayMessage(false, "Gracias. Nuestro equipo te enviará un resumen pronto.");
      form.dataset.submitted = 'true'; // Marcar formulario como enviado
      // Avanzar al siguiente paso del flujo: pregunta TPV
      jdnchat.handlePregunta('pregunta_tpv', '');
    } catch(err) {
      console.error(err);
      displayMessage(false, "Error al enviar. Inténtalo de nuevo.");
    } finally {
      ocultarGifGlobal(); // Ocultar spinner tras procesar petición
    }
  });
}


  // Función para mostrar el modal de reset
function mostrarModalReset() {
  if (resetModal) {
    resetModal.style.display = 'flex'; // Cambiar el estilo a 'flex' para que el modal sea visible
  }
}

// Función para ocultar el modal de reset
function ocultarModalReset() {
  if (resetModal) {
    resetModal.style.display = 'none'; // Cambiar el estilo a 'none' para ocultar el modal
  }
}

// Función para resetear el chat
function resetearChat() {
  clearChatLog();                  // Limpiar todos los mensajes del chat en el DOM
  chatHistory = [];                // Vaciar el historial de texto guardado
  soporteActivo = false;           // Desactivar flag de flujo de soporte
  soporteCounter = 0;              // Reiniciar contador de soporte a 0
  esperandoFormularioSoporte = false; // Desactivar flag de formulario de soporte
  productosActivo = false;         // Desactivar flag de flujo de productos
  productosCounter = 0;            // Reiniciar contador de productos a 0
  esperandoFormularioProductos = false; // Desactivar flag de formulario de productos
  formSubmitCount = 0;             // Reiniciar contador de envíos de formulario a 0

  // 🔧 Reiniciar también el flujo jerárquico
  currentSection = null;           // Eliminar sección actual
  currentFlow = null;              // Eliminar flujo actual
  currentPregunta = null;          // Eliminar pregunta actual
  stateStack = [];                 // Vaciar la pila de estados previos

  mostrarDivisorReinicio();        // Insertar un divisor visual que indica nueva conversación
  setTimeout(() => {
    mostrarMensajeBienvenida();    // Mostrar el mensaje de bienvenida tras 500ms
  }, 500);

  // 🔥 Reiniciar botón y referencia de pregunta pendiente de IA
  wrapperPreguntaPendiente = null; // Eliminar referencia al wrapper de la pregunta pendiente
  preguntaPendienteIA = null;      // Eliminar referencia a la pregunta pendiente de IA
  ocultarBotonVolverPregunta();    // Ocultar el botón flotante de “volver a la pregunta”
}


  // Función para mostrar la burbuja flotante en el contenedor designado
function showBubbleNotification(message, duration = 5000) {
  const bubbleContainer = document.getElementById('jdnchat-floating-bubble-container');
  if (!bubbleContainer) {
    console.warn("No se encontró el contenedor de la burbuja flotante."); // Aviso si no existe el contenedor
    return;
  }

  // Si la burbuja ya existía, simplemente actualizamos su texto
  if (jdnchatBubbleDiv) {
    jdnchatBubbleDiv.textContent = message;
  } else {
    // Si no existe, crear un nuevo div para la burbuja
    jdnchatBubbleDiv = document.createElement('div');
    jdnchatBubbleDiv.classList.add('jdnchat-bubble-notification'); // Clase para estilo de burbuja
    jdnchatBubbleDiv.textContent = message;                         // Asignar texto a la burbuja
    bubbleContainer.appendChild(jdnchatBubbleDiv);                  // Insertar la burbuja en el contenedor
  }

  // Si ya había un temporizador activo para ocultar la burbuja, limpiarlo
  if (jdnchatBubbleTimeout) {
    clearTimeout(jdnchatBubbleTimeout);
  }

  // Programar la eliminación de la burbuja después del tiempo especificado
  jdnchatBubbleTimeout = setTimeout(() => {
    if (jdnchatBubbleDiv && jdnchatBubbleDiv.parentNode) {
      jdnchatBubbleDiv.parentNode.removeChild(jdnchatBubbleDiv); // Quitar la burbuja del DOM
    }
    jdnchatBubbleDiv = null;        // Limpiar referencia a la burbuja
    jdnchatBubbleTimeout = null;    // Limpiar referencia al temporizador
  }, duration);
}


  // Funciones para mostrar y ocultar el GIF de carga global (spinner ubicado dentro del contenedor del formulario)
function mostrarGifGlobal() {
  // Seleccionar el contenedor del formulario para identificar el spinner
  const container = document.querySelector('.jdnchat-form-container');
  if (container) {
    // Buscar el spinner dentro del contenedor y mostrarlo si existe
    const spinner = container.querySelector('.jdnchat-spinner-outside');
    if (spinner) spinner.style.display = 'flex';
  }
}

function ocultarGifGlobal() {
  // Seleccionar el contenedor del formulario para identificar el spinner
  const container = document.querySelector('.jdnchat-form-container');
  if (container) {
    // Buscar el spinner dentro del contenedor y ocultarlo si existe
    const spinner = container.querySelector('.jdnchat-spinner-outside');
    if (spinner) spinner.style.display = 'none';
  }
}

// Función auxiliar para hacer scroll hasta un elemento con offset
function scrollToFieldWithOffset(element, offset = 100) {
  // Mover la vista suavemente hasta el elemento objetivo
  element.scrollIntoView({ behavior: 'smooth', block: 'start' });
  // Ajustar la posición final restando el offset para dejar espacio superior
  window.scrollBy({ top: -offset, behavior: 'smooth' });
}

/**
 * Muestra el botón "Volver a la pregunta anterior" y arranca un listener de scroll
 * para ocultarlo o mostrarlo según la visibilidad de la pregunta pendiente.
 */
function mostrarBotonVolverPregunta() {
  // Si no hay pregunta pendiente ni wrapper asociado, no se hace nada
  if (!preguntaPendienteIA || !wrapperPreguntaPendiente) return;

  const chatLogEl = document.getElementById('jdnchat-chat-log');

  // Capturar la posición inicial de scroll (baseline) solo una vez
  initialScrollStart = chatLogEl.scrollTop;
  initialScrollEnd   = initialScrollStart + chatLogEl.clientHeight;

  // Crear o recuperar el botón "Volver a pregunta"
  let boton = document.getElementById('btnVolverPregunta');
  if (!boton) {
    // Si no existe, crear el botón y asignar ID y clases
    boton = document.createElement('button');
    boton.id = 'btnVolverPregunta';
    // No se añade texto; se usa un PNG como fondo mediante la clase
    boton.classList.add('btn-volver-pregunta');
    boton.addEventListener('click', () => {
      // Al hacer clic, desplazar suavemente la vista hasta la pregunta pendiente
      wrapperPreguntaPendiente.scrollIntoView({ behavior: 'smooth', block: 'start' });
      ocultarBotonVolverPregunta(); // Ocultar el botón luego de regresar
    });
    // Agregar el botón dentro del contenedor principal del chatbot
    document.querySelector('#jdnchat-chatbot-container').appendChild(boton);
  }

  // Asociar listener de scroll solo una vez para controlar visibilidad del botón
  if (!chatLogEl.dataset.volverAttached) {
    chatLogEl.addEventListener('scroll', () => {
      const scrollStart = chatLogEl.scrollTop;                      // Posición actual de scroll superior
      const scrollEnd   = scrollStart + chatLogEl.clientHeight;     // Posición actual de scroll inferior
      const qStart      = wrapperPreguntaPendiente.offsetTop;       // Posición superior de la pregunta pendiente
      const qEnd        = qStart + wrapperPreguntaPendiente.clientHeight; // Posición inferior de la pregunta pendiente

      // Determinar si la parte superior de la pregunta está visible en la vista
      const topVisible   = qStart >= scrollStart && qStart <= scrollEnd;
      // Determinar si la pregunta completa está dentro de la vista
      const fullyVisible = qStart >= scrollStart && qEnd   <= scrollEnd;
      // Detectar desplazamiento hacia arriba respecto al baseline
      const scrolledUp   = scrollStart < initialScrollStart;
      // Detectar desplazamiento hacia abajo respecto al baseline
      const scrolledDown = scrollEnd   > initialScrollEnd;

      // Decidir mostrar u ocultar el botón:
      if (topVisible) {
        // Si la parte superior de la pregunta está visible, ocultar botón
        boton.style.display = 'none';
      } else if (!fullyVisible && (scrolledUp || scrolledDown)) {
        // Si la pregunta no está completamente visible y el usuario scrolleó, mostrar botón
        boton.style.display = 'block';
      } else {
        // En cualquier otro caso, ocultar el botón
        boton.style.display = 'none';
      }

      // Ajustar la dirección de la flecha del botón según la posición de la pregunta
      if (qStart < scrollStart) {
        // Si la pregunta está más arriba de la vista, agregar clase 'scroll-up' para mostrar flecha hacia abajo
        boton.classList.add('scroll-up');
      } else if (qEnd > scrollEnd) {
        // Si la pregunta está más abajo de la vista, quitar clase 'scroll-up' para mostrar flecha hacia arriba
        boton.classList.remove('scroll-up');
      }
    });
    // Marcar que ya se ha asociado el listener para no duplicarlo
    chatLogEl.dataset.volverAttached = 'true';
  }

  // Forzar evaluación inmediata del listener de scroll
  chatLogEl.dispatchEvent(new Event('scroll'));
}

function ocultarBotonVolverPregunta() {
  // Obtener referencia al botón y ocultarlo si existe
  const boton = document.getElementById('btnVolverPregunta');
  if (boton) boton.style.display = 'none';
  // (Opcional) Podrías también reiniciar la clase 'scroll-up' aquí:
  // boton.classList.remove('up');
}

// Retornamos las funciones públicas para exponerlas al exterior del módulo
return {
  init: init,
  handleBotOption: handleBotOption,
  handleSeccion: handleSeccion,
  handleInicio: handleInicio,
  handlePregunta: handlePregunta,
  borrarMensaje: borrarMensaje,
  showBubbleNotification: showBubbleNotification,
  cargarSeccion: cargarSeccion
};
})();

// Inicializar el chatbot cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', jdnchat.init);

