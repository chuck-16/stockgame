from django.shortcuts import render, redirect, HttpResponseRedirect
from yahoo_fin import stock_info as si
import numpy as np
from math import isnan
from .forms import StockSearchForm
from datetime import datetime, timedelta
from pytz import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import NewUserForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import StockHolder
import json
import collections


def homepage(request):
    if request.method == "POST":
        form = StockSearchForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/stock/'+form.cleaned_data.get('ticker')+'/1d')

    form = StockSearchForm
    return render(request=request,
                  template_name="stonks/homepage.html",
                  context={'stocksearchform' : form,
                            'leaderboard' : get_leaderboard()})

def stock(request, ticker, length):
    if request.method == "POST":
        form = StockSearchForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/stock/'+form.cleaned_data.get('ticker')+'/1d')
    form = StockSearchForm

    closed = False
    profit = True
    ticker = ticker
    if length == "1d":
        has_data = False
        delta_number = 0
        while not has_data:
            try:
                data = get_stock_data_with_delta(delta_number, "1m", ticker)
                has_data = True
            except KeyError:
                has_data = False
                delta_number += 1
    elif length == "1w":
        data = get_stock_data_with_delta(5, '1m', ticker)
    elif length == "1m":
        data = get_stock_data_with_delta(30, '1d', ticker)
    elif length == "3m":
        data = get_stock_data_with_delta(90, '1d', ticker)
    elif length == "1y":
        data = get_stock_data_with_delta(365, '1d', ticker)
    else:
        return HttpResponseRedirect('/stock/'+ticker+'/1d')

    data_list = data['close'].tolist()
    data_list = [x for x in data_list if not isnan(x)]
    change = round(float(data_list.pop()) - float(data_list[0]), 2)
    percent_change = abs(round(change/round(float(data_list[0]), 3) * 100, 2))
    if change > 0:
        profit = False
    else:
        profit = True

    stock_holder = StockHolder.objects.filter(username=request.user.username)[0]
    data = json.loads(stock_holder.stocks or '{}')
    amount_owned = 0
    if ticker.upper() in data:
        amount_owned = data[ticker.upper()]

    return render(request=request,
                  template_name="stonks/stock.html",
                  context={"stockprice": data_list,
                  "stockdates" :  [""] * len(data_list),
                  "stockname" : ticker.upper(),
                  "stockpricenow" : round(si.get_live_price(ticker), 2),
                  "length" : length,
                  "profit" : profit,
                  "change" : change,
                  "percentchange" : f'{percent_change}%',
                  "amountowned" : amount_owned,
                  'stocksearchform': form})

def logout_request(request):
    logout(request)
    return HttpResponseRedirect('/')

def register(request):

    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"New Account Created: {username}")
            login(request, user)
            messages.info(request, f"You are now logged in as {username}")
            StockHolder.objects.create(username=username, stocks='', buying_power=1000)
            return HttpResponseRedirect('/')
        else:
            for msg in form.error_messages:
                messages.error(request, f"{msg}: {form.error_messages[msg]}")
    form = NewUserForm
    return render(request=request,
        template_name="stonks/register.html",
        context={"form":form})

def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}")
                return HttpResponseRedirect('/')

    form = AuthenticationForm()

    return render(request=request,
                  template_name="stonks/login.html",
                  context={"form":form})

def buy_request(request, ticker):
    user = request.user
    stock_holder = StockHolder.objects.filter(username=user.username)[0]
    live_price = si.get_live_price(ticker)

    if user.is_authenticated and stock_holder.buying_power >= live_price:
        stock_holder.buy_stock(ticker, live_price, 1)

    return HttpResponseRedirect('/stock/'+ticker+'/1d')

def sell_request(request, ticker):
    user = request.user
    stock_holder = StockHolder.objects.filter(username=user.username)[0]
    live_price = si.get_live_price(ticker)
    data = json.loads(stock_holder.stocks or '{}')

    if user.is_authenticated and ticker.upper() in data:
        stock_holder.sell_stock(ticker, live_price, 1)

    return HttpResponseRedirect('/stock/'+ticker+'/1d')

def account(request, username):
    if request.method == "POST":
        stock_search_form = StockSearchForm(request.POST)
        if stock_search_form.is_valid():
            return HttpResponseRedirect('/stock/'+stock_search_form.cleaned_data.get('ticker')+'/1d')
    stock_search_form = StockSearchForm

    stock_holder = StockHolder.objects.filter(username=username)[0]
    stock_data = json.loads(stock_holder.stocks)
    asset_value = get_portfoilio_value(stock_data)
    total_value = asset_value + round(stock_holder.buying_power, 2)
    return render(request=request,
                  template_name="stonks/account.html",
                  context={"stockholder" : stock_holder,
                  "stockdata" : stock_data,
                  "assetvalue" : asset_value,
                  "totalvalue" : total_value,
                  "buyingpower" : round(stock_holder.buying_power, 2),
                  "stocksearchform" : stock_search_form})

def get_stock_data_with_delta(delta, interval, ticker):
    delta_day = timedelta(days = delta)
    tz = timezone("EST")
    today = datetime.now(tz)
    today = today - delta_day
    return si.get_data(ticker, start_date=f'{today.month}/{today.day}/{today.year}', interval=interval)

def get_portfoilio_value(data):
    asset_value = 0
    for stock in data:
        asset_value += round(data[stock] * si.get_live_price(stock), 2)
    return asset_value

def get_leaderboard():
    leaderboard = []
    for stockholder in StockHolder.objects.all():
        leaderboard.append([stockholder.username, round(stockholder.buying_power, 2)+get_portfoilio_value(json.loads(stockholder.stocks))])
    leaderboard = sorted(leaderboard, key=lambda x: x[1], reverse=True)
    for i, user in enumerate(leaderboard):
        user.append(i+1)
    return leaderboard
