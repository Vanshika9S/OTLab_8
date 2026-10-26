"""
test_validator.py
-----------------
Unit tests for the independent TimetableValidator using hand-crafted tiny instances.

Verifies:
1. Valid feasible schedule with exact back-to-back and slot metrics.
2. Detection of hard student clash violations.
3. Detection of room capacity overbooking.
4. Detection of 3+ exams in a single calendar day.
5. Incomplete course assignment detection.
"""

import pytest
from track_E_case_study.code.validator import TimetableValidator


@pytest.fixture
def tiny_instance():
    """
    Hand-crafted tiny problem instance:
    - 2 students:
        * Student 0 enrolled in Courses 0, 1
        * Student 1 enrolled in Courses 1, 2
    - 3 courses:
        * Course 0: 1 student (Student 0)
        * Course 1: 2 students (Students 0, 1)
        * Course 2: 1 student (Student 1)
    - 4 slots: 2 days x 2 slots/day (Day 0: slots 0, 1; Day 1: slots 2, 3)
    - Seating capacity: 5 seats per slot
    """
    return {
        "metadata": {
            "name": "tiny_handcrafted",
            "num_students": 2,
            "num_courses": 3,
            "num_slots": 4,
            "slots_per_day": 2,
            "num_days": 2,
            "total_room_capacity_per_slot": 5,
        },
        "course_enrollment_counts": {0: 1, 1: 2, 2: 1},
        "student_enrollments": {
            0: [0, 1],
            1: [1, 2],
        },
        "conflicts": {
            "0,1": 1,
            "1,2": 1,
        },
    }


def test_feasible_schedule_and_exact_metrics(tiny_instance):
    """
    Schedule:
      Course 0 -> Slot 0 (Day 0, Period 0)
      Course 1 -> Slot 2 (Day 1, Period 0)
      Course 2 -> Slot 3 (Day 1, Period 1)

    Analysis:
      - Slot 0: Course 0 (Student 0) -> 1 attendee <= 5
      - Slot 2: Course 1 (Students 0, 1) -> 2 attendees <= 5
      - Slot 3: Course 2 (Student 1) -> 1 attendee <= 5
      - No student is in two exams in the same slot -> 0 clashes
      - Back-to-back check:
          Student 0: slots [0, 2] -> slot 0 is Day 0, slot 2 is Day 1 -> NOT same day.
          Student 1: slots [2, 3] -> slot 2 & 3 are adjacent on Day 1 -> EXACTLY 1 b2b penalty.
      - Daily overload:
          Student 0: Day 0: 1 exam, Day 1: 1 exam.
          Student 1: Day 1: 2 exams. (No student has >= 3 in a day).
      - Slots used: 3 (slots 0, 2, 3).
      - Total penalty: 10 * 1 + 50 * 0 + 5 * 3 = 25.0
    """
    validator = TimetableValidator(tiny_instance, alpha_b2b=10.0, alpha_3plus=50.0, alpha_slots=5.0)
    schedule = {0: 0, 1: 2, 2: 3}

    result = validator.evaluate_schedule(schedule)

    assert result["is_feasible"] is True
    assert result["all_assigned"] is True
    assert result["student_clashes"] == 0
    assert result["capacity_violations"] == 0
    assert result["back_to_back_count"] == 1
    assert result["three_plus_day_count"] == 0
    assert result["slots_used"] == 3
    assert result["total_penalty"] == 25.0


def test_hard_student_clash_detection(tiny_instance):
    """
    Schedule with intentional conflict:
      Course 0 -> Slot 0
      Course 1 -> Slot 0  <-- Student 0 is in BOTH Course 0 and Course 1!
      Course 2 -> Slot 2
    """
    validator = TimetableValidator(tiny_instance)
    schedule = {0: 0, 1: 0, 2: 2}

    result = validator.evaluate_schedule(schedule)

    assert result["is_feasible"] is False
    assert result["student_clashes"] == 1


def test_capacity_violation_detection(tiny_instance):
    """
    Restrict capacity to 1 seat.
    Course 1 has 2 students, so scheduling Course 1 into any slot must violate capacity.
    """
    tiny_instance["metadata"]["total_room_capacity_per_slot"] = 1
    validator = TimetableValidator(tiny_instance)
    schedule = {0: 0, 1: 2, 2: 3}

    result = validator.evaluate_schedule(schedule)

    assert result["is_feasible"] is False
    assert result["capacity_violations"] >= 1
    assert result["excess_seats_total"] >= 1


def test_three_plus_per_day_detection():
    """
    Instance with 3 slots on Day 0 and 1 student enrolled in 3 courses.
    All scheduled on Day 0 -> must register 3+ penalty.
    """
    instance = {
        "metadata": {
            "name": "three_plus_test",
            "num_students": 1,
            "num_courses": 3,
            "num_slots": 3,
            "slots_per_day": 3,
            "num_days": 1,
            "total_room_capacity_per_slot": 100,
        },
        "course_enrollment_counts": {0: 1, 1: 1, 2: 1},
        "student_enrollments": {0: [0, 1, 2]},
        "conflicts": {"0,1": 1, "0,2": 1, "1,2": 1},
    }
    validator = TimetableValidator(instance, alpha_b2b=10.0, alpha_3plus=50.0, alpha_slots=5.0)
    # Schedule across slots 0, 1, 2 (all on Day 0)
    schedule = {0: 0, 1: 1, 2: 2}

    result = validator.evaluate_schedule(schedule)

    assert result["student_clashes"] == 0
    assert result["three_plus_day_count"] == 1  # 3 exams - 2 allowed = 1 excess
    assert result["back_to_back_count"] == 2   # (0, 1) and (1, 2)
    assert result["slots_used"] == 3


def test_incomplete_assignment_detection(tiny_instance):
    """
    Schedule missing Course 2.
    """
    validator = TimetableValidator(tiny_instance)
    incomplete_schedule = {0: 0, 1: 1}  # Course 2 missing

    result = validator.evaluate_schedule(incomplete_schedule)

    assert result["all_assigned"] is False
    assert result["missing_courses_count"] == 1
    assert result["is_feasible"] is False
