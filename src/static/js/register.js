document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;

    const errorDiv = document.getElementById('error');
    const successDiv = document.getElementById('success');

    // Скидаємо повідомлення
    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';

    // 1. Клієнтська валідація паролів
    if (password !== confirmPassword) {
        errorDiv.innerText = "Паролі не співпадають!";
        errorDiv.style.display = 'block';
        return;
    }

    try {
        // 2. Відправка запиту
        // Важливо: відправляємо JSON, бо UserCreate (Pydantic) очікує JSON body
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // 3. Успіх
            successDiv.style.display = 'block';
            // Чекаємо 1.5 секунди і перекидаємо на логін
            setTimeout(() => {
                window.location.href = "/login";
            }, 1500);
        } else {
            // 4. Помилка від сервера (наприклад, "User already exists")
            errorDiv.innerText = data.detail || "Помилка реєстрації";
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Error:', error);
        errorDiv.innerText = "Помилка з'єднання з сервером";
        errorDiv.style.display = 'block';
    }
});