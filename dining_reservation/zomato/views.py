from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.utils import timezone
from django.contrib.auth.models import User
from .models import DiningPlace, Booking, Token
from .forms import SignUpForm, DiningPlaceForm, BookingForm
from django.shortcuts import get_object_or_404
import json

def admin_required(view_func):
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({"error": "Admin access required"}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapped

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        form = SignUpForm(data)
        if form.is_valid():
            user = form.save()
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({
                "status": "Account successfully created",
                "status_code": 200,
                "user_id": user.id
            })
        else:
            return JsonResponse({"errors": form.errors}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=405)

@csrf_exempt
def user_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({
                "status": "Login successful",
                "status_code": 200,
                "user_id": user.id,
                "access_token": token.key,
                "token_type": "Bearer"
            })
        else:
            return JsonResponse({
                "status": "Incorrect username/password provided. Please retry",
                "status_code": 401
            }, status=401)
    return JsonResponse({"error": "Invalid request"}, status=405)

# def token_required(view_func):
#     def wrapped(request, *args, **kwargs):
#         auth_header = request.META.get('HTTP_AUTHORIZATION')
#         if not auth_header:
#             return JsonResponse({"error": "No token provided"}, status=401)
#         try:
#             _, token = auth_header.split()
#             user_token = Token.objects.get(key=token)
#             request.user = user_token.user
#         except (ValueError, Token.DoesNotExist):
#             return JsonResponse({"error": "Invalid token"}, status=401)
#         return view_func(request, *args, **kwargs)
#     return wrapped

def token_required(view_func):
    def wrapped(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return JsonResponse({"error": "No token provided"}, status=401)
        try:
            auth_parts = auth_header.split()
            if auth_parts[0].lower() != "bearer" or len(auth_parts) != 2:
                return JsonResponse({"error": "Invalid token format"}, status=401)
            token = auth_parts[1]
            user_token = Token.objects.get(key=token)
            request.user = user_token.user
        except (IndexError, Token.DoesNotExist):
            return JsonResponse({"error": "Invalid token"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapped

@csrf_exempt
@token_required
@admin_required
def create_dining_place(request):
    if not request.user.is_staff:
        return JsonResponse({"error": "Permission denied"}, status=403)
    if request.method == 'POST':
        data = json.loads(request.body)
        form = DiningPlaceForm(data)
        if form.is_valid():
            place = form.save()
            return JsonResponse({
                "message": f"{place.name} added successfully",
                "place_id": place.id,
                "status_code": 200,
            })
        else:
            return JsonResponse({"errors": form.errors}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=405)

@csrf_exempt
@token_required
@admin_required
def update_dining_place(request, place_id):             #For Updating Existing Dining Place Details
    if request.method == 'PUT':
        place = get_object_or_404(DiningPlace, id=place_id)
        data = json.loads(request.body)
        form = DiningPlaceForm(data, instance=place)
        if form.is_valid():
            updated_place = form.save()
            return JsonResponse({
                "message": f"{updated_place.name} updated successfully",
                "place_id": updated_place.id,
                "status_code": 200
            })
        else:
            return JsonResponse({"errors": form.errors}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=405)


@csrf_exempt
@token_required
@admin_required
def delete_dining_place(request, place_id):
    if request.method == 'DELETE':
        place = get_object_or_404(DiningPlace, id=place_id)
        place_name = place.name
        place.delete()
        return JsonResponse({
            "message": f"{place_name} deleted successfully",
            "status_code": 200
        })
    return JsonResponse({"error": "Invalid request"}, status=405)

@token_required
def search_dining_places(request):
    if request.method == 'GET':
        name = request.GET.get('name', '')
        places = DiningPlace.objects.filter(name__icontains=name)
        results = [
            {
                "place_id": place.id,
                "name": place.name,
                "address": place.address,
                "phone_no": place.phone_no,
                "website": place.website,
                "operational_hours": {
                    "open_time": place.open_time.strftime("%H:%M:%S"),
                    "close_time": place.close_time.strftime("%H:%M:%S")
                }
            } for place in places
        ]
        return JsonResponse({"results": results})
    return JsonResponse({"error": "Invalid request"}, status=405)

@token_required
def check_availability(request, place_id):
    if request.method == 'GET':
        place = DiningPlace.objects.get(id=place_id)
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        
        if not start_time or not end_time:
            return JsonResponse({"error": "start_time and end_time are required"}, status=400)

        start_time = timezone.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_time = timezone.datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        conflicting_bookings = Booking.objects.filter(
            dining_place=place,
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if conflicting_bookings.exists():
            next_available = conflicting_bookings.order_by('-end_time').first().end_time
            return JsonResponse({
                "place_id": place.id,
                "name": place.name,
                "phone_no": place.phone_no,
                "available": False,
                "next_available_slot": next_available.isoformat()
            })
        else:
            return JsonResponse({
                "place_id": place.id,
                "name": place.name,
                "phone_no": place.phone_no,
                "available": True,
                "next_available_slot": None
            })
    return JsonResponse({"error": "Invalid request"}, status=405)

@csrf_exempt
@token_required
def book_dining_place(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        form = BookingForm(data)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user

            conflicting_bookings = Booking.objects.filter(
                dining_place=booking.dining_place,
                start_time__lt=booking.end_time,
                end_time__gt=booking.start_time
            )

            if conflicting_bookings.exists():
                return JsonResponse({
                    "status": "Slot is not available at this moment, please try some other place",
                    "status_code": 400
                }, status=400)

            booking.save()
            return JsonResponse({
                "status": "Slot booked successfully",
                "status_code": 200,
                "booking_id": booking.id
            })
        else:
            return JsonResponse({"errors": form.errors}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=405)