// Select all sliders
const sliders = document.querySelectorAll('.slider');

// Loop through each slider and attach event listeners
sliders.forEach((slider) => {
  slider.addEventListener('input', (e) => {
    const container = e.target.closest('.container'); // Find the corresponding container
    if (container) {
      container.style.setProperty('--position', `${e.target.value}%`);
    }
  });
});

