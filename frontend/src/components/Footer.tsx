import { Link } from 'react-router-dom'

const col = (title: string, links: [string, string][]) => (
  <div className="mb-4">
    <h5 className="mb-3 font-bold">{title}</h5>
    <ul className="list-none p-0">
      {links.map(([label, href]) => (
        <li key={label} className="mb-2">
          <Link to={href} className="text-ink no-underline hover:underline">
            {label}
          </Link>
        </li>
      ))}
    </ul>
  </div>
)

export default function Footer() {
  return (
    <footer className="mt-20 bg-[#f8f9fa] py-8" role="contentinfo">
      <div className="mx-auto max-w-[1520px] px-4">
        <div className="grid grid-cols-4 gap-6 max-md:grid-cols-2">
          {col('Каталог товаров', [
            ['Легковые автомобили', '/category/legkovye-avtomobili'],
            ['Грузовые автомобили', '/category/gruzovye-avtomobili'],
            ['Мототехника', '/category/mototehnika'],
            ['Спецтехника', '/category/spectehnika'],
            ['Шины и диски', '/category/shiny-i-diski'],
          ])}
          {col('Информация', [
            ['О нас', '/about'],
            ['Помощь', '/help'],
            ['Стать продавцом', '/sellers/become'],
            ['Правила покупки', '/buyer-rules'],
            ['Правила продажи', '/seller-rules'],
          ])}
          {col('Политики', [
            ['Политика конфиденциальности', '/privacy'],
            ['Обработка персональных данных', '/personal-data'],
            ['Публичная оферта', '/public-offer'],
            ['Пользовательское соглашение', '/terms'],
            ['Условия возврата', '/return-policy'],
          ])}
          <div className="mb-4">
            <h5 className="mb-3 font-bold">Контакты</h5>
            <ul className="list-none p-0">
              <li className="mb-2">
                <a href="mailto:linkavto@linkavto.ru" className="text-ink no-underline hover:underline">
                  <i className="fas fa-envelope mr-2" />linkavto@linkavto.ru
                </a>
              </li>
              <li className="mb-2">
                <a href="tel:+79999999999" className="text-ink no-underline hover:underline">
                  <i className="fas fa-phone mr-2" />+7 (999) 999-99-99
                </a>
              </li>
            </ul>
          </div>
        </div>

        <hr className="my-6 border-gray-300" />

        <div className="text-center">
          <div className="flex justify-center">
            <svg width="44" height="44" viewBox="0 0 404 301" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M231.528 0H169.424C164.035 0 159.059 2.89151 156.391 7.57441L1.98888 278.574C-3.70848 288.574 3.51305 301 15.022 301H190.727C196.1 301 201.062 298.126 203.736 293.467L299.502 126.607C305.241 116.607 298.022 104.141 286.492 104.141H221.861C216.505 104.141 211.556 106.996 208.875 111.632L133.042 242.776C132.042 244.505 130.196 245.57 128.198 245.57C123.916 245.57 121.222 240.955 123.326 237.226L244.591 22.3728C250.234 12.3735 243.01 0 231.528 0Z" fill="#272526" />
              <path d="M352.303 207.945H288.578C277.077 207.945 269.854 220.357 275.537 230.356L311.368 293.411C314.033 298.102 319.013 301 324.409 301H388.356C399.875 301 407.096 288.554 401.378 278.554L365.324 215.5C362.653 210.828 357.684 207.945 352.303 207.945Z" fill="#89BEE8" />
            </svg>
          </div>
          <p className="mt-2">© 2026 LINKAVTO. Все права защищены.</p>
          <div className="mt-2">
            <small>Интернет-магазин автозапчастей для легковых автомобилей, грузовиков, спецтехники и мототехники</small>
          </div>
        </div>
      </div>
    </footer>
  )
}
