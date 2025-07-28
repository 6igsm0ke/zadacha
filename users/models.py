from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError


# Create your models here.
class DefaultTypeClass(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True  # что бы не создавать таблицу в бд


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Role(models.Model):
    name = models.CharField(max_length=256)
    code = models.CharField(max_length=256, null=True, blank=True, unique=True)

    @classmethod
    def get_student(cls):
        return cls.objects.get_or_create(name="Student", code="STD")[0]

    @classmethod
    def get_teacher(cls):
        return cls.objects.get_or_create(name="Teacher", code="TCR")[0]

    def __str__(self):
        return self.name


class User(AbstractUser, BaseModel):
    bio = models.TextField(null=True, blank=True)

    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    def set_role(self, role_code):
        role = Role.objects.get(code=role_code)
        self.role = role
        self.save()

    def has_role(self, role_code):
        return self.role and self.role.code == role_code

    def is_student(self):
        return self.has_role("STD")

    def is_teacher(self):
        return self.has_role("TCR")


class LessonType(DefaultTypeClass):
    # offline or online or maybe hybrid
    def __str__(self):
        return self.name


class SubjectCategory(DefaultTypeClass):
    # Science, Humanitaries and etc.
    def __str__(self):
        return self.name


class Subject(DefaultTypeClass):
    category = models.ForeignKey(SubjectCategory, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class LessonSlot(BaseModel):
    type = models.ForeignKey(LessonType, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="teacher")
    max_students = models.IntegerField(default=1)
    notes = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")

        if not self.teacher.is_teacher():
            raise ValidationError("Only teacher can create slots")

    def __str__(self):
        return f"{self.teacher.first_name} {self.teacher.last_name} | {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class LessonRequest(BaseModel):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    slot = models.ForeignKey(LessonSlot, on_delete=models.CASCADE, verbose_name="slot")
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="student")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        unique_together = [
            "slot",
            "student",
        ]  # что бы один ученик не делал много запросов

    def __str__(self):
        return f"{self.student.username} → {self.slot} [{self.status}]"


class Lesson(BaseModel):
    slot = models.OneToOneField(LessonSlot, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="given")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="taken")
    confirmed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lesson: {self.teacher.username} ↔ {self.student.username} | {self.slot.start_time.strftime('%Y-%   m-%d %H:%M')}"


class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)


class Review(BaseModel):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="written")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )  # рейтинг от 1 до 5
    comment = models.TextField(null=True, blank=True)
