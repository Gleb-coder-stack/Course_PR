// Функции для гостевой части сайта

// Открыть модальное окно входа
function openLoginModal() {
    document.getElementById('loginModal').style.display = 'flex';
    document.getElementById('modal-error-message').style.display = 'none';
}

// Закрыть модальное окно входа
function closeLoginModal() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('modal-error-message').style.display = 'none';
}

// Вход из модального окна
function modalLogin() {
    const username = document.getElementById('modal-username').value;
    const password = document.getElementById('modal-password').value;

    if (!username || !password) {
        showModalError('Пожалуйста, заполните все поля');
        return;
    }

    // Используем ту же функцию login из auth.js
    if (typeof login === 'function') {
        // Если есть глобальная функция login, используем ее
        login();
    } else {
        // Иначе вызываем стандартный логин
        fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.access_token) {
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
                showModalError(data.detail || 'Ошибка авторизации');
            }
        })
        .catch(error => {
            showModalError('Ошибка сети. Проверьте подключение.');
        });
    }
}

// Быстрый вход для тестовых пользователей
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
    document.getElementById('modal-username').value = username;
    document.getElementById('modal-password').value = password;

    // Открываем модальное окно
    openLoginModal();
}

// Показать ошибку в модальном окне
function showModalError(message) {
    const errorEl = document.getElementById('modal-error-message');
    errorEl.textContent = message;
    errorEl.style.display = 'block';

    setTimeout(() => {
        errorEl.style.display = 'none';
    }, 5000);
}

// Установить сегодняшнюю дату
function setToday() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('date-selector').value = today;
    loadSessions();
}

