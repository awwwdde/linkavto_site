/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Дизайн-токены, снятые с оригинального сайта
        header: '#A7D2EF',        // фон шапки
        catalog: '#7BAACF',       // кнопка «Каталог»
        brand: '#89BEE8',         // акцентный голубой (цены, hover)
        ink: '#212529',           // основной цвет текста (как в Bootstrap)
        'cart-success': '#c1e7ff',
        'gradFrom': '#667eea',    // градиент карточек категорий
        'gradTo': '#764ba2',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'system-ui', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif'],
      },
      borderRadius: {
        card: '15px',
      },
      boxShadow: {
        card: '0 2px 8px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
}
