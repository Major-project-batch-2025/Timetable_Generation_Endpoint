from ortools.sat.python import cp_model
import random
from tabulate import tabulate

def solve_timetable(data):
    # Extract data from input
    sections = data["sections"]
    section_course_teacher = data["section_course_teacher"]
    course_req = data["course_req"]
    num_of_classrooms = data["num_of_classrooms"]
    num_of_labrooms = data["num_of_labrooms"]
    all_lab_course_names = data["all_lab_course_names"]
    lab_course_sessions_needed = data["lab_course_sessions_needed"]
    
    # Days and time slots
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    time_slots = ["8:30-9:30", "9:30-10:30", "11:00-12:00", "12:00-1:00", "2:00-3:00", "3:00-4:00"]
    lab_pairs = [("8:30-9:30", "9:30-10:30"), ("11:00-12:00", "12:00-1:00"), ("2:00-3:00", "3:00-4:00")]

    # ----------------------------
    # Preprocessing
    # ----------------------------
    sec_teachers = {}
    for sec in sections:
        teachers = list(section_course_teacher[sec].values())
        sec_teachers[sec] = list(set(teachers + [None]))  # Unique teachers + None

    sec_t2i = {sec: {teacher: idx for idx, teacher in enumerate(sec_teachers[sec])} for sec in sections}
    sec_i2t = {sec: {idx: teacher for teacher, idx in sec_t2i[sec].items()} for sec in sections}

    # Identify lab courses taken by each section
    section_taken_lab_courses = {sec: [] for sec in sections}
    for sec in sections:
        for course_name in section_course_teacher[sec].keys():
            if course_name in all_lab_course_names:
                section_taken_lab_courses[sec].append(course_name)

    # Store theory session activation vars for later use in teacher conflict constraint
    theory_session_active_vars = {}  # (sec, course_name, day, slot) -> BoolVar

    # ----------------------------
    # Model Setup
    # ----------------------------
    model = cp_model.CpModel()
    assign = {}  # (sec, day, slot) -> teacher_idx
    for sec in sections:
        domain = list(sec_t2i[sec].values())
        for d in days:
            for slot in time_slots:
                assign[(sec, d, slot)] = model.NewIntVar(
                    min(domain), max(domain), f"assign_{sec}_{d}_{slot.replace(':','').replace('-','')}"
                )

    # ----------------------------
    # Non-lab Course Constraints
    # ----------------------------
    for sec in sections:
        for course_name, req_sessions in course_req.items():
            teacher = section_course_teacher[sec].get(course_name)
            if not teacher:  # This section does not take this theory course
                continue
            teacher_idx = sec_t2i[sec][teacher]
            occurrence_vars_for_course = []
            for d in days:
                for slot in time_slots:
                    slot_clean = slot.replace(':', '').replace('-', '')
                    # b is true if this theory course is taught by its teacher in this slot
                    b = model.NewBoolVar(f"occ_theory_{sec}_{course_name.replace(' ','')}_{d}_{slot_clean}")
                    model.Add(assign[(sec, d, slot)] == teacher_idx).OnlyEnforceIf(b)
                    model.Add(assign[(sec, d, slot)] != teacher_idx).OnlyEnforceIf(b.Not())
                    occurrence_vars_for_course.append(b)
                    theory_session_active_vars[(sec, course_name, d, slot)] = b  # Store for later
            model.Add(sum(occurrence_vars_for_course) == req_sessions)

    # ----------------------------
    # Lab Course Constraints
    # ----------------------------
    lab_activation_vars = {}  # (sec, lab_c_name, day, s1, s2) -> BoolVar

    for sec in sections:
        for lab_c_name in section_taken_lab_courses[sec]:
            lab_teacher_name = section_course_teacher[sec][lab_c_name]
            lab_teacher_idx = sec_t2i[sec][lab_teacher_name]
            num_sessions_needed = lab_course_sessions_needed[lab_c_name]

            section_specific_lab_course_blocks = []
            for d in days:
                for s1, s2 in lab_pairs:
                    s1_clean = s1.replace(':', '').replace('-', '')
                    s2_clean = s2.replace(':', '').replace('-', '')
                    lab_c_clean = lab_c_name.replace(' ', '')

                    # b_lab_active is true if this specific lab course is scheduled for this section in this block
                    b_lab_active = model.NewBoolVar(f"lab_active_{sec}_{lab_c_clean}_{d}_{s1_clean}_{s2_clean}")
                    lab_activation_vars[(sec, lab_c_name, d, s1, s2)] = b_lab_active

                    # If b_lab_active, assign lab teacher to both slots
                    model.Add(assign[(sec, d, s1)] == lab_teacher_idx).OnlyEnforceIf(b_lab_active)
                    model.Add(assign[(sec, d, s2)] == lab_teacher_idx).OnlyEnforceIf(b_lab_active)

                    # If not b_lab_active, at least one slot is not the lab teacher (reification for Not)
                    ne1 = model.NewBoolVar(f"ne1_{sec}_{lab_c_clean}_{d}_{s1_clean}_{s2_clean}")
                    model.Add(assign[(sec, d, s1)] != lab_teacher_idx).OnlyEnforceIf(ne1)
                    model.Add(assign[(sec, d, s1)] == lab_teacher_idx).OnlyEnforceIf(ne1.Not())

                    ne2 = model.NewBoolVar(f"ne2_{sec}_{lab_c_clean}_{d}_{s1_clean}_{s2_clean}")
                    model.Add(assign[(sec, d, s2)] != lab_teacher_idx).OnlyEnforceIf(ne2)
                    model.Add(assign[(sec, d, s2)] == lab_teacher_idx).OnlyEnforceIf(ne2.Not())
                    model.AddBoolOr([ne1, ne2]).OnlyEnforceIf(b_lab_active.Not())

                    section_specific_lab_course_blocks.append(b_lab_active)

            # Ensure this specific lab course meets its weekly session requirement for this section
            model.Add(sum(section_specific_lab_course_blocks) == num_sessions_needed)

    # Lab Exclusivity (within section)
    for sec in sections:
        for lab_c_name in section_taken_lab_courses[sec]:
            lab_teacher_name = section_course_teacher[sec][lab_c_name]
            lab_teacher_idx = sec_t2i[sec][lab_teacher_name]
            lab_c_clean = lab_c_name.replace(' ', '')
            for d in days:
                for s1_lab, s2_lab in lab_pairs:
                    b_this_lab_active = lab_activation_vars[(sec, lab_c_name, d, s1_lab, s2_lab)]
                    for slot_other in time_slots:
                        if slot_other not in (s1_lab, s2_lab):
                            model.Add(assign[(sec, d, slot_other)] != lab_teacher_idx).OnlyEnforceIf(b_this_lab_active)

    # Lab-room Capacity
    for d in days:
        for s1, s2 in lab_pairs:
            simultaneous_labs_in_slot_pair = []
            for sec_check in sections:
                for lab_c_name_check in section_taken_lab_courses[sec_check]:
                    simultaneous_labs_in_slot_pair.append(lab_activation_vars[(sec_check, lab_c_name_check, d, s1, s2)])
            if simultaneous_labs_in_slot_pair:
                model.Add(sum(simultaneous_labs_in_slot_pair) <= num_of_labrooms)

    # Cross-section lab-day exclusivity for teachers
    for lab_sec in sections:
        for lab_c_name in section_taken_lab_courses[lab_sec]:
            lab_teacher_name = section_course_teacher[lab_sec][lab_c_name]
            if not lab_teacher_name:
                continue

            for lab_day in days:
                for s1_lab, s2_lab in lab_pairs:
                    b_is_this_lab_active = lab_activation_vars[(lab_sec, lab_c_name, lab_day, s1_lab, s2_lab)]
                    for other_sec in sections:
                        if other_sec == lab_sec:
                            continue
                        if lab_teacher_name in sec_t2i[other_sec]:
                            teacher_idx_in_other_sec = sec_t2i[other_sec][lab_teacher_name]
                            for slot_in_other_sec in time_slots:
                                model.Add(assign[(other_sec, lab_day, slot_in_other_sec)] != teacher_idx_in_other_sec).OnlyEnforceIf(b_is_this_lab_active)

    # ----------------------------
    # Total Non-Empty Slots per Section
    # ----------------------------
    for sec in sections:
        none_idx_for_sec = sec_t2i[sec][None]
        total_theory_slots = sum(course_req.get(c, 0) for c in section_course_teacher[sec].keys() if c in course_req)
        total_lab_slots_for_section = 0
        for lab_c_name in section_taken_lab_courses[sec]:
            total_lab_slots_for_section += lab_course_sessions_needed[lab_c_name] * 2
        current_total_required_slots = total_theory_slots + total_lab_slots_for_section

        actually_used_slots_in_sec = []
        for d in days:
            for slot in time_slots:
                slot_clean = slot.replace(':', '').replace('-', '')
                b_slot_used = model.NewBoolVar(f"used_{sec}_{d}_{slot_clean}")
                model.Add(assign[(sec, d, slot)] != none_idx_for_sec).OnlyEnforceIf(b_slot_used)
                model.Add(assign[(sec, d, slot)] == none_idx_for_sec).OnlyEnforceIf(b_slot_used.Not())
                actually_used_slots_in_sec.append(b_slot_used)
        model.Add(sum(actually_used_slots_in_sec) == current_total_required_slots)

    # ----------------------------
    # Teacher Conflict Constraints
    # ----------------------------
    all_teachers_globally = set()
    for sec_name_iter in sections:
        for t_name in section_course_teacher[sec_name_iter].values():
            all_teachers_globally.add(t_name)

    for teacher_name in all_teachers_globally:
        if teacher_name is None:
            continue
        clean_teacher_name_conflict = teacher_name.replace(' ', '_').replace('.', '')
        for d in days:
            # Constraint 1: No teacher double-booking in same slot across sections
            for slot in time_slots:
                slot_clean = slot.replace(':', '').replace('-', '')
                teacher_assignments_in_slot = []
                for sec in sections:
                    if teacher_name in sec_t2i[sec]:
                        teacher_idx_for_sec = sec_t2i[sec][teacher_name]
                        b_teacher_in_sec_slot = model.NewBoolVar(f"tb_{clean_teacher_name_conflict}_{sec}_{d}_{slot_clean}")
                        model.Add(assign[(sec, d, slot)] == teacher_idx_for_sec).OnlyEnforceIf(b_teacher_in_sec_slot)
                        model.Add(assign[(sec, d, slot)] != teacher_idx_for_sec).OnlyEnforceIf(b_teacher_in_sec_slot.Not())
                        teacher_assignments_in_slot.append(b_teacher_in_sec_slot)
                if teacher_assignments_in_slot:
                    model.Add(sum(teacher_assignments_in_slot) <= 1)

            # Constraint 2: A teacher teaches at most one non-lab class per day per section
            for sec in sections:
                is_teacher_conducting_lab_this_sec_day = model.NewBoolVar(f"teacher_lab_{clean_teacher_name_conflict}_{sec}_{d}")
                active_labs_by_teacher_for_sec_day = []
                for lab_c_name in section_taken_lab_courses[sec]:
                    if section_course_teacher[sec].get(lab_c_name) == teacher_name:
                        for s1_lab, s2_lab in lab_pairs:
                            active_labs_by_teacher_for_sec_day.append(lab_activation_vars[(sec, lab_c_name, d, s1_lab, s2_lab)])
                if active_labs_by_teacher_for_sec_day:
                    model.Add(sum(active_labs_by_teacher_for_sec_day) > 0).OnlyEnforceIf(is_teacher_conducting_lab_this_sec_day)
                    model.Add(sum(active_labs_by_teacher_for_sec_day) == 0).OnlyEnforceIf(is_teacher_conducting_lab_this_sec_day.Not())
                else:
                    model.Add(is_teacher_conducting_lab_this_sec_day == 0)

                daily_theory_sessions_by_teacher_sec = []
                if teacher_name in sec_t2i[sec]:
                    for course_name_theory in course_req.keys():
                        if section_course_teacher[sec].get(course_name_theory) == teacher_name:
                            for slot in time_slots:
                                if (sec, course_name_theory, d, slot) in theory_session_active_vars:
                                    daily_theory_sessions_by_teacher_sec.append(theory_session_active_vars[(sec, course_name_theory, d, slot)])
                    if daily_theory_sessions_by_teacher_sec:
                        model.Add(sum(daily_theory_sessions_by_teacher_sec) <= 1).OnlyEnforceIf(is_teacher_conducting_lab_this_sec_day.Not())

    # ----------------------------
    # Classroom Availability & Saturday Cutoff
    # ----------------------------
    for d in days:
        for slot in time_slots:
            slot_clean = slot.replace(':', '').replace('-', '')
            active_general_classes_in_slot = []
            for sec in sections:
                none_idx_for_sec = sec_t2i[sec][None]
                is_assigned_in_slot = model.NewBoolVar(f"assigned_{sec}_{d}_{slot_clean}")
                model.Add(assign[(sec, d, slot)] != none_idx_for_sec).OnlyEnforceIf(is_assigned_in_slot)
                model.Add(assign[(sec, d, slot)] == none_idx_for_sec).OnlyEnforceIf(is_assigned_in_slot.Not())

                is_part_of_active_lab_for_sec_slot = model.NewBoolVar(f"is_part_of_any_lab_{sec}_{d}_{slot_clean}")
                potential_active_labs_for_sec_slot = []
                for s1_lab, s2_lab in lab_pairs:
                    if slot == s1_lab or slot == s2_lab:
                        for lab_c_name in section_taken_lab_courses[sec]:
                            potential_active_labs_for_sec_slot.append(lab_activation_vars[(sec, lab_c_name, d, s1_lab, s2_lab)])
                if potential_active_labs_for_sec_slot:
                    model.Add(sum(potential_active_labs_for_sec_slot) > 0).OnlyEnforceIf(is_part_of_active_lab_for_sec_slot)
                    model.Add(sum(potential_active_labs_for_sec_slot) == 0).OnlyEnforceIf(is_part_of_active_lab_for_sec_slot.Not())
                else:
                    model.Add(is_part_of_active_lab_for_sec_slot == 0)

                uses_general_classroom = model.NewBoolVar(f"uses_gen_room_{sec}_{d}_{slot_clean}")
                model.AddImplication(uses_general_classroom, is_assigned_in_slot)
                model.AddImplication(uses_general_classroom, is_part_of_active_lab_for_sec_slot.Not())
                model.Add(uses_general_classroom == 1).OnlyEnforceIf([is_assigned_in_slot, is_part_of_active_lab_for_sec_slot.Not()])
                active_general_classes_in_slot.append(uses_general_classroom)

            if active_general_classes_in_slot:
                model.Add(sum(active_general_classes_in_slot) <= num_of_classrooms)

    for sec in sections:
        none_idx_for_sec = sec_t2i[sec][None]
        for slot_to_block in ("2:00-3:00", "3:00-4:00"):
            if slot_to_block in time_slots:
                model.Add(assign[(sec, "Saturday", slot_to_block)] == none_idx_for_sec)

    # ----------------------------
    # Compactness Objective
    # ----------------------------
    all_daily_sum_squared_terms = []
    num_slots_in_day = len(time_slots)
    possible_daily_idles = range(num_slots_in_day + 1)
    allowed_value_square_tuples = [(i, i * i) for i in possible_daily_idles]

    for sec in sections:
        none_idx_for_sec = sec_t2i[sec][None]
        for d in days:
            daily_assignment_vars = [assign[(sec, d, slot)] for slot in time_slots]
            daily_internal_idle_indicators_for_sd = []
            for j in range(num_slots_in_day):
                is_slot_j_free = model.NewBoolVar(f"isfree_{sec}_{d}_{j}")
                model.Add(daily_assignment_vars[j] == none_idx_for_sec).OnlyEnforceIf(is_slot_j_free)
                model.Add(daily_assignment_vars[j] != none_idx_for_sec).OnlyEnforceIf(is_slot_j_free.Not())

                has_class_before_j = model.NewBoolVar(f"hasclassbefore_{sec}_{d}_{j}")
                if j == 0:
                    model.Add(has_class_before_j == 0)
                else:
                    occupied_before = [model.NewBoolVar(f"occb_{sec}_{d}_{j}_{k}") for k in range(j)]
                    for k_idx in range(j):
                        model.Add(daily_assignment_vars[k_idx] != none_idx_for_sec).OnlyEnforceIf(occupied_before[k_idx])
                        model.Add(daily_assignment_vars[k_idx] == none_idx_for_sec).OnlyEnforceIf(occupied_before[k_idx].Not())
                    model.Add(sum(occupied_before) > 0).OnlyEnforceIf(has_class_before_j)
                    model.Add(sum(occupied_before) == 0).OnlyEnforceIf(has_class_before_j.Not())

                has_class_after_j = model.NewBoolVar(f"hasclassafter_{sec}_{d}_{j}")
                if j == num_slots_in_day - 1:
                    model.Add(has_class_after_j == 0)
                else:
                    occupied_after = [model.NewBoolVar(f"occa_{sec}_{d}_{j}_{k}") for k in range(j + 1, num_slots_in_day)]
                    for k_idx, actual_slot_idx in enumerate(range(j + 1, num_slots_in_day)):
                        model.Add(daily_assignment_vars[actual_slot_idx] != none_idx_for_sec).OnlyEnforceIf(occupied_after[k_idx])
                        model.Add(daily_assignment_vars[actual_slot_idx] == none_idx_for_sec).OnlyEnforceIf(occupied_after[k_idx].Not())
                    model.Add(sum(occupied_after) > 0).OnlyEnforceIf(has_class_after_j)
                    model.Add(sum(occupied_after) == 0).OnlyEnforceIf(has_class_after_j.Not())

                slot_j_is_internal_idle = model.NewBoolVar(f"internalidle_{sec}_{d}_{j}")
                model.AddImplication(slot_j_is_internal_idle, is_slot_j_free)
                model.AddImplication(slot_j_is_internal_idle, has_class_before_j)
                model.AddImplication(slot_j_is_internal_idle, has_class_after_j)
                model.Add(slot_j_is_internal_idle == 1).OnlyEnforceIf([is_slot_j_free, has_class_before_j, has_class_after_j])
                daily_internal_idle_indicators_for_sd.append(slot_j_is_internal_idle)

            daily_sum_var = model.NewIntVar(0, num_slots_in_day, f"daily_sum_idle_{sec}_{d}")
            model.Add(daily_sum_var == sum(daily_internal_idle_indicators_for_sd))
            daily_sum_sq_var = model.NewIntVar(0, num_slots_in_day * num_slots_in_day, f"daily_sum_sq_idle_{sec}_{d}")
            model.AddAllowedAssignments([daily_sum_var, daily_sum_sq_var], allowed_value_square_tuples)
            all_daily_sum_squared_terms.append(daily_sum_sq_var)

    max_total_penalty = len(sections) * len(days) * (num_slots_in_day**2)
    total_penalty_objective = model.NewIntVar(0, max_total_penalty if max_total_penalty > 0 else 1, "total_penalty_objective")
    if all_daily_sum_squared_terms:
        model.Add(total_penalty_objective == sum(all_daily_sum_squared_terms))
    else:
        model.Add(total_penalty_objective == 0)
    model.Minimize(total_penalty_objective)

    # ----------------------------
    # Solve
    # ----------------------------
    solver = cp_model.CpSolver()
    solver.parameters.random_seed = random.randint(1, 10000000)
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": "failed", "message": "No feasible timetable found."}

    # Prepare the result in the expected format
    result = {}
    for sec in sections:
        result[sec] = {}
        for d in days:
            result[sec][d] = {}
            for slot in time_slots:
                assigned_teacher_idx = solver.Value(assign[(sec, d, slot)])
                teacher_name_assigned = sec_i2t[sec][assigned_teacher_idx]

                if teacher_name_assigned is None:
                    result[sec][d][slot] = {"course": "None", "teacher": ""}
                else:
                    course_name_display = "None"
                    # Check if it's an active lab session
                    is_active_lab_session_slot = False
                    for lab_c_name_iter in section_taken_lab_courses[sec]:
                        if section_course_teacher[sec].get(lab_c_name_iter) == teacher_name_assigned:
                            for s1_lab_disp, s2_lab_disp in lab_pairs:
                                if (slot == s1_lab_disp or slot == s2_lab_disp) and solver.Value(lab_activation_vars.get((sec, lab_c_name_iter, d, s1_lab_disp, s2_lab_disp), 0)):
                                    course_name_display = lab_c_name_iter
                                    is_active_lab_session_slot = True
                                    break
                            if is_active_lab_session_slot:
                                break

                    if not is_active_lab_session_slot:
                        for c_name, t_name_map in section_course_teacher[sec].items():
                            if t_name_map == teacher_name_assigned and c_name not in all_lab_course_names:
                                course_name_display = c_name
                                break
                        if course_name_display == "None":
                            for c_name, t_name_map in section_course_teacher[sec].items():
                                if t_name_map == teacher_name_assigned:
                                    course_name_display = c_name
                                    break

                    result[sec][d][slot] = {
                        "course": course_name_display,
                        "teacher": teacher_name_assigned or ""
                    }

    return {"status": "success", "timetable": result}