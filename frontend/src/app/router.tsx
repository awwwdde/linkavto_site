import { createBrowserRouter } from 'react-router'
import { RootLayout } from '@/app/layouts/RootLayout'
import { RouteError } from '@/app/layouts/RouteError'

/**
 * §4: структура URL сохраняется со старого сайта, все страницы — lazy-роуты.
 */
export const router = createBrowserRouter([
  {
    path: '/',
    Component: RootLayout,
    ErrorBoundary: RouteError,
    children: [
      { index: true, lazy: () => import('@/pages/home') },
      { path: 'category/*', lazy: () => import('@/pages/catalog') },
      { path: 'product/:slug', lazy: () => import('@/pages/product') },
      { path: 'search', lazy: () => import('@/pages/search') },
      { path: 'garage', lazy: () => import('@/pages/garage') },
      { path: 'cart', lazy: () => import('@/pages/cart') },
      { path: 'checkout', lazy: () => import('@/pages/checkout') },
      { path: 'checkout/success/:orderId', lazy: () => import('@/pages/checkout-success') },
      { path: 'checkout/fail/:orderId', lazy: () => import('@/pages/checkout-fail') },
      { path: 'favorites', lazy: () => import('@/pages/favorites') },
      {
        path: 'profile',
        lazy: () => import('@/pages/profile'),
        children: [
          { index: true, lazy: () => import('@/pages/profile/orders') },
          { path: 'orders', lazy: () => import('@/pages/profile/orders') },
          { path: 'orders/:id', lazy: () => import('@/pages/profile/order-detail') },
          { path: 'addresses', lazy: () => import('@/pages/profile/addresses') },
          { path: 'settings', lazy: () => import('@/pages/profile/settings') },
        ],
      },
      { path: 'seller/:id', lazy: () => import('@/pages/seller') },
      { path: 'become-seller', lazy: () => import('@/pages/become-seller') },
      { path: ':slug', lazy: () => import('@/pages/static-page') },
      { path: '*', lazy: () => import('@/pages/not-found') },
    ],
  },
])
