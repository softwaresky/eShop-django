from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.files import File
from django.utils import timezone
from django.contrib.auth import login, authenticate
from django.contrib.auth.signals import user_logged_in

from .models import *
from .forms import RegistrationForm

import json
import os
import pprint

# Create your views here.

def index(request):
    context = {}
    context["lst_category"] = Category.objects.filter(parent=None)
    # context.update(get_product_order_calculation_dict(request.session.get("cart_temp", None)))
    context.update(get_product_order_calculation_dict(request))
    return render(request, "shoppingApp/index.html", context)

def registration(request):

    if request.method == "POST":
        reg_form = RegistrationForm(request.POST)
        if reg_form.is_valid():
            user = reg_form.save()
            user.refresh_from_db()
            user.userprofile.address = reg_form.cleaned_data.get("address")
            user.save()
            password = reg_form.cleaned_data.get("password1")
            user = authenticate(username=user.username, password=password)
            login(request, user)
            return redirect("index")
    else:
        reg_form = RegistrationForm()

    context = {}
    context["form"] = reg_form

    return render(request, "shoppingApp/registration.html", context)

def select_category(request, category_id):

    # category = get_object_or_404(Category, pk=category_id)
    category = Category.objects.get(pk=category_id)
    lst_product = Product.objects.filter(category__in=category.get_children())

    context = {}
    context["selected_category"] = category.get_parents()
    context["lst_category"] = Category.objects.filter(parent=None)
    context["lst_product"] = lst_product
    # context.update(get_product_order_calculation_dict(request.session.get("cart_temp", None)))
    context.update(get_product_order_calculation_dict(request))

    return render(request, "shoppingApp/base.html", context)

def select_product(request, product_id):

    context = {}
    # product = get_object_or_404(Product, pk=product_id)
    product = Product.objects.get(pk=product_id)
    context["product"] = product
    context["lst_category"] = Category.objects.filter(parent=None)
    context["lst_category_parent"] = product.category.get_parents()
    context["category_zip"] = zip(range(len(product.category.get_parents())), product.category.get_parents())
    # context.update(get_product_order_calculation_dict(request.session.get("cart_temp", None)))
    context.update(get_product_order_calculation_dict(request))

    return render(request, "shoppingApp/product_detail.html", context)

def order_product(request, product_id, url_order_from):

    quantity_number = request.POST.get("quantity_number", None)
    try:
        quantity_number = float(quantity_number)
    except:
        pass

    if request.user.is_authenticated:
        # product = get_object_or_404(Product, pk=product_id)
        product = Product.objects.get(pk=product_id)
        order_product, created = OrderProduct.objects.get_or_create(product=product)
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(product__id=product.id).exists():
                order_product.quantity += quantity_number
                order_product.save()
            else:
                order_product.quantity = quantity_number
                order_product.save()
                order.items.add(order_product)
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(user=request.user, ordered_date=ordered_date)
            order_product.quantity = quantity_number
            order_product.save()
            order.items.add(order_product)
    else:

        # If user doesn't exist (isn't logged in)
        if request.POST and quantity_number:

            product_id_str = f"{product_id}"

            try:
                quantity_number = float(quantity_number)
            except:
                quantity_number = 0.0

            if "cart_temp" not in request.session:
                request.session["cart_temp"] = {}

            if product_id_str not in request.session["cart_temp"]:
                request.session["cart_temp"][product_id_str] = 0.0
            request.session["cart_temp"][product_id_str] += quantity_number

            request.session.modified = True

    return redirect(url_order_from)

