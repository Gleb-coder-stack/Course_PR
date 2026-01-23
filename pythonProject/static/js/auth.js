async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('error-message');

    if (!username || !password) {
        showError('Пожалуйста, заполните все поля');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('/api/auth/login', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify({
                username: data.username,
                role: data.role,
                full_name: data.full_name
            }));

            // Перенаправляем в зависимости от роли
            if (data.role === 'admin') {
                window.location.href = '/admin';
            } else if (data.role === 'cashier') {
                window.location.href = '/cashier';
            } else {
                window.location.href = '/';
            }
        } else {
            const error = await response.json();
            showError(error.detail || 'Ошибка авторизации');
        }
    } catch (error) {
        showError('Ошибка сети. Проверьте подключение.');
    }
}

function quickLogin(role) {
    let username, password;

    if (role === 'admin') {
        username = 'admin';
        password = 'admin123';
    } else if (role === 'cashier') {
        username = 'cashier';
        password = 'cashier123';
    } else {
        return;
    }

    // Заполняем поля формы
    document.getElementById('username').value = username;
    document.getElementById('password').value = password;

    // Вызываем функцию входа
    login();
}

function showError(message) {
    const errorEl = document.getElementById('error-message');
    errorEl.textContent = message;
    errorEl.style.display = 'block';

    setTimeout(() => {
        errorEl.style.display = 'none';
    }, 5000);
}

// Проверка авторизации при загрузке
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');
    if (token) {
        // Проверяем валидность токена
        fetch('/api/check-auth', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        })
        .then(user => {
            if (user) {
                // Перенаправляем если уже авторизован
                if (user.role === 'admin') {
                    window.location.href = '/admin';
                } else if (user.role === 'cashier') {
                    window.location.href = '/cashier';
                }
            }
        });
    }
});

// Выход из системы
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Получение токена для запросов
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/';
        return {};
    }

    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}