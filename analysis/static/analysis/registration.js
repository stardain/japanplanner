const usernameField = document.getElementById('id_username'); // Django's default ID
const feedbackArea = document.createElement('div');
usernameField.after(feedbackArea);

usernameField.addEventListener('input', function() {
    const username = this.value;

    if (username.length > 0) {
        // Send a GET request to our validation view
        fetch(`/ajax/validate-username/?username=${username}`)
            .then(response => response.json())
            .then(data => {
                if (data.is_taken) {
                    feedbackArea.innerHTML = "<span style='color: red;'>Username already taken!</span>";
                    usernameField.style.borderColor = "red";
                } else {
                    feedbackArea.innerHTML = "<span style='color: green;'>Username available!</span>";
                    usernameField.style.borderColor = "green";
                }
            });
    } else {
        feedbackArea.innerHTML = "";
    }
});