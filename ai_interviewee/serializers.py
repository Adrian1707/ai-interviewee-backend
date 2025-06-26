from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from .models import Document, UserProfile, Skill
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        UserProfile.objects.create(user=user)
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user and user.is_active:
            refresh = RefreshToken.for_user(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
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

class SkillNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('name',)


class UserProfileSerializer(serializers.ModelSerializer):
    years_of_experience = serializers.SerializerMethodField()
    skills = SkillNameSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'display_name', 'bio', 'years_of_experience', 'skills')

    def get_years_of_experience(self, obj):
        from datetime import date
        if obj.career_start_date:
            return date.today().year - obj.career_start_date.year
        return None
