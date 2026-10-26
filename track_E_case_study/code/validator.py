"""
validator.py
------------
Independent Feasibility and Objective Evaluation Engine for University Exam Timetabling.

This module is completely decoupled from any solver, heuristic, or optimizer.
It acts as the single source of truth for:
  1. Hard Constraint Verification (Feasibility):
     - Complete and unique course assignment.
     - Zero student exam clashes (no student with >= 2 exams in the same slot).
     - Venue seating capacity compliance per slot.
  2. Soft Constraint Metric & Objective Evaluation:
     - Back-to-back student exam count (same day, adjacent slots).
     - 3+ exams in a single day student overload count.
     - Total number of active time slots used.
     - Weighted objective penalty scalarization:
       Z = alpha_1 * Z_b2b + alpha_2 * Z_3plus + alpha_3 * Z_slots
"""

from typing import Dict, List, Any, Tuple


class TimetableValidator:
    """
    Independent validator for exam timetable schedules.
    """

    def __init__(
        self,
        instance: Dict[str, Any],
        alpha_b2b: float = 10.0,
        alpha_3plus: float = 50.0,
        alpha_slots: float = 5.0,
    ):
        """
        Initializes the validator with the problem instance parameters.
        """
        self.instance = instance
        self.meta = instance["metadata"]
        self.num_courses = self.meta["num_courses"]
        self.num_slots = self.meta["num_slots"]
        self.slots_per_day = self.meta["slots_per_day"]
        self.capacity_per_slot = self.meta["total_room_capacity_per_slot"]

        self.course_enrollments = instance["course_enrollment_counts"]
        self.student_enrollments = {
            int(k): v for k, v in instance["student_enrollments"].items()
        }

        # Weights for multi-objective penalty function
        self.alpha_b2b = alpha_b2b
        self.alpha_3plus = alpha_3plus
        self.alpha_slots = alpha_slots

    def get_day_of_slot(self, slot: int) -> int:
        """Returns the 0-indexed calendar day index for a given time slot."""
        return slot // self.slots_per_day

    def are_adjacent_same_day(self, slot1: int, slot2: int) -> bool:
        """Checks if two slots are consecutive within the exact same calendar day."""
        return (abs(slot1 - slot2) == 1) and (self.get_day_of_slot(slot1) == self.get_day_of_slot(slot2))

    def evaluate_schedule(self, schedule: Dict[int, int]) -> Dict[str, Any]:
        """
        Evaluates a complete or partial schedule.
        Schedule mapping: course_id -> slot_id (both integers).

        Returns:
        --------
        Dictionary containing comprehensive feasibility status and objective metrics.
        """
        # -------------------------------------------------------------
        # 1. Check Completeness of Assignment
        # -------------------------------------------------------------
        assigned_courses = set(schedule.keys())
        expected_courses = set(range(self.num_courses))
        missing_courses = list(expected_courses - assigned_courses)
        all_assigned = len(missing_courses) == 0

        # Slot-to-courses mapping
        slot_to_courses: Dict[int, List[int]] = {s: [] for s in range(self.num_slots)}
        invalid_slots = []
        for c, s in schedule.items():
            if 0 <= s < self.num_slots:
                slot_to_courses[s].append(c)
            else:
                invalid_slots.append((c, s))

        # -------------------------------------------------------------
        # 2. Hard Constraint: Student Clashes
        # -------------------------------------------------------------
        # For each student, check which slots their enrolled exams fall into
        student_clash_count = 0
        clash_details = []

        # Invert: for each student, slot -> list of courses
        student_slots: Dict[int, Dict[int, List[int]]] = {}
        for s_id, courses in self.student_enrollments.items():
            slots_for_student: Dict[int, List[int]] = {}
            for c in courses:
                if c in schedule:
                    slot = schedule[c]
                    slots_for_student.setdefault(slot, []).append(c)
            student_slots[s_id] = slots_for_student

            # Count clashes
            for slot, c_list in slots_for_student.items():
                if len(c_list) > 1:
                    # Student has >= 2 exams in slot
                    # Clashes = len(c_list) - 1 or combination pairs
                    excess = len(c_list) - 1
                    student_clash_count += excess
                    clash_details.append({
                        "student_id": s_id,
                        "slot": slot,
                        "courses": c_list,
                        "excess": excess
                    })

        # -------------------------------------------------------------
        # 3. Hard Constraint: Room Capacity Compliance
        # -------------------------------------------------------------
        capacity_violations = 0
        excess_seats_total = 0
        slot_attendees: Dict[int, int] = {}

        for slot, courses in slot_to_courses.items():
            total_students_in_slot = sum(
                self.course_enrollments.get(str(c), self.course_enrollments.get(c, 0))
                for c in courses
            )
            slot_attendees[slot] = total_students_in_slot
            if total_students_in_slot > self.capacity_per_slot:
                capacity_violations += 1
                excess_seats_total += (total_students_in_slot - self.capacity_per_slot)

        # Feasibility check
        is_feasible = (
            all_assigned
            and len(invalid_slots) == 0
            and student_clash_count == 0
            and capacity_violations == 0
        )

        # -------------------------------------------------------------
        # 4. Soft Objective: Back-to-Back Exams on Same Day
        # -------------------------------------------------------------
        back_to_back_count = 0
        for s_id, slots_dict in student_slots.items():
            occupied_slots = sorted([s for s in slots_dict.keys() if 0 <= s < self.num_slots])
            for i in range(len(occupied_slots) - 1):
                s1 = occupied_slots[i]
                s2 = occupied_slots[i + 1]
                if s2 == s1 + 1 and self.get_day_of_slot(s1) == self.get_day_of_slot(s2):
                    # Each pair of exams in adjacent slots on same day is a b2b penalty
                    # Multiplied by the product of courses in both slots
                    b2b_instances = len(slots_dict[s1]) * len(slots_dict[s2])
                    back_to_back_count += b2b_instances

        # -------------------------------------------------------------
        # 5. Soft Objective: 3+ Exams in a Single Calendar Day
        # -------------------------------------------------------------
        three_plus_day_count = 0
        for s_id, slots_dict in student_slots.items():
            # Tally exams by calendar day
            day_exam_counts: Dict[int, int] = {}
            for slot, c_list in slots_dict.items():
                day = self.get_day_of_slot(slot)
                day_exam_counts[day] = day_exam_counts.get(day, 0) + len(c_list)

            for day, count in day_exam_counts.items():
                if count >= 3:
                    three_plus_day_count += (count - 2)

        # -------------------------------------------------------------
        # 6. Soft Objective: Active Slots Utilized
        # -------------------------------------------------------------
        slots_used = sum(1 for courses in slot_to_courses.values() if len(courses) > 0)

        # -------------------------------------------------------------
        # 7. Total Objective Penalty
        # -------------------------------------------------------------
        total_penalty = (
            self.alpha_b2b * back_to_back_count
            + self.alpha_3plus * three_plus_day_count
            + self.alpha_slots * slots_used
        )

        return {
            "is_feasible": is_feasible,
            "all_assigned": all_assigned,
            "missing_courses_count": len(missing_courses),
            "invalid_slot_assignments": len(invalid_slots),
            "student_clashes": student_clash_count,
            "capacity_violations": capacity_violations,
            "excess_seats_total": excess_seats_total,
            "back_to_back_count": back_to_back_count,
            "three_plus_day_count": three_plus_day_count,
            "slots_used": slots_used,
            "slot_attendees": slot_attendees,
            "total_penalty": total_penalty,
        }
