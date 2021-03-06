from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView
from .models import Booking
from profiles.models import UserProfile
from .forms import BookingForm, BookThisMotorhomeForm
from django.contrib import messages
from motorhomes.models import Motorhome
import json
import dateutil
from dateutil.parser import parse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from checkout.models import BillingAddress, BookingSummary
from checkout.views import CheckoutAddressView, CheckoutView

# a view to show all bookings


@staff_member_required
def BookingListView(request):

    bookings = Booking.objects.all()

    context = {
        'bookings': bookings,
    }
    return render(request, 'bookings/bookings_list.html', context)


# a view to show user's bookings
@login_required
def MyBookings(request):
    if not request.user.is_authenticated:
        messages.add_message(
            request, messages.WARNING, 'Please login or register to view this page')
        return redirect(reverse('motorhomes'))

    user = request.user
    bookings = Booking.objects.filter(booked_by=user).order_by('-booked_on')
    bsummaries = BookingSummary.objects.filter(
        user=request.user).order_by('-date_created')
    context = {
        'bookings': bookings,
        'bsummaries': bsummaries,
    }
    return render(request, 'bookings/my_bookings.html', context)


class BookingView(CreateView):
    # A view to create Booking
    model = Booking
    template_name = 'bookings/create_booking.html'
    fields = '__all__'
    success_url = reverse_lazy('create_booking')

# a view to create booking with a choosen vehicle


@login_required
def BookThisMotorhome(request, pk):
    """ This view is to create a booking after choosing motorhome """
    if not request.user.is_authenticated:
        messages.add_message(
            request, messages.WARNING, 'Please login or register to create your booking.')
        return redirect(reverse('motorhomes'))
    user = request.user
    template = 'bookings/book_this_motorhome.html'
    motorhome = get_object_or_404(Motorhome, pk=pk)
    form = BookThisMotorhomeForm()
    context = {
        'motorhome': motorhome,
        'form': form,
    }
    if request.method == 'POST':
        request.session['user.pk'] = user.pk
        # get the dates from the form
        booked_from = request.POST.get('start_date', False)
        booked_until = request.POST.get('end_date', False)
        # using dateutils to parse the date passed from the page to django accepted format
        booked_until_parsed = dateutil.parser.parse(booked_until)
        booked_from_parsed = dateutil.parser.parse(booked_from)
        # should the from date larger then the until or the same, return to this page with warning
        if (booked_until_parsed - booked_from_parsed).days < 1:
            messages.add_message(
                request, messages.WARNING, 'Please check your dates, something wrong')
            return render(request, template, context)

        td = booked_until_parsed-booked_from_parsed
        # get days to count the total
        days = td.days
        total = td.days*motorhome.daily_rental_fee
        try:
            # create booking with the given details, others set to default
            booking = Booking(
                booked_by=user,
                booked_vehicle=motorhome,
                booked_from=booked_from,
                booked_until=booked_until,
            )
            booking.save()
            # add booking information to session
            # so it can be accessed later on
            request.session['motorhome.pk'] = pk

            request.session['days'] = days
            request.session['total'] = total
            request.session['booked_from'] = booked_from
            request.session['booked_until'] = booked_until
            request.session['booking_id'] = booking.booking_id
            # uopdate userprofile instance with the last booking ref
            UserProfile.objects.filter(pk=user.id).update(
                last_booking_ref=booking.booking_id)

            # If user has billingaddress then go to the checkout view,
            # no billing address saved, redirect to the checkout checkout view to add it before go to payment
            billingaddress = BillingAddress.objects.filter(user=request.user)
            if billingaddress:
                return redirect(reverse('checkout'))
                messages.add_message(request, messages.SUCCESS,
                                     "Your Booking has been created, let's go to checkout")
            else:
                return redirect(reverse('checkout_address'))
                messages.add_message(request, messages.SUCCESS,
                                     "Your Booking has been created, let's add a billingadress")
        except:
            messages.add_message(request, messages.ERROR,
                                 'Sorry, We were unable to create your booking, please try again or contact us')
            return render(request, template, context)

    return render(request, template, context)


@login_required
def CheckoutThisBooking(request, pk):
    """ This view is to redirect user to
    checkout from the my bookings page
    This can happen if the user have not finished the checkout
    after the booking was made
    """

    try:
        booking = Booking.objects.get(pk=pk)
        motorhome = get_object_or_404(Motorhome, pk=booking.booked_vehicle.id)
        user = request.user
        request.session['user.pk'] = user.pk
        # get the dates from the form
        booked_from = booking.booked_from
        booked_until = booking.booked_until
        td = booked_until-booked_from
        # get days to count the total
        days = td.days
        total = td.days*motorhome.daily_rental_fee
        request.session['motorhome.pk'] = motorhome.id
        request.session['days'] = days
        request.session['total'] = total
        request.session['booked_from'] = booked_from.isoformat()
        request.session['booked_until'] = booked_until.isoformat()
        request.session['booking_id'] = booking.booking_id
        # uopdate userprofile instance with the last booking ref
        UserProfile.objects.filter(pk=user.id).update(
            last_booking_ref=booking.booking_id)
        # If user has billingaddress then go to the checkout view,
        # no billing address saved, redirect to the checkout checkout view to add it before go to payment
        billingaddress = BillingAddress.objects.filter(user=request.user)
        if billingaddress:
            return redirect(reverse('checkout'))
            messages.add_message(request, messages.SUCCESS,
                                 "Billing Address found, let's checkout")
        else:
            return redirect(reverse('checkout_address'))
            messages.add_message(request, messages.SUCCESS,
                                 "Billing Address not found, let's add a billing adress")
    except:
        messages.add_message(request, messages.ERROR,
                             'Sorry, We were unable to progress with your booking, please try again or contact us')
        return redirect(reverse(MyBookings))
