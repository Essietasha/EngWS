window.addEventListener('DOMContentLoaded', () => {
    const home = document.querySelector('.homebg');
    const categorySelect = document.querySelector('.categoryDivEl');
    const signupLoginDiv = document.querySelector('.signupRightDiv');

    if (home) home.classList.add('homeslide');
    if (categorySelect) categorySelect.classList.add('slidein');
    if (signupLoginDiv) signupLoginDiv.classList.add('slideinslower');
})



document.addEventListener("DOMContentLoaded", function () {

  const dateInput = document.getElementById("date");
  const timeInput = document.getElementById("time");

  function updateMinValues() {
    const now = new Date();
    const today = now.toISOString().split("T")[0];
    dateInput.min = today;

    if (dateInput.value === today) {
      const hours = now.getHours().toString().padStart(2, "0");
      const minutes = now.getMinutes().toString().padStart(2, "0");
      timeInput.min = `${hours}:${minutes}`;
    } else {
      timeInput.removeAttribute("min");
    }
  }
  setInterval(updateMinValues, 60000);
  updateMinValues();
  dateInput.addEventListener("change", updateMinValues);
});
