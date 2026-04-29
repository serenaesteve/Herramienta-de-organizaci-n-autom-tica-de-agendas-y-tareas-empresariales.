# AgendaAI 🗓️

Herramienta de organización automática de agendas y tareas empresariales con IA local (Ollama + LLaMA 3).

## Características

- **Login y registro** de usuarios con sesiones seguras
- **Dashboard** con estadísticas y resumen del día
- **Gestión de tareas** con prioridades, categorías, fechas límite y filtros
- **Calendario interactivo** con vista mensual y semanal, eventos por tipo
- **Asistente IA** con Ollama + LLaMA 3 para organización inteligente
- **Perfil de usuario** con estadísticas personales
- Diseño rosa/morado estilo 3D, tipografía Nunito

## Instalación

```bash
# 1. Entrar al directorio
cd agendaai

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Asegúrate de tener Ollama con LLaMA 3
ollama pull llama3
ollama run llama3

# 5. Ejecutar la app
python app.py
```

Abre http://localhost:5000 en tu navegador.

## Variables de entorno (opcionales)

```bash
export SECRET_KEY="tu-clave-secreta"
export OLLAMA_URL="http://localhost:11434"  # por defecto
```

## Estructura del proyecto

```
agendaai/
├── app.py                  # Flask principal (rutas, modelos, lógica)
├── requirements.txt
├── static/
│   ├── css/main.css        # Estilos completos rosa/morado
│   └── js/main.js          # JavaScript global
└── templates/
    ├── base.html           # Layout con sidebar
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── tasks.html
    ├── calendar.html
    ├── ai.html
    └── profile.html
```

## Tecnologías

- **Backend**: Flask + SQLAlchemy + SQLite
- **Auth**: Werkzeug (hash de contraseñas)
- **IA**: Ollama + LLaMA 3 (local, sin coste)
- **Frontend**: HTML/CSS/JS puro + Nunito font
- **DB**: SQLite (archivo `instance/agendaai.db`)