// Загрузить сеансы на выбранную дату
async function loadSessions() {
    const date = document.getElementById('date-selector').value;
    const container = document.getElementById('sessions-container');

    container.innerHTML = `
        <div class="no-data">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Загрузка сеансов...</p>
        </div>
    `;

    try {
        const response = await fetch(`/api/sessions/public?date=${date}`);
        if (response.ok) {
            const sessions = await response.json();

            if (sessions && sessions.length > 0) {
                // Группируем сеансы по залам
                const halls = {};
                sessions.forEach(session => {
                    if (!halls[session.hall]) {
                        halls[session.hall] = [];
                    }
                    halls[session.hall].push(session);
                });

                let html = '';

                // Для каждого зала создаем блок
                Object.keys(halls).forEach(hallName => {
                    const hallSessions = halls[hallName];

                    html += `
                        <div style="margin-bottom: 2rem; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <div style="background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%); color: white; padding: 1rem 1.5rem;">
                                <h3 style="margin: 0; display: flex; align-items: center; gap: 10px;">
                                    <i class="fas fa-video"></i>
                                    ${hallName}
                                </h3>
                            </div>
                            <div style="padding: 1.5rem;">
                                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem;">
                    `;

                    hallSessions.forEach(session => {
                        const isAlmostFull = session.available_seats < 10;
                        const isFull = session.available_seats <= 0;

                        html += `
                            <div style="background: ${isFull ? '#FFEBEE' : isAlmostFull ? '#FFF3E0' : 'var(--gray)'};
                                        padding: 1rem; border-radius: 8px; border-left: 4px solid ${isFull ? '#F44336' : isAlmostFull ? '#FF9800' : 'var(--primary)'};">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                    <div style="font-weight: 600; color: var(--dark);">${session.film_title}</div>
                                    <div style="color: ${isFull ? '#F44336' : isAlmostFull ? '#FF9800' : 'var(--secondary)'};
                                                font-weight: 600;">${session.price} ₽</div>
                                </div>
                                <div style="display: flex; gap: 15px; color: var(--text-light); font-size: 0.9rem; margin-bottom: 0.5rem;">
                                    <div>
                                        <i class="far fa-clock"></i>
                                        ${session.start} - ${session.end}
                                    </div>
                                    <div style="color: ${isFull ? '#F44336' : isAlmostFull ? '#FF9800' : 'var(--primary)'};">
                                        <i class="fas fa-chair"></i>
                                        ${session.available_seats} мест
                                    </div>
                                </div>
                                <button onclick="buyTicket(${session.id})"
                                        style="width: 100%; padding: 8px; background: ${isFull ? '#B71C1C' : 'var(--primary)'};
                                               color: white; border: none; border-radius: 4px; cursor: ${isFull ? 'not-allowed' : 'pointer'};"
                                        ${isFull ? 'disabled' : ''}>
                                    ${isFull ? 'Нет мест' : isAlmostFull ? 'Мало мест' : 'Купить билет'}
                                </button>
                            </div>
                        `;
                    });

                    html += `
                                </div>
                            </div>
                        </div>
                    `;
                });

                container.innerHTML = html;
            } else {
                container.innerHTML = `
                    <div class="no-data">
                        <i class="far fa-calendar-times"></i>
                        <p>На выбранную дату нет сеансов</p>
                    </div>
                `;
            }
        } else {
            container.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Ошибка загрузки сеансов</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка:', error);
        container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-wifi-slash"></i>
                <p>Ошибка соединения с сервером</p>
            </div>
        `;
    }
}

// Загрузить фильмы с ближайшими сеансами
async function loadFilms() {
    const container = document.getElementById('films-container');

    container.innerHTML = `
        <div class="no-data">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Загрузка фильмов...</p>
        </div>
    `;

    try {
        // Загружаем фильмы
        const filmsResponse = await fetch('/api/films/public');
        let films = [];

        if (filmsResponse.ok) {
            films = await filmsResponse.json();
        }

        // Загружаем сеансы на сегодня
        const today = new Date().toISOString().split('T')[0];
        const sessionsResponse = await fetch(`/api/sessions/public?date=${today}`);
        let todaySessions = [];

        if (sessionsResponse.ok) {
            todaySessions = await sessionsResponse.json();
        }

        // Загружаем сеансы на завтра
        const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
        const tomorrowResponse = await fetch(`/api/sessions/public?date=${tomorrow}`);
        let tomorrowSessions = [];

        if (tomorrowResponse.ok) {
            tomorrowSessions = await tomorrowResponse.json();
        }

        // Объединяем все сеансы
        const allSessions = [...todaySessions, ...tomorrowSessions];

        if (films && films.length > 0) {
            let html = '';

            films.forEach(film => {
                // Получаем первые 2 буквы названия для постера
                const posterLetters = film.title.substring(0, 2).toUpperCase();

                // Находим ближайшие 3 сеанса для этого фильма
                const filmSessions = allSessions
                    .filter(session => session.film_id === film.id)
                    .sort((a, b) => {
                        // Сначала сегодняшние, потом завтрашние
                        const dateA = new Date(a.date + ' ' + a.start);
                        const dateB = new Date(b.date + ' ' + b.start);
                        return dateA - dateB;
                    })
                    .slice(0, 3); // Берем только 3 ближайших

                html += `
                    <div class="film-card">
                        <div class="film-header">
                            <div class="film-poster">${posterLetters}</div>
                            <div class="film-title">
                                <h3>${film.title}</h3>
                                <div class="film-meta">
                                    <span>${film.genre || 'Не указан'}</span>
                                    <span>${film.age_rating || '0+'}</span>
                                    <span>${film.duration || '0'} мин</span>
                                </div>
                            </div>
                        </div>
                        <div class="film-content">
                            <div class="film-description">
                                ${film.description || 'Описание отсутствует'}
                            </div>

                            ${filmSessions.length > 0 ? `
                                <div class="film-sessions">
                                    <div class="sessions-title">
                                        <i class="far fa-clock"></i>
                                        Ближайшие сеансы:
                                    </div>
                                    <div class="sessions-list">
                            ` : ''}

                            ${filmSessions.map(session => {
                                const sessionDate = new Date(session.date);
                                const today = new Date();
                                const tomorrow = new Date(today.getTime() + 86400000);
                                let dateText = '';

                                if (sessionDate.toDateString() === today.toDateString()) {
                                    dateText = 'Сегодня';
                                } else if (sessionDate.toDateString() === tomorrow.toDateString()) {
                                    dateText = 'Завтра';
                                } else {
                                    dateText = sessionDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
                                }

                                const isAlmostFull = session.available_seats < 10;
                                const isFull = session.available_seats <= 0;

                                return `
                                    <div class="session-item">
                                        <div class="session-time">${dateText}, ${session.start}</div>
                                        <div class="session-details">
                                            <span class="session-hall">${session.hall}</span>
                                            <span class="session-price">${session.price} ₽</span>
                                            <span style="color: ${isFull ? '#F44336' : isAlmostFull ? '#FF9800' : '#4CAF50'}">
                                                ${isFull ? 'Нет мест' : `${session.available_seats} мест`}
                                            </span>
                                        </div>
                                        <button class="session-btn" onclick="buyTicket(${session.id})" ${isFull ? 'disabled' : ''}>
                                            ${isFull ? 'Нет мест' : 'Купить'}
                                        </button>
                                    </div>
                                `;
                            }).join('')}

                            ${filmSessions.length > 0 ? `
                                    </div>
                                </div>
                            ` : `
                                <div class="sessions-title">
                                    <i class="far fa-calendar-times"></i>
                                    Ближайших сеансов нет
                                </div>
                            `}
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        } else {
            container.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-film"></i>
                    <p>Нет доступных фильмов</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка:', error);
        container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-wifi-slash"></i>
                <p>Ошибка соединения с сервером</p>
            </div>
        `;
    }
}

// Купить билет (перенаправление на страницу входа)
function buyTicket(sessionId) {
    openLoginModal();
    // Можно сохранить sessionId в localStorage для дальнейшего использования
    localStorage.setItem('selected_session', sessionId);
}

// Загрузка данных при старте
document.addEventListener('DOMContentLoaded', function() {
    // Устанавливаем сегодняшнюю дату в селектор
    setToday();

    // Загружаем фильмы с сеансами
    loadFilms();

    // Закрыть модальное окно при клике вне его
    window.onclick = function(event) {
        const modal = document.getElementById('loginModal');
        if (event.target === modal) {
            closeLoginModal();
        }
    }

    // Закрыть модальное окно по ESC
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeLoginModal();
        }
    });
});