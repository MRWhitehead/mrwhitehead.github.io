// Select all containers and sliders
const containers = document.querySelectorAll('.container');
const sliders = document.querySelectorAll('.slider');

// Loop through each slider and attach event listeners
sliders.forEach((slider, index) => {
  slider.addEventListener('input', (e) => {
    const container = containers[index]; // Get the corresponding container
    container.style.setProperty('--position', `${e.target.value}%`);
  });
});