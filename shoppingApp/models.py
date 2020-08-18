from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.

class UserProfile(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None)
    address = models.CharField(max_length=512, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Category(models.Model):

    name = models.CharField(max_length=256)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', on_delete=models.CASCADE)

    def __str__(self):
        return "{0}".format(self.name)

    def get_parents(self):

        def get_parent_recursive_(item=None, lst_item=[]):

            if item:
                lst_item.append(item)

                if item.parent:
                    return get_parent_recursive_(item.parent, lst_item)

            return lst_item

        return get_parent_recursive_(self)[::-1]

    def get_children(self):

        def get_children_recursive_(item=None, lst_item=[]):

            if item:
                lst_item.append(item)

                for child_ in item.children.all():
                    return get_children_recursive_(child_, lst_item)

            return lst_item

        return get_children_recursive_(self)

class Product(models.Model):

    TYPE_CHOICES = (
        ("парче", "парче"),
        ("кг", "килограм"),
        ("л", "литар")
    )

    category = models.ForeignKey(Category, related_name='products', null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=256)
    brand = models.CharField(max_length=256, null=True, blank=True)
    description_title = models.CharField(max_length=256, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    product_type = models.CharField(choices=TYPE_CHOICES, null=True, blank=True, default=TYPE_CHOICES[0][0], max_length=256)
    price = models.DecimalField(decimal_places=2, max_digits=6, null=True, blank=True)
    image = models.ImageField(upload_to='uploads/', null=True, blank=True)

    def __str__(self):
        return "{0}: [{1}]".format(self.title, self.price)


class OrderProduct(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0.0)

    def get_amount(self):
        return self.product.price * self.quantity if self.product and self.product.price else 0

    def __str__(self):
        return "{0} x {1}".format(self.product, self.quantity)

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderProduct)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)

def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)

models.signals.post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)