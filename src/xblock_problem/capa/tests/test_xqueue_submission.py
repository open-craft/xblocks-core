"""
Unit tests for the XQueueInterfaceSubmission class.
"""

import json
import logging
from unittest.mock import Mock, patch

import pytest
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.fields import ScopeIds

from xblock_problem.capa.xqueue_interface import make_xheader
from xblock_problem.capa.xqueue_submission import XQueueInterfaceSubmission


@pytest.fixture
def xqueue_service():
    """
    Fixture that returns an instance of XQueueInterfaceSubmission.
    """
    location = BlockUsageLocator(CourseLocator("test_org", "test_course", "test_run"), "problem", "ExampleProblem")
    block = Mock(scope_ids=ScopeIds("user1", "problem", location, location))
    block.usage_key = location
    block.context_key = location.course_key
    block.max_score = Mock(return_value=10)
    return XQueueInterfaceSubmission(block)


def test_get_submission_params(xqueue_service):  # pylint: disable=redefined-outer-name
    """
    Test extracting item data from an xqueue submission.
    """
    header = make_xheader(lms_key="default", queue_name="default")
    payload = json.dumps(
        {
            "student_info": json.dumps({"anonymous_student_id": "student_id"}),
            "student_response": "student_answer",
            "grader_payload": json.dumps({"grader": "test.py"}),
        }
    )

    student_item, student_answer, queue_name, grader_file_name, points_possible, grader_options = (
        xqueue_service.get_submission_params(header, payload)
    )

    assert student_item == {
        "item_id": "block-v1:test_org+test_course+test_run+type@problem+block@ExampleProblem",
        "item_type": "problem",
        "course_id": "course-v1:test_org+test_course+test_run",
        "student_id": "student_id",
    }
    assert student_answer == "student_answer"
    assert queue_name == "default"
    assert grader_file_name == "test.py"
    assert points_possible == 10
    assert grader_options == {"lang": "", "hide_output": False, "skip_grader": False}


@pytest.mark.django_db
@patch("submissions.api.create_external_grader_detail")
def test_send_to_submission(mock_create_external_grader_detail, xqueue_service):  # pylint: disable=redefined-outer-name
    """
    Test sending a submission to the grading system.
    """
    header = make_xheader(lms_key="default", queue_name="default")
    body = json.dumps(
        {
            "student_info": json.dumps({"anonymous_student_id": "student_id"}),
            "student_response": "student_answer",
            "grader_payload": json.dumps({"grader": "test.py"}),
        }
    )

    mock_response = {"submission": "mock_submission"}
    mock_create_external_grader_detail.return_value = mock_response

    result = xqueue_service.send_to_submission(header, body, queue_key="default")

    assert result == mock_response
    mock_create_external_grader_detail.assert_called_once_with(
        {
            "item_id": "block-v1:test_org+test_course+test_run+type@problem+block@ExampleProblem",
            "item_type": "problem",
            "course_id": "course-v1:test_org+test_course+test_run",
            "student_id": "student_id",
        },
        "student_answer",
        queue_name="default",
        queue_key="default",
        grader_file_name="test.py",
        points_possible=10,
        lang="",
        hide_output=False,
        skip_grader=False,
        files=None,
    )


@pytest.mark.parametrize(
    "grader_payload, expected_grader_file_name, expect_warning",
    [
        (json.dumps({"grader": "test.py"}), "test.py", False),
        (json.dumps({"grader": "test.py", "lang": "es", "hide_output": True}), "test.py", False),
        ({"grader": "test.py"}, "test.py", False),
        (json.dumps({"lang": "es"}), "", False),
        ("", "", True),
        (None, "", True),
        ("not json at all", "", True),
        (json.dumps(["test.py"]), "", True),
        (json.dumps("test.py"), "", True),
    ],
)
def test_get_submission_params_grader_payload_shapes(
    xqueue_service,  # pylint: disable=redefined-outer-name
    caplog,
    grader_payload,
    expected_grader_file_name,
    expect_warning,
):
    """
    Whatever a course author puts in <grader_payload>, we pull out "grader" if we
    can and don't fail the submission if we can't. When we can't, we log the
    problem's usage key so there's a trail when the grader fails.
    """
    header = json.dumps({"queue_name": "default"})
    payload = json.dumps(
        {
            "student_info": json.dumps({"anonymous_student_id": "student_id"}),
            "student_response": "student_answer",
            "grader_payload": grader_payload,
        }
    )

    with caplog.at_level(logging.WARNING, logger="xblock_problem.capa.xqueue_submission"):
        _, _, _, grader_file_name, _, _ = xqueue_service.get_submission_params(header, payload)

    assert grader_file_name == expected_grader_file_name
    warnings = [r.getMessage() for r in caplog.records if "isn't a JSON object" in r.getMessage()]
    if expect_warning:
        assert len(warnings) == 1
        assert str(xqueue_service.block.usage_key) in warnings[0]
    else:
        assert not warnings


