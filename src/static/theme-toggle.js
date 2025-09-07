// ===== GESTION DU THÈME CLAIR/SOMBRE =====

class ThemeManager {
  constructor() {
    this.currentTheme = this.getStoredTheme() || 'light';
    this.init();
  }

  init() {
    // Appliquer le thème au chargement
    this.applyTheme(this.currentTheme);
    
    // Créer le bouton de basculement
    this.createThemeToggle();
    
    // Écouter les changements de préférence système
    this.watchSystemTheme();
  }

  getStoredTheme() {
    return localStorage.getItem('theme');
  }

  setStoredTheme(theme) {
    localStorage.setItem('theme', theme);
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    this.currentTheme = theme;
    this.setStoredTheme(theme);
    this.updateToggleButton();
  }

  toggleTheme() {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.applyTheme(newTheme);
    
    // Animation de transition douce
    document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
    setTimeout(() => {
      document.body.style.transition = '';
    }, 300);
  }

  createThemeToggle() {
    // Vérifier si le bouton existe déjà
    if (document.querySelector('.theme-toggle')) {
      return;
    }

    const toggleButton = document.createElement('button');
    toggleButton.className = 'theme-toggle';
    toggleButton.innerHTML = `
      <span class="theme-toggle-icon">🌙</span>
      <span class="theme-toggle-text">Mode sombre</span>
    `;
    
    toggleButton.addEventListener('click', () => {
      this.toggleTheme();
    });

    document.body.appendChild(toggleButton);
    this.toggleButton = toggleButton;
  }

  updateToggleButton() {
    if (!this.toggleButton) return;

    const icon = this.toggleButton.querySelector('.theme-toggle-icon');
    const text = this.toggleButton.querySelector('.theme-toggle-text');

    if (this.currentTheme === 'dark') {
      icon.textContent = '☀️';
      text.textContent = 'Mode clair';
    } else {
      icon.textContent = '🌙';
      text.textContent = 'Mode sombre';
    }
  }

  watchSystemTheme() {
    // Écouter les changements de préférence système
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      mediaQuery.addEventListener('change', (e) => {
        // Seulement si l'utilisateur n'a pas défini de préférence
        if (!this.getStoredTheme()) {
          const systemTheme = e.matches ? 'dark' : 'light';
          this.applyTheme(systemTheme);
        }
      });
    }
  }
}

// ===== ANIMATIONS ET INTERACTIONS =====

class UIEnhancements {
  constructor() {
    this.init();
  }

  init() {
    this.addScrollEffects();
    this.addHoverEffects();
    this.addLoadingAnimations();
    this.addFormEnhancements();
  }

  addScrollEffects() {
    // Animation au scroll pour les éléments
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in');
        }
      });
    }, observerOptions);

    // Observer les cartes et éléments principaux
    document.querySelectorAll('.card, .product-card, .form-group').forEach(el => {
      observer.observe(el);
    });
  }

  addHoverEffects() {
    // Effet de parallaxe léger sur les cartes
    document.querySelectorAll('.card, .product-card').forEach(card => {
      card.addEventListener('mouseenter', (e) => {
        e.target.style.transform = 'translateY(-4px) scale(1.02)';
      });

      card.addEventListener('mouseleave', (e) => {
        e.target.style.transform = 'translateY(0) scale(1)';
      });
    });
  }

  addLoadingAnimations() {
    // Animation de chargement pour les images
    document.querySelectorAll('img').forEach(img => {
      img.addEventListener('load', function() {
        this.classList.add('fade-in');
      });
    });
  }

  addFormEnhancements() {
    // Amélioration des formulaires
    document.querySelectorAll('.form-input').forEach(input => {
      // Animation du label flottant
      const label = input.previousElementSibling;
      
      input.addEventListener('focus', () => {
        if (label && label.classList.contains('form-label')) {
          label.style.transform = 'translateY(-20px) scale(0.9)';
          label.style.color = 'var(--primary-color)';
        }
      });

      input.addEventListener('blur', () => {
        if (label && label.classList.contains('form-label') && !input.value) {
          label.style.transform = '';
          label.style.color = '';
        }
      });
    });

    // Validation visuelle en temps réel
    document.querySelectorAll('input[type="email"]').forEach(input => {
      input.addEventListener('input', (e) => {
        const isValid = e.target.checkValidity();
        e.target.style.borderColor = isValid ? 'var(--primary-color)' : '#dc3545';
      });
    });
  }
}

// ===== UTILITAIRES =====

class Utils {
  static debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  static throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  static smoothScrollTo(element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }

  static showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 16px 24px;
      background: var(--primary-color);
      color: white;
      border-radius: 12px;
      box-shadow: var(--shadow-lg);
      z-index: 1000;
      transform: translateX(100%);
      transition: transform 0.3s ease;
    `;

    document.body.appendChild(notification);

    // Animation d'entrée
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 100);

    // Suppression automatique
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }
}

// ===== INITIALISATION =====

document.addEventListener('DOMContentLoaded', () => {
  // Initialiser le gestionnaire de thème
  window.themeManager = new ThemeManager();
  
  // Initialiser les améliorations UI
  window.uiEnhancements = new UIEnhancements();
  
  // Ajouter les utilitaires globaux
  window.Utils = Utils;
  
  console.log('🎨 Système de thème Vinted initialisé');
});

// ===== GESTION DES ERREURS =====

window.addEventListener('error', (e) => {
  console.error('Erreur JavaScript:', e.error);
});

// ===== EXPORT POUR MODULES =====

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ThemeManager, UIEnhancements, Utils };
}

