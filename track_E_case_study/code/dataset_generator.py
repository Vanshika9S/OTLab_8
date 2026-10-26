"""
dataset_generator.py
--------------------
Generates realistic university exam timetabling instances with deterministic random seeds.

Key Concepts:
- Students enroll in 4 to 6 courses each.
- Courses are grouped into academic departments to induce realistic co-enrollment clusters
  (e.g., Computer Science, Electrical Eng, Mathematics, Humanities).
- Room capacities enforce physical venue limits per time slot.
- Generates both a primary reference instance (300 students) and a scaling benchmark suite
  (100, 300, 1000, 3000 students).
"""

import json
import os
import random
from typing import Dict, List, Any


def generate_exam_instance(
    num_students: int = 300,
    num_courses: int = 40,
    num_slots: int = 12,
    slots_per_day: int = 3,
    room_capacities: List[int] = None,
    courses_per_student_range: tuple = (4, 6),
    num_departments: int = 4,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Generates a single synthetic exam timetabling instance.

    Parameters:
    -----------
    num_students : Total number of enrolled students.
    num_courses : Total number of distinct examinations to schedule.
    num_slots : Total number of available time slots across the exam period.
    slots_per_day : Standard number of exam periods per day (e.g. 3 = Morning, Afternoon, Evening).
    room_capacities : List of room seating capacities. Total slot capacity = sum(room_capacities).
    courses_per_student_range : Min and max courses each student registers for.
    num_departments : Number of course clusters to generate realistic co-enrollment patterns.
    seed : Deterministic random seed for reproducibility.

    Returns:
    --------
    Dict containing instance metadata, courses, students, rooms, and conflict graph.
    """
    if room_capacities is None:
        # Default rooms: 3 exam halls with total slot capacity = 300
        room_capacities = [120, 100, 80]

    rng = random.Random(seed)

    # 1. Distribute courses into departments
    # Courses 0..9 -> Dept 0, 10..19 -> Dept 1, etc.
    courses_by_dept: Dict[int, List[int]] = {d: [] for d in range(num_departments)}
    for c in range(num_courses):
        dept = c % num_departments
        courses_by_dept[dept].append(c)

    # 2. Generate student enrollments
    # Each student picks a primary major (dept) and takes 3-4 major courses + 1-2 electives
    student_enrollments: Dict[int, List[int]] = {}
    course_enrollment_counts: Dict[int, int] = {c: 0 for c in range(num_courses)}

    for s_id in range(num_students):
        primary_dept = rng.randint(0, num_departments - 1)
        total_courses = rng.randint(courses_per_student_range[0], courses_per_student_range[1])

        # Major courses from primary department (at least 2, up to available in dept)
        n_major = min(rng.randint(3, 4), len(courses_by_dept[primary_dept]), total_courses)
        major_courses = rng.sample(courses_by_dept[primary_dept], n_major)

        # Electives from other departments
        other_courses = [
            c for d, c_list in courses_by_dept.items() if d != primary_dept for c in c_list
        ]
        n_electives = total_courses - n_major
        elective_courses = rng.sample(other_courses, min(n_electives, len(other_courses)))

        enrolled = sorted(list(set(major_courses + elective_courses)))
        student_enrollments[s_id] = enrolled

        for c in enrolled:
            course_enrollment_counts[c] += 1

    # 3. Construct conflict graph
    # Edge between course i and j if at least one student takes both; weight = count of shared students
    conflict_matrix: Dict[str, int] = {}
    conflict_count = 0
    for s_id, courses in student_enrollments.items():
        n = len(courses)
        for i in range(n):
            for j in range(i + 1, n):
                c1, c2 = min(courses[i], courses[j]), max(courses[i], courses[j])
                key = f"{c1},{c2}"
                conflict_matrix[key] = conflict_matrix.get(key, 0) + 1

    # Conflict graph density: num_edges / (num_courses * (num_courses - 1) / 2)
    possible_edges = num_courses * (num_courses - 1) // 2
    actual_edges = len(conflict_matrix)
    graph_density = actual_edges / possible_edges if possible_edges > 0 else 0.0

    instance = {
        "metadata": {
            "name": f"synthetic_{num_students}s_{num_courses}c_{num_slots}sl",
            "seed": seed,
            "num_students": num_students,
            "num_courses": num_courses,
            "num_slots": num_slots,
            "slots_per_day": slots_per_day,
            "num_days": num_slots // slots_per_day,
            "total_room_capacity_per_slot": sum(room_capacities),
            "room_capacities": room_capacities,
            "conflict_edges_count": actual_edges,
            "conflict_graph_density": round(graph_density, 4),
        },
        "course_enrollment_counts": course_enrollment_counts,
        "student_enrollments": student_enrollments,
        "conflicts": conflict_matrix,
    }
    return instance


def save_instance(instance: Dict[str, Any], filepath: str) -> None:
    """Saves instance dictionary to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(instance, f, indent=2)


def generate_benchmark_suite(output_dir: str = "track_E_case_study/data") -> None:
    """
    Generates the primary reference instance (300 students) and the scaling suite
    (100, 300, 1000, 3000 students) for Track E experiments.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Primary Reference Instance (300 students, 40 courses, 12 slots)
    primary = generate_exam_instance(
        num_students=300,
        num_courses=40,
        num_slots=12,
        slots_per_day=3,
        room_capacities=[120, 100, 80],  # 300 seats per slot
        seed=42,
    )
    save_instance(primary, os.path.join(output_dir, "synthetic_primary_300.json"))
    print(f"Generated primary instance: 300 students, 40 courses, {primary['metadata']['conflict_edges_count']} conflict edges (density {primary['metadata']['conflict_graph_density']})")

    # 2. Scaling Suite: 100, 300, 1000, 3000 students
    scaling_sizes = [100, 300, 1000, 3000]
    for n_stud in scaling_sizes:
        # Scale room capacity proportionally to accommodate cohort size
        seats_per_slot = max(100, int(n_stud * 1.0))
        r1 = int(seats_per_slot * 0.4)
        r2 = int(seats_per_slot * 0.35)
        r3 = seats_per_slot - r1 - r2
        scaled_inst = generate_exam_instance(
            num_students=n_stud,
            num_courses=40,
            num_slots=12,
            slots_per_day=3,
            room_capacities=[r1, r2, r3],
            seed=42 + n_stud,
        )
        filepath = os.path.join(output_dir, f"synthetic_scale_{n_stud}.json")
        save_instance(scaled_inst, filepath)
        print(f"Generated scaling instance: {n_stud} students -> saved to {filepath}")


if __name__ == "__main__":
    generate_benchmark_suite()
