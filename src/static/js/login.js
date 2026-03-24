document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const errorDiv = document.getElementById('error');
    errorDiv.style.display = 'none';

    try {
        const response = await fetch('/login', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            // 3. 🚀 ПЕРЕНАПРАВЛЕННЯ (Саме цього не вистачало)
            // Якщо логін успішний, йдемо на дашборд або tracking
            window.location.href = "/tracking/";
        } else {
            // Якщо помилка (наприклад, 401)
            errorDiv.innerText = "Невірний логін або пароль";
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Помилка з\'єднання:', error);
        errorDiv.innerText = "Помилка сервера";
        errorDiv.style.display = 'block';
    }
});