from django.db import models
import json
# Create your models here.
class StockHolder(models.Model):
    username = models.TextField()
    stocks = models.TextField()
    buying_power = models.FloatField()

    def buy_stock(self, ticker, price, amount):
        ticker = ticker.upper()
        self.buying_power -= price*amount

        data = json.loads(self.stocks or '{}')
        if ticker in data:
            data[ticker] = data[ticker] + amount
        else:
            data[ticker] = amount

        self.stocks = json.dumps(data)
        self.save()
        print(self.stocks)

    def sell_stock(self, ticker, price, amount):
        ticker = ticker.upper()
        self.buying_power += price*amount

        data = json.loads(self.stocks or '{}')
        if ticker in data:
            data[ticker] = data[ticker] - amount
        else:
            raise Exception(f"Ticker {ticker} not owned by {self.username}")
            return

        self.stocks = json.dumps(data)
        self.save()

    def __str__(self):
        return self.username
