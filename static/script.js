// ==========================================
// VARIABLES GLOBALES Y CONFIGURACIÓN
// ==========================================
const APP = {
    init() {
        this.initFlashMessages();
        this.initUserDropdown();
        this.initAnimations();
        this.initFormValidations();
        this.initTableAnimations();
        this.setFavicon();
    },

    // Configurar favicon
    setFavicon() {
        const link = document.querySelector("link[rel='icon']") || document.createElement('link');
        link.rel = 'icon';
        link.href = '/static/img/favicon.png';
        document.head.appendChild(link);
    }
};

// ==========================================
// MENSAJES FLASH
// ==========================================
APP.initFlashMessages = function() {
    // Crear contenedor para mensajes si no existe
    if (!document.querySelector('.flash-messages')) {
        const container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }

    // Procesar mensajes existentes de Flask
    const flashContainer = document.querySelector('.flash-messages');
    
    // Auto-cerrar mensajes después de 5 segundos
    setTimeout(() => {
        const messages = document.querySelectorAll('.flash-message');
        messages.forEach(msg => {
            msg.style.animation = 'slideOutRight 0.3s ease-in forwards';
            setTimeout(() => msg.remove(), 300);
        });
    }, 5000);

    // Función para mostrar nuevos mensajes
    window.showFlash = function(message, type = 'success') {
        const flash = document.createElement('div');
        flash.className = `flash-message flash-${type}`;
        flash.innerHTML = `
            ${message}
            <button class="flash-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        flashContainer.appendChild(flash);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (flash.parentElement) {
                flash.style.animation = 'slideOutRight 0.3s ease-in forwards';
                setTimeout(() => flash.remove(), 300);
            }
        }, 5000);
    };
};

// Animación para cerrar mensajes
const slideOutRightKeyframes = `
    @keyframes slideOutRight {
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
if (!document.querySelector('#slideOutRight-keyframes')) {
    const style = document.createElement('style');
    style.id = 'slideOutRight-keyframes';
    style.textContent = slideOutRightKeyframes;
    document.head.appendChild(style);
}

// ==========================================
// DROPDOWN DE USUARIO
// ==========================================
APP.initUserDropdown = function() {
    const userInfo = document.querySelector('.user-info');
    const userDropdown = document.querySelector('.user-dropdown');

    if (userInfo && userDropdown) {
        userInfo.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });

        // Cerrar dropdown al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!userInfo.contains(e.target)) {
                userDropdown.classList.remove('active');
            }
        });

        // Cerrar dropdown con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                userDropdown.classList.remove('active');
            }
        });
    }
};

// ==========================================
// ANIMACIONES GENERALES
// ==========================================
APP.initAnimations = function() {
    // Observador para animaciones al hacer scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, {
        threshold: 0.1
    });

    // Observar elementos que deben animarse
    document.querySelectorAll('.module-card, .form-card, .table-container').forEach(el => {
        observer.observe(el);
    });

    // Animación para botones
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Efecto ripple para botones principales
    document.querySelectorAll('.btn-primary, .btn-success').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255,255,255,0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
};

// Keyframes para efecto ripple
const rippleKeyframes = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
if (!document.querySelector('#ripple-keyframes')) {
    const style = document.createElement('style');
    style.id = 'ripple-keyframes';
    style.textContent = rippleKeyframes;
    document.head.appendChild(style);
}

// ==========================================
// VALIDACIONES DE FORMULARIO
// ==========================================
APP.initFormValidations = function() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input[required], select[required]');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                this.classList.toggle('invalid', !this.value.trim());
            });
            
            input.addEventListener('input', function() {
                this.classList.remove('invalid');
            });
        });

        // Validación al enviar formulario
        form.addEventListener('submit', function(e) {
            let isValid = true;
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('invalid');
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showFlash('Por favor completa todos los campos requeridos', 'error');
            }
        });
    });
};

// Estilos para campos inválidos
const invalidInputStyles = `
    .form-control.invalid,
    .form-input.invalid {
        border-color: #dc3545;
        box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1);
    }
`;
if (!document.querySelector('#invalid-input-styles')) {
    const style = document.createElement('style');
    style.id = 'invalid-input-styles';
    style.textContent = invalidInputStyles;
    document.head.appendChild(style);
}

// ==========================================
// ANIMACIONES DE TABLA
// ==========================================
APP.initTableAnimations = function() {
    const tableRows = document.querySelectorAll('.table tbody tr');
    
    tableRows.forEach((row, index) => {
        row.style.animationDelay = `${index * 0.1}s`;
        row.classList.add('fade-in');
        
        // Efecto hover mejorado
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.01)';
            this.style.zIndex = '1';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.zIndex = 'auto';
        });
    });
};

// ==========================================
// FUNCIONES ESPECÍFICAS PARA PÁGINAS
// ==========================================

// Funciones para login/register
function initAuthPage() {
    const authCard = document.querySelector('.auth-card');
    if (authCard) {
        authCard.style.opacity = '0';
        setTimeout(() => {
            authCard.style.opacity = '1';
            authCard.classList.add('bounce-in');
        }, 100);
    }

    // Efecto de typing en el título
    const title = document.querySelector('.auth-title');
    if (title) {
        const text = title.textContent;
        title.textContent = '';
        let i = 0;
        
        const typeWriter = () => {
            if (i < text.length) {
                title.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            }
        };
        
        setTimeout(typeWriter, 500);
    }
}

// Funciones para dashboard
function initDashboard() {
    const moduleCards = document.querySelectorAll('.module-card');
    
    moduleCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
            card.style.transition = 'all 0.5s ease';
        }, index * 200);
    });
}

// ==========================================
// INICIALIZACIÓN
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    APP.init();
    
    // Inicializar funciones específicas según la página
    if (document.querySelector('.auth-container')) {
        initAuthPage();
    }
    
    if (document.querySelector('.modules-grid')) {
        initDashboard();
    }
    
    // Procesar mensajes flash de Flask si existen
    const flashes = document.querySelectorAll('[data-flash]');
    flashes.forEach(flash => {
        const message = flash.textContent;
        const type = flash.dataset.flash;
        flash.remove();
        showFlash(message, type);
    });
});

// ==========================================
// FUNCIONES UTILITARIAS
// ==========================================
function confirmDelete(message = '¿Estás seguro de que deseas eliminar este elemento?') {
    return confirm(message);
}

function toggleLoader(show = true) {
    let loader = document.querySelector('.loader');
    
    if (show && !loader) {
        loader = document.createElement('div');
        loader.className = 'loader';
        loader.innerHTML = `
            <div class="loader-spinner"></div>
            <p>Cargando...</p>
        `;
        document.body.appendChild(loader);
    } else if (!show && loader) {
        loader.remove();
    }
}

// Estilos para el loader
const loaderStyles = `
    .loader {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }
    
    .loader-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #165d2a;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;

if (!document.querySelector('#loader-styles')) {
    const style = document.createElement('style');
    style.id = 'loader-styles';
    style.textContent = loaderStyles;
    document.head.appendChild(style);
}
