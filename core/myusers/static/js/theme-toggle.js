document.addEventListener('DOMContentLoaded', function () {
    const themeToggleButton = document.getElementById('theme-toggle');
    const lightTheme = document.getElementById('light-theme');
    const darkTheme = document.getElementById('dark-theme');

    // Проверка сохраненной темы (если такая есть)
    if (localStorage.getItem('theme') === 'dark') {
        // Если тема темная, активируем темную тему
        darkTheme.removeAttribute('disabled');
        lightTheme.setAttribute('disabled', 'true');
    } else {
        // Иначе, оставляем светлую тему активной
        lightTheme.removeAttribute('disabled');
        darkTheme.setAttribute('disabled', 'true');
    }

    // Обработчик для переключения тем
    themeToggleButton.addEventListener('click', function () {
        if (darkTheme.disabled) {
            // Переключаем на темную тему
            darkTheme.removeAttribute('disabled');
            lightTheme.setAttribute('disabled', 'true');
            localStorage.setItem('theme', 'dark');  // Сохраняем выбранную тему
        } else {
            // Переключаем на светлую тему
            lightTheme.removeAttribute('disabled');
            darkTheme.setAttribute('disabled', 'true');
            localStorage.setItem('theme', 'light');  // Сохраняем выбранную тему
        }
    });
});
