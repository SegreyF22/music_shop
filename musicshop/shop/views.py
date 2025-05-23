from django.shortcuts import render
from django import views
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import authenticate, login
from utils import recalc_cart
from .mixins import CartMixin, NotificationsMixin
from .models import Artist, Album, Customer, CartProduct, Notification
from .forms import LoginForm, RegistrationForm, OrderForm
from django.db import transaction


class BaseView(CartMixin, NotificationsMixin, views.View):

    def get(self, request, *args, **kwargs):
        album = Album.objects.all().order_by('-id')[:5]
        month_bestseller, month_bestseller_qty = Album.objects.get_month_bestseller()
        context = {
            'albums': album,
            'cart': self.cart,
            'notifications': self.notifications(request.user)
        }
        if month_bestseller:
            context.update({'month_bestseller':month_bestseller, 'month_bestseller_qty':month_bestseller_qty})
        return render(request, 'base.html', context)


class ArtistDetailView(NotificationsMixin, views.generic.DetailView):
    model = Artist
    template_name = 'artist/artist_detail.html'
    slug_url_kwarg = 'artist_slug'
    context_object_name = 'artist'


class AlbumDetailView(CartMixin, NotificationsMixin, views.generic.DetailView):
    model = Album
    template_name = 'album/album_detail.html'
    slug_url_kwarg = 'album_slug'
    context_object_name = 'album'


class LoginView(views.View):

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        context = {
            'form': form
        }
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return HttpResponseRedirect('/')
        context = {
            'form': form
        }
        return render(request, 'login.html', context)


class RegistrationView(views.View):

    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        context = {
            'form': form
        }
        return render(request, 'registration.html', context)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = form.cleaned_data['username']
            new_user.email = form.cleaned_data['email']
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Customer.objects.create(
                user=new_user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            login(request, user)
            return HttpResponseRedirect('/')
        context = {
            'form': form
        }
        return render(request, 'registration.html', context)


class AccountView(CartMixin, NotificationsMixin, views.View):

    def get(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        context = {
            'customer': customer,
            'cart': self.cart,
            'notifications': self.notifications(request.user)
        }
        return render(request, 'account.html', context)


class CartView(CartMixin, NotificationsMixin, views.View):

    def get(self, request, *args, **kwargs):
        return render(request, 'cart.html', {'cart': self.cart, 'notifications': self.notifications(request.user)})


class AddToCartView(CartMixin, views.View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product, created = CartProduct.objects.get_or_create(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )
        if created:
            self.cart.products.add(cart_product)
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, 'Товар добавлен в корзину')
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class DeleteFromCartView(CartMixin, views.View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, 'Товар удален из корзины')
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class ChangeQTYView(CartMixin, views.View):

    def post(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )
        qty = int(request.POST.get('qty'))
        cart_product.qty = qty
        cart_product.save()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, 'Количество товара изменено')
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class AddToWishlist(views.View):

    @staticmethod
    def get(request, *args, **kwargs):
        album = Album.objects.get(id=kwargs['album_id'])
        customer = Customer.objects.get(user=request.user)
        customer.wishlist.add(album)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class ClearNotificationsView(views.View):

    @staticmethod
    def get(request, *args, **kwargs):
        Notification.objects.make_all_read(request.user.customer)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class RemoveFromWishListView(views.View):

    @staticmethod
    def get(request, *args, **kwargs):
        album = Album.objects.get(id=kwargs['album_id'])
        customer = Customer.objects.get(user=request.user)
        customer.wishlist.remove(album)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class CheckoutView(CartMixin, NotificationsMixin, views.View):

    def get(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'form': form,
            'notifications': self.notifications(request.user)
        }
        return render(request, 'checkout.html', context)


class MakeOrderView(CartMixin, views.View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        customer = Customer.objects.get(user=request.user)
        if form.is_valid():
            out_of_stock = []
            more_than_on_stock = []
            out_of_stock_message = ''
            more_than_on_stock_message = ''
            for item in self.cart.products.all():
                if not item.content_object.stock:
                    out_of_stock.append(' - '.join([item.content_object.artist.name, item.content_object.name]))
                if item.content_object.stock and item.content_object.stock < item.qty:
                    more_than_on_stock.append(
                        {'product': ' - '.join([item.content_object.artist.name, item.content_object.name]),
                         'stock':item.content_object.stock, 'qty': item.qty})
            if out_of_stock:
                out_of_stock_products = ', '.join(out_of_stock)
                out_of_stock_message = f'Товара уже нет в наличии: {out_of_stock_products}.\n'
            if more_than_on_stock_message:
                for item in more_than_on_stock:
                    more_than_on_stock_message += (f'Товар: {item["products"]},'
                                                   f'В наличии: {item["stock"]}'
                                                   f'Заказано: {item["qty"]}\n')
            error_message_for_customer = ''
            if out_of_stock:
                error_message_for_customer = out_of_stock_message + '\n'
            if more_than_on_stock:
                error_message_for_customer += more_than_on_stock_message + '\n'
            if error_message_for_customer:
                messages.add_message(request, messages.INFO, error_message_for_customer)
                return HttpResponseRedirect('/checkout/')
            # если все ок и надо сохранить инфу о новом заказе
            new_order = form.save(commit=False)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.order_data = form.cleaned_data['order_data']
            # new_order.comment = form.cleaned_data['comment']
            new_order.save()
            # сохраняем корзину
            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            customer.orders.add(new_order)
            # уменьшение кол-ва товара на кол-во заказанного товара
            for item in self.cart.products.all():
                item.content_object.stock -= item.stock
                item.content_object.save()

            messages.add_message(request, messages.INFO, 'Спасибо за заказ! Менеджер с Вами свяжется')
            return HttpResponseRedirect('/')
        return HttpResponseRedirect('/')









