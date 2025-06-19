from django.db import models
from pprint import pprint

class BaseModel(models.Model):
    class Meta:
        abstract = True  # So it doesn't create a table

    @classmethod
    def all(cls):
        return cls.objects.all()

    @classmethod
    def last(cls):
        return cls.objects.last()

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.objects.get(*args, **kwargs)

    def __str__(self):
        # You can customize this as needed
        return f"{pprint(self.__dict__)}"
