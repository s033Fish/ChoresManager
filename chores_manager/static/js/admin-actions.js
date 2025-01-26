console.log("JavaScript loaded successfully!");

// Add an event listener for the "Add Chores" form submission
document.getElementById('addChoresForm').addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent default form submission

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    console.log("Submitting data:", data);

    fetch('/admin-actions/add-chores/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            console.log("Chore added successfully!");
            const feedback = document.getElementById('adminActionsFeedback');
            feedback.classList.remove('d-none', 'alert-danger');
            feedback.classList.add('alert-success');
            feedback.innerText = 'Chore added successfully!';

            // Hide the modal after successful submission
            const modal = bootstrap.Modal.getInstance(document.getElementById('addChoresModal'));
            modal.hide();
        } else {
            alert('Failed to add chore. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error adding chore:', error);
        alert('An error occurred while adding the chore.');
    });
});

// Add an event listener for admin actions like assigning chores and sending SMS
function executeAction(action, buttonId) {
    const feedback = document.getElementById('adminActionsFeedback');
    const button = document.getElementById(buttonId);

    button.disabled = true;
    button.innerText = 'Processing...';

    fetch(`/admin-actions/${action}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            console.log(`${action} action completed successfully!`);
            button.classList.remove('btn-primary');
            button.classList.add('btn-success');
            button.innerText = 'Completed';

            feedback.classList.remove('d-none', 'alert-danger');
            feedback.classList.add('alert-success');
            feedback.innerText = `${action.replace('-', ' ').toUpperCase()} action completed successfully!`;
        } else {
            button.disabled = false;
            button.innerText = 'Retry';

            feedback.classList.remove('d-none', 'alert-success');
            feedback.classList.add('alert-danger');
            feedback.innerText = `Failed to complete ${action.replace('-', ' ').toUpperCase()} action. Please try again.`;
        }
    })
    .catch(error => {
        console.error('Error executing action:', error);
        button.disabled = false;
        button.innerText = 'Retry';

        feedback.classList.remove('d-none', 'alert-success');
        feedback.classList.add('alert-danger');
        feedback.innerText = `An error occurred while processing ${action.replace('-', ' ').toUpperCase()} action.`;
    });
}

// Function to update the day of the week based on the selected date
window.updateDayOfWeek = function () {
    const dateInput = document.getElementById('choreDate').value;
    const dayOfWeekInput = document.getElementById('dayOfWeek');

    if (dateInput) {
        const date = new Date(dateInput);
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayOfWeek = days[date.getUTCDay()]; // Get day of the week from the date
        dayOfWeekInput.value = dayOfWeek; // Set the value of the Day of Week field
        console.log("Day of Week updated to:", dayOfWeek);
    } else {
        dayOfWeekInput.value = ''; // Clear the Day of Week field if no date is selected
        console.log("Date input cleared; Day of Week reset.");
    }
};