def get_product_order_calculation_dict(request):

    dict_result = {}
    dict_products = {}

    if request.user.is_authenticated:
        # order = get_object_or_404(Order, user=request.user, ordered=False)
        order = None
        try:
            order = Order.objects.get(user=request.user, ordered=False)
        except:
            pass

        if order:
            for product_order_ in order.items.all():
                amount = float(product_order_.product.price) * product_order_.quantity

                dict_data = {}
                dict_data["id"] = product_order_.product.id
                dict_data["title"] = product_order_.product.title
                dict_data["price"] = float(product_order_.product.price)
                dict_data["product_type"] = product_order_.product.product_type
                dict_data["amount"] = amount
                dict_data["quantity"] = product_order_.quantity

                if product_order_.product.id not in dict_products:
                    dict_products[product_order_.product.id] = {}
                dict_products[product_order_.product.id] = dict_data

    else:
        dict_session_data = request.session.get("cart_temp", None)
        if dict_session_data:

            for product_id_, quantity_ in dict_session_data.items():

                try:
                    product_id_ = int(product_id_)
                except:
                    continue

                product = Product.objects.filter(id=product_id_).get()
                if product and product.price:
                    amount = float(product.price) * quantity_

                    dict_data = {}
                    dict_data["id"] = product.id
                    dict_data["title"] = product.title
                    dict_data["price"] = float(product.price)
                    dict_data["product_type"] = product.product_type
                    dict_data["amount"] = amount
                    dict_data["quantity"] = quantity_

                    if product.id not in dict_products:
                        dict_products[product.id] = {}
                    dict_products[product.id] = dict_data

    lst_product_quantity = list(dict_products.values())
    dict_result["lst_product_quantity"] = lst_product_quantity
    dict_result["cart_totals"] = sum([item["price"] * item["quantity"] for item in lst_product_quantity])

    return dict_result

def cart_update_item(request):

    product_id = request.GET.get("product_id", None)
    quantity_number = request.GET.get("quantity_number", None)

    if product_id and quantity_number is not None:
        product_id_str = f"{product_id}"
        try:
            quantity_number = float(quantity_number)
        except:
            pass

        if request.user.is_authenticated:
            # product = get_object_or_404(Product, pk=product_id)
            product = Product.objects.get(pk=product_id)

            order_qs = Order.objects.filter(user=request.user, ordered=False)
            if order_qs.exists():
                order = order_qs[0]
                if order.items.filter(product__id=product.id).exists():
                    order_product = order.items.filter(product__id=product.id).get()

                    order_product.quantity = quantity_number
                    order_product.save()

        elif "cart_temp" in request.session:
            if product_id_str not in request.session["cart_temp"]:
                request.session["cart_temp"][product_id_str] = 0.0
            request.session["cart_temp"][product_id_str] = quantity_number
            request.session.modified = True


    # dict_data = get_product_order_calculation_dict(request.session.get("cart_temp", None))
    dict_data = get_product_order_calculation_dict(request)

    return  render(request, 'shoppingApp/cart_summary.html', context=dict_data)

def cart_remove_item(request):
    product_id = request.GET.get("product_id", None)

    if product_id:
        if request.user.is_authenticated:
            # product = get_object_or_404(Product, pk=product_id)
            product = Product.objects.get(pk=product_id)
            order_qs = Order.objects.filter(user=request.user, ordered=False)
            if order_qs.exists():
                order = order_qs[0]
                if order.items.filter(product__id=product_id).exists():
                    order_product = OrderProduct.objects.filter(product=product)[0]
                    order.items.remove(order_product)
                    order_product.delete()
        else:
            product_id_str = f"{product_id}"
            if "cart_temp" in request.session:
                if product_id_str in request.session["cart_temp"]:
                    del request.session["cart_temp"][product_id_str]
                request.session.modified = True

    # dict_data = get_product_order_calculation_dict(request.session.get("cart_temp", None))
    dict_data = get_product_order_calculation_dict(request)

    return  render(request, 'shoppingApp/cart_summary.html', context=dict_data)

def order_product_from_session(request):

    if request.user.is_authenticated:
        dict_session_data = request.session.get("cart_temp", None)
        if dict_session_data:
            order_qs = Order.objects.filter(user=request.user, ordered=False)

            if order_qs.exists():
                order = order_qs[0]
            else:
                ordered_date = timezone.now()
                order = Order.objects.create(user=request.user, ordered_date=ordered_date)

            for product_id_, quantity_ in dict_session_data.items():
                try:
                    product_id_ = int(product_id_)
                except:
                    continue

                # product = get_object_or_404(Product, pk=product_id_)
                product = Product.objects.get(pk=product_id_)
                order_product, created = OrderProduct.objects.get_or_create(product=product)

                if order.items.filter(product__id=product.id).exists():
                    order_product.quantity += quantity_
                    order_product.save()
                else:
                    order_product.quantity = quantity_
                    order_product.save()
                    order.items.add(order_product)

            del request.session["cart_temp"]
            request.session.modified = True

