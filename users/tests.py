from django.test import TestCase
from django.utils import timezone

from .models import *


# Create your tests here.
class BaseModelTest(TestCase):
    def setUp(self):
        self.teacher_role = Role.get_teacher()
        self.student_role = Role.get_student()

        self.teacher = User.objects.create(username="Teacher1", password="12345")
        self.teacher.role = self.teacher_role
        self.teacher.save()

        self.category = SubjectCategory.objects.create(name="Science")
        self.subject = Subject.objects.create(name="Maths", category=self.category)

        self.lesson_type = LessonType.objects.create(name="Online")

        self.student = User.objects.create_user(username="Student1", password="12345")
        self.student.role = self.student_role
        self.student.save()


class UserModelTest(BaseModelTest):

    def test_user_roles(self):
        self.assertTrue(self.teacher.is_teacher())
        self.assertFalse(self.teacher.is_student())
        self.assertTrue(self.student.is_student())


class LessonSlotModelTest(BaseModelTest):

    def test_valid_lesson_slot(self):
        slot = LessonSlot.objects.create(
            type=self.lesson_type,
            subject=self.subject,
            teacher=self.teacher,
            max_students=5,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
        )
        self.assertEqual(slot.teacher.username, "Teacher1")

    def test_invalid_lesson_slot_with_student(self):
        slot = LessonSlot(
            type=self.lesson_type,
            subject=self.subject,
            teacher=self.student,
            max_students=5,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
        )
        with self.assertRaises(ValidationError):
            slot.full_clean()

    def test_invalid_lesson_slot_with_time(self):
        slot = LessonSlot.objects.create(
            type=self.lesson_type,
            subject=self.subject,
            teacher=self.teacher,
            max_students=5,
            start_time=timezone.now(),
            end_time=timezone.now() - timezone.timedelta(hours=1),
        )

        with self.assertRaises(ValidationError):
            slot.full_clean()


class LessonRequestSlotModelTest(BaseModelTest):
    def setUp(self):
        super().setUp()
        self.slot = LessonSlot.objects.create(
            type=self.lesson_type,
            subject=self.subject,
            teacher=self.teacher,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            max_students=5,
        )

    def test_valid_lesson_request(self):
        req = LessonRequest.objects.create(
            slot=self.slot, student=self.student, status="pending"
        )
        self.assertEqual(req.status, "pending")
        self.assertEqual(req.slot, self.slot)

    def test_duplicate_lesson_request(self):
        LessonRequest.objects.create(slot=self.slot, student=self.student)

        with self.assertRaises(Exception):
            LessonRequest.objects.create(slot=self.slot, student=self.student)


class LessonModelTest(BaseModelTest):
    def setUp(self):
        super().setUp()
        self.slot = LessonSlot.objects.create(
            type=self.lesson_type,
            subject=self.subject,
            teacher=self.teacher,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            max_students=5,
        )

    def test_valid_lesson(self):
        les = Lesson.objects.create(
            slot=self.slot,
            teacher=self.teacher,
            student=self.student,
            confirmed_at=timezone.now(),
        )
        self.assertEqual(les.slot, self.slot)
        self.assertEqual(les.teacher.username, "Teacher1")


class ReviewModelTest(BaseModelTest):
    def setUp(self):
        super().setUp()
        self.slot = LessonSlot.objects.create(
            type=self.lesson_type,
            subject=self.subject,
            teacher=self.teacher,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            max_students=5,
        )

        self.les = Lesson.objects.create(
            slot=self.slot,
            teacher=self.teacher,
            student=self.student,
            confirmed_at=timezone.now(),
        )

    def test_valid_review(self):
        review = Review.objects.create(
            lesson=self.les,
            student=self.student,
            teacher=self.teacher,
            rating=5,
            comment="Good teacher",
        )
        self.assertEqual(review.lesson, self.les)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.teacher, self.teacher)

    def test_invalid_rating_review(self):
        review = Review(
            lesson=self.les,
            student=self.student,
            teacher=self.teacher,
            rating=10,
            comment="Good teacher",
        )

        with self.assertRaises(ValidationError):
            review.full_clean()


class NotificationModelTest(BaseModelTest):
    def test_create_notification(self):
        notif = Notification.objects.create(
            user=self.teacher, message="You have a new lesson request"
        )
        self.assertEqual(notif.user, self.teacher)
        self.assertFalse(notif.is_read)
