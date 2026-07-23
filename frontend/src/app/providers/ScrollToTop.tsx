import { useEffect } from 'react'
import { useLocation } from 'react-router'

/** Переход на новый роут возвращает скролл наверх; смена ?query — нет. */
export function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' })
  }, [pathname])

  return null
}
