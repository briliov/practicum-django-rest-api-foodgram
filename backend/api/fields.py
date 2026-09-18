"""Fields for API Foodgram."""

import base64

import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Custom field to decode images received in Base64 string format."""

    def to_internal_value(self, data):
        """Decode a Base64 encoded string into a Django ContentFile object."""
        if isinstance(data, str) and data.startswith('data:image'):
            cleaned_data = data.replace(' ', '')
            format, imgstr = cleaned_data.split(';base64,')
            ext = format.split('/')[-1]
            id = uuid.uuid4()
            data = ContentFile(base64.b64decode(imgstr), name=f'{id}.{ext}')
        return super().to_internal_value(data)
