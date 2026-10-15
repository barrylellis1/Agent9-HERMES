"""The No Action and Solution lines are drawn by one function, for real and demo decisions alike."""
from src.agents.new.a9_value_assurance_agent import projection_lines


def test_no_action_continues_the_slope_and_solution_reaches_the_midpoint_by_window_end():
    inaction, expected, horizon = projection_lines(100.0, -2.0, 90, 4.0, 8.0, lower_is_better=False)
    assert horizon == 12 and len(inaction) == 13 and inaction[3] == 94.0
    assert expected == [100.0, 102.0, 104.0, 106.0]


def test_for_a_cost_the_solution_line_points_down():
    _, expected, _ = projection_lines(50.0, 1.0, 60, 2.0, 4.0, lower_is_better=True)
    assert expected == [50.0, 48.5, 47.0]


def test_a_window_under_a_month_still_draws_one_month():
    _, expected, horizon = projection_lines(10.0, 0.0, 10, 1.0, 1.0, lower_is_better=False)
    assert expected == [10.0, 11.0] and horizon == 12
