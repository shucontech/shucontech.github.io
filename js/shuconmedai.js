(function() {
  'use strict';
  function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
      link.addEventListener('click', function(e) {
        const href = this.getAttribute('href');

        if (href === '#') return;
        
        const target = document.querySelector(href);
        
        if (target) {
          e.preventDefault();
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }

  function initScrollAnimations() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fadeIn');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    const moduleCards = document.querySelectorAll('.module-card');
    moduleCards.forEach((card, index) => {
      card.style.animationDelay = `${index * 0.1}s`;
      observer.observe(card);
    });

    const pricingCards = document.querySelectorAll('.pricing-card');
    pricingCards.forEach((card, index) => {
      card.style.animationDelay = `${index * 0.2}s`;
      observer.observe(card);
    });
  }

  function initContactForm() {
    const form = document.getElementById('contact-form');
    
    if (!form) return;

    form.addEventListener('submit', async function(e) {
      e.preventDefault();

      const submitBtn = form.querySelector('.submit-btn');
      const alertContainer = document.getElementById('form-alert');

      const formData = {
        fullName: form.querySelector('[name="fullName"]').value,
        phone: form.querySelector('[name="phone"]').value,
        email: form.querySelector('[name="email"]').value,
        hospitalName: form.querySelector('[name="hospitalName"]').value,
        message: form.querySelector('[name="message"]').value
      };

      if (!formData.fullName || !formData.email || !formData.hospitalName || !formData.message) {
        showAlert('Please fill in all required fields (marked with *)', 'error');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending...';

      try {
        await new Promise(resolve => setTimeout(resolve, 1500));

        showAlert('Thank you! Your message has been sent successfully. We\'ll get back to you within 24 hours.', 'success');

        form.reset();

      } catch (error) {
        console.error('Contact form error:', error);
        showAlert('There was an error sending your message. Please try again or contact us directly at shucontech@gmail.com', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Message';
      }
    });

    function showAlert(message, type) {
      const alertContainer = document.getElementById('form-alert');
      alertContainer.innerHTML = `
        <div class="alert alert-${type}">
          <strong>${message}</strong>
        </div>
      `;

      alertContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

      if (type === 'success') {
        setTimeout(() => {
          alertContainer.innerHTML = '';
        }, 5000);
      }
    }
  }

  function initLaptopHover() {
    const laptopContainer = document.querySelector('.laptop-container');
    
    if (!laptopContainer) return;

    laptopContainer.addEventListener('mouseenter', function() {
      this.classList.add('hovered');
    });

    laptopContainer.addEventListener('mouseleave', function() {
      this.classList.remove('hovered');
    });
  }

  function initMobileMenu() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.hero-nav-links');
    
    if (!menuBtn || !navLinks) return;

    menuBtn.addEventListener('click', function() {
      navLinks.classList.toggle('active');
      this.classList.toggle('active');
    });

    const links = navLinks.querySelectorAll('a');
    links.forEach(link => {
      link.addEventListener('click', function() {
        navLinks.classList.remove('active');
        menuBtn.classList.remove('active');
      });
    });
  }

  function initStatsCounter() {
    const stats = document.querySelectorAll('.stat-number');
    
    const observerOptions = {
      threshold: 0.5
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateValue(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    stats.forEach(stat => observer.observe(stat));

    function animateValue(element) {
      const text = element.textContent;
      const isPercentage = text.includes('%');
      const isPlus = text.includes('+');
      const isTime = text.includes('/');
      
      if (isTime) return; // Skip time values like "24/7"
      
      const value = parseFloat(text.replace(/[^0-9.]/g, ''));
      const duration = 2000;
      const steps = 60;
      const increment = value / steps;
      let current = 0;

      const timer = setInterval(() => {
        current += increment;
        if (current >= value) {
          current = value;
          clearInterval(timer);
        }
        
        let displayValue = isPercentage ? current.toFixed(1) : Math.floor(current);
        if (isPercentage) displayValue += '%';
        if (isPlus) displayValue += 'k+';
        
        element.textContent = displayValue;
      }, duration / steps);
    }
  }

  function init() {
    initSmoothScroll();
    initScrollAnimations();
    initContactForm();
    initLaptopHover();
    initMobileMenu();
    initStatsCounter();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();

