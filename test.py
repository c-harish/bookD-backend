import datetime

a = datetime.datetime.now()
print(a.date() == datetime.datetime.now().date())
print(type(a.date()))