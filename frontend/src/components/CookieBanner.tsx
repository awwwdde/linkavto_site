import { useState } from 'react'

export default function CookieBanner() {
  const [visible, setVisible] = useState(() => !localStorage.getItem('cookieAccepted'))
  if (!visible) return null
  return (
    <div className="fixed bottom-4 left-1/2 z-[1000] flex w-[min(640px,92vw)] -translate-x-1/2 items-center gap-4 rounded-xl bg-white px-5 py-4 shadow-[0_8px_30px_rgba(0,0,0,0.18)]">
      <p className="m-0 text-sm text-gray-600">
        Мы используем файлы cookie для персонализации сервисов и улучшения удобства пользования сайтом. Продолжая работу,
        вы соглашаетесь с нашей Политикой конфиденциальности.
      </p>
      <button
        onClick={() => {
          localStorage.setItem('cookieAccepted', '1')
          setVisible(false)
        }}
        className="shrink-0 rounded-lg bg-black px-5 py-2.5 text-sm font-semibold text-white"
      >
        Принять
      </button>
    </div>
  )
}
