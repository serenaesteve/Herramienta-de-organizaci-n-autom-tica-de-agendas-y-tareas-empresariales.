// Modal helpers
function openModal(id) {
  document.getElementById(id).classList.add('open');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
  }
});

// Toggle task via fetch
function toggleTask(id, el) {
  fetch('/tasks/toggle/' + id, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      const card = el.closest('.task-card');
      const title = card.querySelector('.task-title');
      if (data.done) {
        el.classList.add('checked');
        card.classList.add('done-card');
        if (title) title.classList.add('done');
      } else {
        el.classList.remove('checked');
        card.classList.remove('done-card');
        if (title) title.classList.remove('done');
      }
    });
}

// Delete task via fetch
function deleteTask(id) {
  if (!confirm('¿Eliminar esta tarea?')) return;
  fetch('/tasks/delete/' + id, { method: 'POST' })
    .then(r => r.json())
    .then(() => {
      const card = document.getElementById('task-' + id);
      if (card) card.remove();
    });
}

// Delete event via fetch
function deleteEvent(id) {
  if (!confirm('¿Eliminar este evento?')) return;
  fetch('/events/delete/' + id, { method: 'POST' })
    .then(r => r.json())
    .then(() => location.reload());
}

// AI chat
let chatHistory = [];
async function sendAIMessage() {
  const inp = document.getElementById('ai-input');
  const msg = inp ? inp.value.trim() : '';
  if (!msg) return;
  inp.value = '';
  appendMessage(msg, 'user');
  showThinking();
  try {
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    hideThinking();
    appendMessage(data.reply || 'Sin respuesta.', 'assistant');
  } catch (e) {
    hideThinking();
    appendMessage('Error al conectar. Verifica que Ollama esté activo.', 'assistant');
  }
}

async function organizeAI() {
  showThinking();
  try {
    const res = await fetch('/api/ai/organize', { method: 'POST' });
    const data = await res.json();
    hideThinking();
    appendMessage(data.reply || 'Sin respuesta.', 'assistant');
  } catch (e) {
    hideThinking();
    appendMessage('Error al conectar con Ollama.', 'assistant');
  }
}

function appendMessage(text, role) {
  const area = document.getElementById('ai-chat-area');
  if (!area) return;
  const div = document.createElement('div');
  div.className = 'ai-bubble ' + role;
  div.textContent = text;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
}

function showThinking() {
  const area = document.getElementById('ai-chat-area');
  if (!area) return;
  const div = document.createElement('div');
  div.id = 'ai-thinking';
  div.className = 'ai-dots';
  div.innerHTML = '<div class="ai-dot-anim"></div><div class="ai-dot-anim"></div><div class="ai-dot-anim"></div>';
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
}

function hideThinking() {
  const el = document.getElementById('ai-thinking');
  if (el) el.remove();
}

// Enter key for AI input
document.addEventListener('DOMContentLoaded', function() {
  const aiInp = document.getElementById('ai-input');
  if (aiInp) {
    aiInp.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') sendAIMessage();
    });
  }
});
