INSERT OR IGNORE INTO courses (code, name, description, active, image_url) VALUES
('python_basics', 'Основи Python', 'Базовий курс з мови програмування Python', 1, 'https://i.ibb.co/xwQFDcY/roadmap-course-2025.png'),
('web_dev', 'Веб-розробка', 'HTML, CSS, JavaScript та створення сайтів.', 0, ''),
('mobile_dev', 'Мобільна розробка', 'Розробка застосунків для Android та iOS.', 0, ''),
('ml_intro', 'Машинне навчання', 'Основи машинного навчання та алгоритми.', 0, '');

-- якщо active в курса = 0, то курс не буде відображатися в чат-боті!