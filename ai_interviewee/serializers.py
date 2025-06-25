from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from .models import Document, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['email'], validated_data['password'])
        UserProfile.objects.create(user=user)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")

class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'txt', 'doc', 'docx']
            )
        ]
    )
    
    class Meta:
        model = Document
        fields = ['title', 'document_type', 'file', 'is_public', 'tags']
        document_type = serializers.ChoiceField(
            choices=Document.DOCUMENT_TYPE_CHOICES  # Add this
        )
        extra_kwargs = {
            'title': {'required': False},
            'document_type': {'required': False},
            'is_public': {'required': False},
        }
        tags = serializers.JSONField(  # Explicitly declare as JSONField
            required=False,
            help_text='JSON array of tags'
        )

    def validate_file(self, value):
        # Additional file validation
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("File size cannot exceed 10MB")
        return value
    
    def create(self, validated_data):
        # Set the owner to the current user
        validated_data['owner'] = self.context['request'].user
        
        # Extract file metadata
        file = validated_data['file']
        validated_data['file_size'] = file.size
        validated_data['mime_type'] = file.content_type or ''
        
        return super().create(validated_data)


class DocumentSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'document_type', 'file_url', 'file_size', 
            'mime_type', 'processing_status', 'processing_error',
            'is_public', 'tags', 'owner_username', 'uploaded_at', 
            'processed_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'mime_type', 'processing_status', 
            'processing_error', 'owner_username', 'uploaded_at', 
            'processed_at', 'updated_at'
        ]
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
