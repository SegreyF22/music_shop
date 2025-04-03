from django import views
from .models import Cart, Customer


class CartMixin(views.generic.detail.SingleObjectMixin, views.View):

    # проверяет авторизован ли пользователь и
    def dispatch(self, request, *args, **kwargs):
        cart = None
        if request.user.is_authenticated:
            customer = Customer.objects.filter(user=request.user).first()
            if not customer:
                customer = Customer.objects.create(user=request.user)
            cart = Cart.objects.filter(owner=customer, in_order=False).first()
            if not cart:
                cart = Cart.objects.create(owner=customer)
        # else:
        #     cart = Cart.objects.filter(for_anonymous_user=True).first()
        #     if not cart:
        #         cart = Cart.objects.create(for_anonymous_user=True)
        self.cart = cart
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.cart
        return context
