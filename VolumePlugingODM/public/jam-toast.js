export class JamToast {
  constructor({ maxCount = 3, timeout = 3000, position = 'top-right', mobilePosition = 'bottom' } = {}) {
    this.maxCount = maxCount;
    this.timeout = timeout;
    this.position = position;
    this.mobilePosition = mobilePosition;
    this.container = document.createElement('div');
    this.container.classList.add('toast-container', `toast-${position}`);
    document.body.appendChild(this.container);
    this.toasts = [];

    // Adjust for mobile position on load and resize
    this.setMobilePosition();
    window.addEventListener('resize', () => this.setMobilePosition());
  }

  // Set mobile position classes based on screen width and mobilePosition
  setMobilePosition() {
    if (window.innerWidth <= 768) {
      this.container.classList.toggle('toast-top-mobile', this.mobilePosition === 'top');
      this.container.classList.toggle('toast-bottom-mobile', this.mobilePosition === 'bottom');
    } else {
      // Remove mobile-specific classes if not in mobile view
      this.container.classList.remove('toast-top-mobile', 'toast-bottom-mobile');
    }
  }

  // Show a new toast message with type
  showToast(message, type = 'info') {
    while (this.toasts.length >= this.maxCount) {
      this.removeToast(this.toasts[0], true);  // Force remove oldest toast
    }

    const toast = document.createElement('div');
    toast.classList.add('toast', `toast-${type}`);
    toast.innerText = message;

    // Click to close functionality
    toast.addEventListener('click', () => this.removeToast(toast));

    this.container.appendChild(toast);
    this.toasts.push(toast);

    // Animate toast appearance
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    // Auto-remove after timeout
    setTimeout(() => this.removeToast(toast), this.timeout);
  }

  // Remove toast from DOM and array
  removeToast(toast, forceRemove = false) {
    if (toast) {
      if (!forceRemove) {
        toast.classList.remove('show');
        setTimeout(() => this.finalizeRemoval(toast), 300);
      } else {
        this.finalizeRemoval(toast);
      }
    }
  }

  // Finalize removal
  finalizeRemoval(toast) {
    if (this.container.contains(toast)) {
      this.container.removeChild(toast);
      this.toasts = this.toasts.filter(t => t !== toast);
    }
  }
}
