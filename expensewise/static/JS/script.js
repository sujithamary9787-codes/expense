document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll("form[data-confirm]");

    forms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const message = form.getAttribute("data-confirm");

            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

    const amountInputs = document.querySelectorAll('input[type="number"]');

    amountInputs.forEach(function (input) {
        input.addEventListener("input", function () {
            if (Number(this.value) < 0) {
                this.value = "";
            }
        });
    });
});
