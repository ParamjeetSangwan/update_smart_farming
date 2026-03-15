from django.shortcuts import render, get_object_or_404, redirect
from .models import Tool, Pesticide
from orders.models import Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# ---------------- Home ----------------
def marketplace_home(request):
    return render(request, 'marketplace/marketplace_home.html')


# ---------------- Tools ----------------
@login_required
def tools_view(request):
    tools = Tool.objects.all()

    categories = Tool.objects.values_list('category', flat=True).distinct().order_by('category')
    min_price = Tool.objects.order_by('price').first().price if Tool.objects.exists() else 0
    max_price = Tool.objects.order_by('-price').first().price if Tool.objects.exists() else 1000

    selected_category = request.GET.get('category')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if selected_category and selected_category != "All":
        tools = tools.filter(category=selected_category)

    if price_min:
        tools = tools.filter(price__gte=price_min)
    if price_max:
        tools = tools.filter(price__lte=price_max)

    return render(request, 'marketplace/tools.html', {
        'tools': tools,
        'categories': categories,
        'min_price': min_price,
        'max_price': max_price,
        'selected_category': selected_category,
        'price_min': price_min,
        'price_max': price_max,
    })


def tool_detail(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    return render(request, 'marketplace/tool_detail.html', {'tool': tool})


@login_required
def add_tool_to_cart(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    cart = request.session.get("cart", [])

    found = False
    for item in cart:
        if item["item_id"] == tool.id and item["item_type"] == "tool":
            item["quantity"] += 1
            found = True
            break

    if not found:
        cart.append({
            "item_type": "tool",
            "item_id": tool.id,
            "name": tool.name,
            "price": float(tool.price),
            "quantity": 1
        })

    request.session["cart"] = cart
    request.session.modified = True
    return redirect("marketplace:cart_view")


# ---------------- Pesticides ----------------
def pesticides_view(request):
    pesticides = Pesticide.objects.all()
    return render(request, 'marketplace/pesticides.html', {'pesticides': pesticides})


def pesticide_detail(request, pesticide_id):
    pesticide = get_object_or_404(Pesticide, id=pesticide_id)
    return render(request, 'marketplace/pesticides_detail.html', {'pesticide': pesticide})


@login_required
def add_pesticide_to_cart(request, pesticide_id):
    pesticide = get_object_or_404(Pesticide, id=pesticide_id)
    cart = request.session.get("cart", [])

    quantity = int(request.POST.get("quantity", 1))

    found = False
    for item in cart:
        if item["item_id"] == pesticide.id and item["item_type"] == "pesticide":
            item["quantity"] += quantity
            found = True
            break

    if not found:
        cart.append({
            "item_type": "pesticide",
            "item_id": pesticide.id,
            "name": pesticide.name,
            "price": float(pesticide.price),
            "quantity": quantity
        })

    request.session["cart"] = cart
    request.session.modified = True
    return redirect("marketplace:cart_view")


# ---------------- Cart ----------------
@login_required
def cart_view(request):
    cart = request.session.get("cart", [])
    cart_items = []
    total_price = 0

    for item in cart:
        try:
            product = None
            if item["item_type"] == "tool":
                product = Tool.objects.get(id=item["item_id"])
            elif item["item_type"] == "pesticide":
                product = Pesticide.objects.get(id=item["item_id"])

            if product:
                quantity = int(item.get("quantity", 1))
                subtotal = product.price * quantity

                cart_items.append({
                    "item_id": item["item_id"],
                    "item_type": item["item_type"],
                    "product": product,
                    "quantity": quantity,
                    "subtotal": subtotal,
                })

                total_price += subtotal
        except (Tool.DoesNotExist, Pesticide.DoesNotExist):
            continue

    return render(request, "marketplace/cart.html", {
        "cart_items": cart_items,
        "total_price": total_price,
    })


@login_required
def update_cart(request):
    if request.method == "POST":
        cart = request.session.get("cart", [])
        updated_cart = []

        for i in range(len(cart)):
            item_id = request.POST.get(f"item_id_{i}")
            item_type = request.POST.get(f"item_type_{i}")
            quantity = request.POST.get(f"quantity_{i}")

            if item_id and quantity:
                try:
                    quantity = int(quantity)
                except ValueError:
                    quantity = 1

                if quantity > 0:
                    for item in cart:
                        if str(item["item_id"]) == str(item_id) and item["item_type"] == item_type:
                            item["quantity"] = quantity
                            updated_cart.append(item)
                            break

        request.session["cart"] = updated_cart
        request.session.modified = True

    return redirect("marketplace:cart_view")


# ---------------- Checkout / Orders ----------------
@login_required
def checkout_view(request):
    cart = request.session.get("cart", [])
    cart_items = []
    total_price = 0

    for item in cart:
        try:
            product = None
            if item["item_type"] == "tool":
                product = Tool.objects.get(id=item["item_id"])
            elif item["item_type"] == "pesticide":
                product = Pesticide.objects.get(id=item["item_id"])

            if product:
                quantity = int(item.get("quantity", 1))
                subtotal = float(product.price) * quantity

                cart_items.append({
                    "item_id": item["item_id"],
                    "item_type": item["item_type"],
                    "product": product,
                    "quantity": quantity,
                    "subtotal": subtotal,
                })

                total_price += subtotal
        except (Tool.DoesNotExist, Pesticide.DoesNotExist):
            continue

    return render(request, "marketplace/checkout.html", {
        "cart_items": cart_items,
        "total_price": total_price,
    })


@login_required
def confirm_order(request):
    """Confirm checkout and create an Order + OrderItems"""
    cart = request.session.get("cart", [])
    if not cart:
        return redirect("marketplace:cart_view")

    total_price = sum(item["price"] * item["quantity"] for item in cart)
    order = Order.objects.create(user=request.user, total_price=total_price)

    for item in cart:
        OrderItem.objects.create(
            order=order,
            item_type=item["item_type"],
            item_id=item["item_id"],
            name=item["name"],
            price=item["price"],
            quantity=item["quantity"],
        )

    # clear session cart
    request.session["cart"] = []
    request.session.modified = True

    return redirect("marketplace:my_orders")


@login_required
def my_orders(request):
    """Show user's past orders with product details"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')

    for order in orders:
        for item in order.items.all():
            if item.item_type == 'tool':
                item.product = Tool.objects.filter(id=item.item_id).first()
            elif item.item_type == 'pesticide':
                item.product = Pesticide.objects.filter(id=item.item_id).first()
            else:
                item.product = None

    return render(request, 'marketplace/my_orders.html', {'orders': orders})

def place_order(request):
    if request.method == "POST":
        # Example: create a new order for the logged-in user
        order = Order.objects.create(user=request.user)

        # (If you have a cart system, fetch cart items here)
        cart_items = []  # Replace with your actual cart logic
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

        return redirect('marketplace:my_orders')

    return render(request, 'marketplace/place_order.html')



def clear_orders(request):
    if request.method == "POST":
        Order.objects.filter(user=request.user).delete()
        messages.success(request, "All your orders have been cleared.")
    return redirect("marketplace:my_orders")