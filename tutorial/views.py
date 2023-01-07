from django.shortcuts import render
import stripe
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *

stripe.api_key = settings.STRIPE_PRIVATE_KEY
# endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
YOUR_DOMAIN = 'http://127.0.0.1:8000'


#home view
def home(request):
    return render(request,'checkout.html')

#success view
def success(request):
    return render(request,'success.html')

 #cancel view
def cancel(request):
    return render(request,'cancel.html')


@csrf_exempt
def create_checkout_session(request):
    #Updated- creating Order object
    order=Order(email=" ",paid="False",amount=0,description=" ")
    order.save()
    session = stripe.checkout.Session.create(
    client_reference_id=request.user.id if request.user.is_authenticated else None,
    payment_method_types=['card'],
    line_items=[{
    'price_data': {
    'currency': 'usd',
    'product_data': {
    'name': 'Intro to Django Course',
    },
    'unit_amount': 10000,
    },
    'quantity': 1,
    }],
    #Update - passing order ID in checkout to update the order object in webhook
    metadata={
    "order_id":order.id
    },
    mode='payment',
    success_url=YOUR_DOMAIN + '/success.html',
    cancel_url=YOUR_DOMAIN + '/cancel.html',
    )
    return JsonResponse({'id': session.id})

@csrf_exempt
def webhook(request):
    print("Webhook")
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
    payload, sig_header, endpoint_secret
    )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
    # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        #NEW CODE
        session = event['data']['object']
        #getting information of order from session
        customer_email = session["customer_details"]["email"]
        price = session["amount_total"] /100
        sessionID = session["id"]
        #grabbing id of the order created
        ID=session["metadata"]["order_id"]
        #Updating order
        Order.objects.filter(id=ID).update(email=customer_email,amount=price,paid=True,description=sessionID)

    return HttpResponse(status=200)