def sig_fill_cart_from_session(sender, user, request, **kwargs):
    order_product_from_session(request)

user_logged_in.connect(sig_fill_cart_from_session)

def session_clear(request):
    request.session.clear()
    request.session.modified = True
    return redirect('/')


# --------------------------------------------------------------------------------------------------------------
# Feed database from json
def read_json(file_path=""):
    if file_path:
        return json.load(open(file_path, 'r', encoding='utf-8'))
    return None

def feed_db_from_json(json_path="", scrapy_storage_dir=""):

    insert_count = 0
    lst_product = read_json(json_path)

    lst_category = set()
    for dict_product_ in sorted(lst_product, key=lambda d: d["category_path"]):
        category_path = dict_product_["category_path"]
        lst_category.add(category_path)

    for category_path_ in sorted(lst_category):
        parent_category = None
        lst_split_category_path = f"{category_path_}".split("->")

        for i in range(len(lst_split_category_path)):
            category_ = lst_split_category_path[i]
            this_category = None

            if Category.objects.filter(name=category_).exists():
                this_category = Category.objects.get(name=category_)

            if not this_category:
                this_category = Category(name=category_, parent=parent_category)
                this_category.save()

            parent_category = this_category


    for dict_product_ in sorted(lst_product, key=lambda d: d["category_path"]):

        if not dict_product_["price"]:
            continue

        category_path = dict_product_["category_path"]
        lst_split_category_path = []
        for part_ in f"{category_path}".split("->"):
            if part_ not in lst_split_category_path:
                lst_split_category_path.append(part_)

        category_target = None

        for category_root_ in Category.objects.filter(name=lst_split_category_path[0], parent=None):

            find_count = 0
            this_category = category_root_

            for category_path_part_ in lst_split_category_path:

                for child_ in this_category.children.all():

                    if child_.name == category_path_part_:
                        this_category = child_
                        find_count += 1

                if find_count == len(lst_split_category_path)-1:
                    category_target = this_category
                    break

            if category_target:
                break


        image_path = ""
        for image_dict_ in dict_product_["images"]:
            image_path = os.path.abspath(os.path.join(scrapy_storage_dir, image_dict_["path"]))

        dict_kwargs = dict(dict_product_)
        dict_kwargs.pop("images")
        dict_kwargs.pop("image_urls")
        dict_kwargs.pop("category_path")

        dict_kwargs["category"] = category_target
        # dict_kwargs["image"] = image_path
        dict_kwargs["product_type"] = "парче" if dict_product_["product_type"] == "KOM" else "кг"

        is_exist = Product.objects.filter(**dict_kwargs).exists()

        if not is_exist:
            new_product = Product(**dict_kwargs)
            if image_path:
                new_product.image.save(os.path.basename(image_path), File(open(image_path, 'rb')), save=False)
            new_product.save()
            insert_count += 1

    return insert_count

def fill_data(request):
    json_path = r"C:\Users\Softwaresky\PycharmProjects\ScrapyProjects\eTinex\outputs\tinex_products_v004.json"
    scrapy_storage_dir = r"E:\tinex_scrapy_store\images"

    insert_count = feed_db_from_json(json_path=json_path, scrapy_storage_dir=scrapy_storage_dir)
    messages.add_message(request, messages.INFO, 'Filled data. Insert {0} number of Products'.format(insert_count))

    return render(request, "shoppingApp/index.html" , {})

def remove_data(request):
    # Category.objects.all().delete()
    # Product.objects.all().delete()
    # OrderProduct.objects.all().delete()
    # Order.objects.all().delete()

    print ("Remove all category and products")
    messages.add_message(request, messages.INFO, 'Remove all category and products')

    return render(request, "shoppingApp/index.html", {})
