def ecommerce_context(request):
    wishlist_ids = []
    for item in request.session.get('wishlist', []):
        try:
            wishlist_ids.append(int(item))
        except (TypeError, ValueError):
            continue

    cart_count = 0
    if request.user.is_authenticated:
        cart = getattr(request.user, 'cart', None)
        if cart is not None:
            cart_count = cart.total_items()

    return {
        'wishlist_ids': wishlist_ids,
        'wishlist_count': len(wishlist_ids),
        'cart_count': cart_count,
    }
