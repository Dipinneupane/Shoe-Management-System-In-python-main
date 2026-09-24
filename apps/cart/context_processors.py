from .models import Cart

def cart_count(request):
    if request.user.is_authenticated:
        total = Cart.objects.filter(user=request.user).count()
        return {'cart_count': total}
    return {'cart_count': 0}
