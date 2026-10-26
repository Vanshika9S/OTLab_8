"""
toronto_parser.py
-----------------
Parser and documentation for the classic Carter et al. (1996) Toronto Examination Timetabling Benchmark suite.

Benchmark Provenance & Download Instructions:
---------------------------------------------
The Toronto Examination Timetabling benchmarks are the recognized standard in operations research.
Public instances include:
  - car-s-91 (Carleton University, 682 exams, 16,925 students)
  - ear-f-83 (Earl Haig Collegiate, 190 exams, 1,125 students)
  - hec-s-92 (HEC Montreal, 81 exams, 2,823 students)
  - kfu-s-93 (King Fahd University, 461 exams, 5,349 students)
  - lse-f-91 (London School of Economics, 381 exams, 2,726 students)
  - rye-s-93 (Ryerson University, 486 exams, 11,483 students)
  - sta-f-83 (St. Andrews University, 139 exams, 611 students)
  - tre-s-92 (Trent University, 261 exams, 4,360 students)
  - uta-s-92 (University of Toronto Arts & Sci, 622 exams, 21,267 students)
  - ute-s-92 (University of Toronto Engineering, 184 exams, 2,750 students)
  - yor-f-83 (York University, 181 exams, 9,411 students)

Where to Download:
  1. Primary Academic Archive (University of Nottingham):
     http://www.cs.nott.ac.uk/~pszrq/data.htm
  2. Public Open Source GitHub Mirror:
     https://github.com/chkwon/exam-timetabling-benchmark

Files Required per instance:
  - `<instance>.crs`: Course catalog containing '<course_id> <num_enrolled_students>' per line.
  - `<instance>.stu`: Student enrollments containing space-separated course IDs per student per line.
"""

import os
from typing import Dict, Any, List


def parse_toronto_instance(
    crs_filepath: str,
    stu_filepath: str,
    num_slots: int = 18,
    slots_per_day: int = 3,
    room_capacity_per_slot: int = 1000,
) -> Dict[str, Any]:
    """
    Parses Carter benchmark .crs and .stu files into the unified Track E instance structure.

    Parameters:
    -----------
    crs_filepath : Path to the .crs file.
    stu_filepath : Path to the .stu file.
    num_slots : Number of exam periods specified in standard benchmark literature.
    slots_per_day : Standard number of slots per calendar day (default 3).
    room_capacity_per_slot : Total capacity per slot (if unconstrained, set large).

    Returns:
    --------
    Dict containing instance metadata, courses, student enrollments, and conflict graph.
    """
    if not os.path.exists(crs_filepath):
        raise FileNotFoundError(f"Course file not found: {crs_filepath}")
    if not os.path.exists(stu_filepath):
        raise FileNotFoundError(f"Student file not found: {stu_filepath}")

    # 1. Parse .crs
    course_enrollment_counts: Dict[int, int] = {}
    with open(crs_filepath, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                cid = int(parts[0])
                count = int(parts[1])
                course_enrollment_counts[cid] = count

    # 2. Parse .stu
    student_enrollments: Dict[int, List[int]] = {}
    student_id = 0
    with open(stu_filepath, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                courses = [int(p) for p in parts]
                student_enrollments[student_id] = sorted(courses)
                student_id += 1

    num_students = len(student_enrollments)
    num_courses = len(course_enrollment_counts)

    # 3. Build conflict graph
    conflict_matrix: Dict[str, int] = {}
    for s_id, courses in student_enrollments.items():
        n = len(courses)
        for i in range(n):
            for j in range(i + 1, n):
                c1, c2 = min(courses[i], courses[j]), max(courses[i], courses[j])
                key = f"{c1},{c2}"
                conflict_matrix[key] = conflict_matrix.get(key, 0) + 1

    possible_edges = num_courses * (num_courses - 1) // 2
    actual_edges = len(conflict_matrix)
    graph_density = actual_edges / possible_edges if possible_edges > 0 else 0.0

    instance_name = os.path.splitext(os.path.basename(crs_filepath))[0]

    return {
        "metadata": {
            "name": f"toronto_{instance_name}",
            "source": "Carter et al. (1996) Benchmark Suite",
            "num_students": num_students,
            "num_courses": num_courses,
            "num_slots": num_slots,
            "slots_per_day": slots_per_day,
            "num_days": num_slots // slots_per_day,
            "total_room_capacity_per_slot": room_capacity_per_slot,
            "conflict_edges_count": actual_edges,
            "conflict_graph_density": round(graph_density, 4),
        },
        "course_enrollment_counts": course_enrollment_counts,
        "student_enrollments": student_enrollments,
        "conflicts": conflict_matrix,
    }
