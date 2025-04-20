from ortools.sat.python import cp_model
import random

def solve_timetable(data):
    sections = data["sections"]
    section_course_teacher = data["section_course_teacher"]
    course_sessions_per_week = data["course_sessions_per_week"]
    num_of_rooms = data["num_of_rooms"]

    # Days and slots
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    time_slots = [
        "8:30-9:30", "9:30-10:30", "11:00-12:00",
        "12:00-1:00", "2:00-3:00", "3:00-4:00"
    ]
    time_slot_details = [
        (8.5, 9.5), (9.5, 10.5), (11.0, 12.0),
        (12.0, 13.0), (14.0, 15.0), (15.0, 16.0)
    ]

    model = cp_model.CpModel()

    # Build int mappings
    section_course_to_int = {
        sec: {course: idx for idx, course in enumerate(section_course_teacher[sec].keys())}
        for sec in sections
    }
    section_int_to_course = {
        sec: {idx: course for course, idx in section_course_to_int[sec].items()}
        for sec in sections
    }

    assignment = {}
    for sec in sections:
        dom = list(section_course_to_int[sec].values())
        for d in days:
            for t in time_slots:
                var = model.NewIntVar(min(dom), max(dom), f"assign_{sec}_{d}_{t}")
                assignment[(sec, d, t)] = var

    # Apply session requirements
    total_required = sum(course_sessions_per_week.values())
    for sec in sections:
        for course, sessions in course_sessions_per_week.items():
            if course not in section_course_teacher[sec]:
                continue
            idx = section_course_to_int[sec][course]
            indicators = []
            for d in days:
                for t in time_slots:
                    indicator = model.NewBoolVar(f"{sec}_{course}_{d}_{t}_assigned")
                    model.Add(assignment[(sec, d, t)] == idx).OnlyEnforceIf(indicator)
                    model.Add(assignment[(sec, d, t)] != idx).OnlyEnforceIf(indicator.Not())
                    indicators.append(indicator)
            model.Add(sum(indicators) == sessions)

    # Total slots used (non-None)
    for sec in sections:
        none_idx = section_course_to_int[sec]["None"]
        indicators = []
        for d in days:
            for t in time_slots:
                indicator = model.NewBoolVar(f"{sec}_{d}_{t}_non_none")
                model.Add(assignment[(sec, d, t)] != none_idx).OnlyEnforceIf(indicator)
                model.Add(assignment[(sec, d, t)] == none_idx).OnlyEnforceIf(indicator.Not())
                indicators.append(indicator)
        model.Add(sum(indicators) == total_required)

    # Collect all teachers
    all_teachers = set()
    for sec_map in section_course_teacher.values():
        for teacher in sec_map.values():
            if teacher: all_teachers.add(teacher)

    all_teachers = list(all_teachers)

    # Prevent teacher conflict across sections
    for teacher in all_teachers:
        for d in days:
            for t in time_slots:
                indicators = []
                for sec in sections:
                    for course, tchr in section_course_teacher[sec].items():
                        if tchr == teacher:
                            idx = section_course_to_int[sec][course]
                            indicator = model.NewBoolVar(f"{teacher}_{sec}_{d}_{t}")
                            model.Add(assignment[(sec, d, t)] == idx).OnlyEnforceIf(indicator)
                            model.Add(assignment[(sec, d, t)] != idx).OnlyEnforceIf(indicator.Not())
                            indicators.append(indicator)
                if indicators:
                    model.Add(sum(indicators) <= 1)

    # Enforce 2-hour gap between classes for same teacher
    conflicting_pairs = []
    for i in range(len(time_slot_details)):
        for j in range(i + 1, len(time_slot_details)):
            if time_slot_details[j][0] < time_slot_details[i][1] + 2:
                conflicting_pairs.append((i, j))

    for teacher in all_teachers:
        for d in days:
            for (i, j) in conflicting_pairs:
                indicators = []
                for sec in sections:
                    for course, tchr in section_course_teacher[sec].items():
                        if tchr != teacher:
                            continue
                        idx = section_course_to_int[sec][course]
                        ind_i = model.NewBoolVar(f"{teacher}_{sec}_{d}_{time_slots[i]}")
                        ind_j = model.NewBoolVar(f"{teacher}_{sec}_{d}_{time_slots[j]}")
                        model.Add(assignment[(sec, d, time_slots[i])] == idx).OnlyEnforceIf(ind_i)
                        model.Add(assignment[(sec, d, time_slots[i])] != idx).OnlyEnforceIf(ind_i.Not())
                        model.Add(assignment[(sec, d, time_slots[j])] == idx).OnlyEnforceIf(ind_j)
                        model.Add(assignment[(sec, d, time_slots[j])] != idx).OnlyEnforceIf(ind_j.Not())
                        indicators.extend([ind_i, ind_j])
                if indicators:
                    model.Add(sum(indicators) <= 1)

    # Teacher teaches once per day per section
    for sec in sections:
        for d in days:
            for course, teacher in section_course_teacher[sec].items():
                if course == "None" or teacher is None:
                    continue
                idx = section_course_to_int[sec][course]
                indicators = []
                for t in time_slots:
                    indicator = model.NewBoolVar(f"{teacher}_{sec}_{d}_{t}_once")
                    model.Add(assignment[(sec, d, t)] == idx).OnlyEnforceIf(indicator)
                    model.Add(assignment[(sec, d, t)] != idx).OnlyEnforceIf(indicator.Not())
                    indicators.append(indicator)
                model.Add(sum(indicators) <= 1)

    # Classroom constraint
    for d in days:
        for t in time_slots:
            indicators = []
            for sec in sections:
                none_idx = section_course_to_int[sec]["None"]
                indicator = model.NewBoolVar(f"{sec}_{d}_{t}_room")
                model.Add(assignment[(sec, d, t)] != none_idx).OnlyEnforceIf(indicator)
                model.Add(assignment[(sec, d, t)] == none_idx).OnlyEnforceIf(indicator.Not())
                indicators.append(indicator)
            model.Add(sum(indicators) <= num_of_rooms)

    # Saturday cutoff: no classes after 1:00
    for sec in sections:
        for t in ["2:00-3:00", "3:00-4:00"]:
            none_idx = section_course_to_int[sec]["None"]
            model.Add(assignment[(sec, "Saturday", t)] == none_idx)

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.random_seed = random.randint(1, 100000)
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": "failed", "message": "No feasible timetable found."}

    result = {}
    for sec in sections:
        result[sec] = {}
        for d in days:
            result[sec][d] = {}
            for t in time_slots:
                idx = solver.Value(assignment[(sec, d, t)])
                course = section_int_to_course[sec][idx]
                teacher = section_course_teacher[sec].get(course, "")
                result[sec][d][t] = {
                    "course": course,
                    "teacher": teacher or ""
                }

    return {"status": "success", "timetable": result}
