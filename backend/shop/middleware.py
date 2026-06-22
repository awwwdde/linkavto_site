from django.utils.deprecation import MiddlewareMixin
import time


class DefaultCaptchaRequiredMiddleware(MiddlewareMixin):
    """Устанавливает request.captcha_required = False по умолчанию."""
    def process_request(self, request):
        request.captcha_required = False
        request.turnstile_site_key = ''


class ProductStatisticsMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(request, 'user') and 'product' in view_kwargs:
            # Отслеживание просмотров товаров
            product_slug = view_kwargs.get('slug')
            if product_slug:
                request._product_view_start = time.time()

    def process_response(self, request, response):
        if hasattr(request, '_product_view_start') and hasattr(request, 'user'):
            from .models import Product, ProductView

            product_slug = request.resolver_match.kwargs.get('slug')
            if product_slug:
                try:
                    product = Product.objects.get(slug=product_slug)
                    duration = time.time() - request._product_view_start

                    ProductView.objects.create(
                        product=product,
                        user=request.user if request.user.is_authenticated else None,
                        session_key=request.session.session_key,
                        duration=int(duration)
                    )

                    # Обновляем счетчик просмотров товара
                    product.views += 1
                    product.save(update_fields=['views'])

                except Product.DoesNotExist:
                    pass

        return response


class CaptchaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Исключаем статические файлы и API endpoints
        if (request.path.startswith('/static/') or
                request.path.startswith('/media/') or
                request.path.startswith('/admin/') or
                request.path.startswith('/search/api/') or
                request.path in ['/slider-captcha/', '/verify-slider-captcha/']):
            return self.get_response(request)

        # Проверяем, прошла ли капча
        captcha_passed = request.session.get('captcha_passed', False)
        captcha_timestamp = request.session.get('captcha_timestamp', 0)

        # Капча действительна 24 часа
        if captcha_passed and (time.time() - captcha_timestamp) < 86400:
            request.captcha_required = False
            return self.get_response(request)

        from django.conf import settings
        site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
        # Не показывать капчу, если ключ не задан — виджет сломается
        if not site_key:
            request.captcha_required = False
            request.turnstile_site_key = ''
            return self.get_response(request)

        from django.shortcuts import redirect
        from urllib.parse import quote
        request.captcha_required = True
        request.turnstile_site_key = site_key
        return redirect('/slider-captcha/?next=' + quote(request.get_full_path(), safe='/:@!$&\'()*+,;='))