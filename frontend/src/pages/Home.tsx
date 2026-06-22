import { useEffect, useState } from 'react'
import { getHome, getCategories, type HomeData, type Category } from '../api'
import HeroCarousel from '../components/HeroCarousel'
import CategoryGrid from '../components/CategoryGrid'
import ProductSection from '../components/ProductSection'

export default function Home() {
  const [home, setHome] = useState<HomeData | null>(null)
  const [categories, setCategories] = useState<Category[]>([])

  useEffect(() => {
    getHome().then(setHome).catch(console.error)
    getCategories('root').then(setCategories).catch(console.error)
  }, [])

  return (
    <div className="mx-auto max-w-[1520px] px-4">
      <HeroCarousel slides={home?.carousel_slides ?? []} />

      <section className="mb-4 flex justify-center">
        <CategoryGrid categories={categories} />
      </section>

      {home && (
        <>
          <ProductSection title="Новинки" products={home.new_products} />
          <ProductSection title="Распродажа" products={home.sale_products} />
          <ProductSection title="Популярные товары" products={home.popular_products} />
          <ProductSection title="Лидеры продаж" products={home.bestsellers} />
        </>
      )}
    </div>
  )
}