def test_get_submission_params_without_grader_payload(xqueue_service):  # pylint: disable=redefined-outer-name
    """A body with no grader_payload at all still gives us submission params."""
    header = json.dumps({"queue_name": "default"})
    payload = json.dumps(
        {
            "student_info": json.dumps({"anonymous_student_id": "student_id"}),
            "student_response": "student_answer",
        }
    )

    _, student_answer, _, grader_file_name, _, grader_options = xqueue_service.get_submission_params(header, payload)

    assert student_answer == "student_answer"
    assert grader_file_name == ""
    assert grader_options == {"lang": "", "hide_output": False, "skip_grader": False}


@pytest.mark.parametrize(
    "grader_payload, expected_grader_options",
    [
        # Nothing set: xqueue-watcher's defaults.
        ({"grader": "test.py"}, {"lang": "", "hide_output": False, "skip_grader": False}),
        (
            {"grader": "test.py", "lang": "es", "hide_output": True, "skip_grader": True},
            {"lang": "es", "hide_output": True, "skip_grader": True},
        ),
        # xqueue-watcher only checks truthiness, so the string "false" counts as true.
        ({"hide_output": "false", "skip_grader": 1}, {"lang": "", "hide_output": True, "skip_grader": True}),
        ({"hide_output": 0, "skip_grader": None}, {"lang": "", "hide_output": False, "skip_grader": False}),
        # A lang that isn't a short string is dropped.
        ({"lang": 5}, {"lang": "", "hide_output": False, "skip_grader": False}),
        ({"lang": None}, {"lang": "", "hide_output": False, "skip_grader": False}),
        ({"lang": "x" * 33}, {"lang": "", "hide_output": False, "skip_grader": False}),
        ({"lang": "x" * 32}, {"lang": "x" * 32, "hide_output": False, "skip_grader": False}),
    ],
)
def test_get_submission_params_grader_options(
    xqueue_service,  # pylint: disable=redefined-outer-name
    grader_payload,
    expected_grader_options,
):
    """We pull lang, hide_output, and skip_grader out of grader_payload the way xqueue-watcher reads them."""
    header = json.dumps({"queue_name": "default"})
    payload = json.dumps(
        {
            "student_info": json.dumps({"anonymous_student_id": "student_id"}),
            "student_response": "student_answer",
            "grader_payload": json.dumps(grader_payload),
        }
    )

    *_, grader_options = xqueue_service.get_submission_params(header, payload)

    assert grader_options == expected_grader_options


@pytest.mark.django_db
@patch("submissions.api.create_external_grader_detail")
def test_send_to_submission_passes_grader_options(
    mock_create_external_grader_detail,
    xqueue_service,  # pylint: disable=redefined-outer-name
):
    """The lang, hide_output, and skip_grader options from grader_payload go to edx-submissions."""
    header = json.dumps({"queue_name": "default"})
    body = json.dumps(
        {
            "grader_payload": json.dumps(
                {"grader": "output/grader.py", "lang": "es", "hide_output": True, "skip_grader": True}
            ),
            "student_info": json.dumps({"anonymous_student_id": "student_id"}),
            "student_response": "student_answer",
        }
    )

    xqueue_service.send_to_submission(header, body, queue_key="default")

    kwargs = mock_create_external_grader_detail.call_args.kwargs
    assert kwargs["grader_file_name"] == "output/grader.py"
    assert kwargs["lang"] == "es"
    assert kwargs["hide_output"] is True
    assert kwargs["skip_grader"] is True


@pytest.mark.django_db
@patch("submissions.api.create_external_grader_detail")
def test_send_to_submission_non_json_grader_payload(
    mock_create_external_grader_detail,
    xqueue_service,  # pylint: disable=redefined-outer-name
):
    """
    A problem with no <grader_payload> (or one that isn't a JSON object) is still
    queued, with xqueue-watcher's default grader options.
    """
    header = json.dumps({"queue_name": "default"})
    body = json.dumps(
        {
            "grader_payload": "",
            "student_info": json.dumps({"anonymous_student_id": "student_id"}),
            "student_response": "student_answer",
        }
    )

    result = xqueue_service.send_to_submission(header, body, queue_key="default")

    assert result == mock_create_external_grader_detail.return_value
    kwargs = mock_create_external_grader_detail.call_args.kwargs
    assert kwargs["grader_file_name"] == ""
    assert (kwargs["lang"], kwargs["hide_output"], kwargs["skip_grader"]) == ("", False, False)


@pytest.mark.django_db
@patch("submissions.api.create_external_grader_detail")
def test_send_to_submission_with_missing_fields(mock_create_external_grader_detail, xqueue_service):  # pylint: disable=redefined-outer-name
    """
    Test send_to_submission with missing required fields.
    """
    header = make_xheader(lms_key="default", queue_name="default")
    body = json.dumps(
        {
            "student_info": json.dumps({"anonymous_student_id": "student_id"}),
            "grader_payload": json.dumps({"grader": "test.py"}),
        }
    )

    result = xqueue_service.send_to_submission(header, body, queue_key="default")

    assert "error" in result
    assert "Validation error" in result["error"]
    mock_create_external_grader_detail.assert_not_called()
