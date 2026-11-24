"""Test the XQueue interface."""

import json
from unittest.mock import Mock, patch

import pytest
from submissions.errors import SubmissionInternalError, SubmissionRequestError

from xblock_problem.capa.errors import RuntimeErrorSubmission
from xblock_problem.capa.xqueue_interface import XQueueInterface, make_xheader


@pytest.mark.django_db
@patch("xblock_problem.capa.xqueue_submission.XQueueInterfaceSubmission.send_to_submission")
def test_send_to_queue(mock_send_to_submission):
    """send_to_queue hands the header, body and queue key to edx-submissions."""
    xqueue_interface = XQueueInterface(block=Mock())

    header = make_xheader(lms_key="default", queue_name="testqueue")
    body = json.dumps(
        {
            "student_info": json.dumps({"anonymous_student_id": "student_id"}),
            "student_response": "student_answer",
        }
    )

    mock_send_to_submission.return_value = {"submission": "mock_submission"}
    error, msg = xqueue_interface.send_to_queue(header, body)

    mock_send_to_submission.assert_called_once_with(header, body, "default", {})
    assert error == 0
    assert msg == ""


@pytest.mark.django_db
@patch("xblock_problem.capa.xqueue_submission.XQueueInterfaceSubmission.send_to_submission")
def test_send_to_queue_with_files(mock_send_to_submission):
    """Uploaded files are passed through keyed by file name."""
    xqueue_interface = XQueueInterface(block=Mock())
    header = make_xheader(lms_key="default", queue_name="testqueue")
    body = json.dumps({"student_info": json.dumps({"anonymous_student_id": "student_id"})})
    prog = Mock()
    prog.name = "prog1.py"

    mock_send_to_submission.return_value = {"submission": "mock_submission"}
    error, _ = xqueue_interface.send_to_queue(header, body, files_to_upload=[prog])

    mock_send_to_submission.assert_called_once_with(header, body, "default", {"prog1.py": prog})
    assert not error


@pytest.mark.django_db
@patch("xblock_problem.capa.xqueue_submission.XQueueInterfaceSubmission.send_to_submission")
def test_send_to_queue_reports_submission_service_error(mock_send_to_submission):
    """
    If edx-submissions can't create the submission, send_to_queue returns an error
    so the problem tells the learner, instead of reporting success.
    """
    xqueue_interface = XQueueInterface(block=Mock())
    header = make_xheader(lms_key="default", queue_name="testqueue")
    body = json.dumps({"student_info": json.dumps({"anonymous_student_id": "student_id"})})

    mock_send_to_submission.return_value = {"error": "Validation error: The field 'student_response' does not exist."}
    error, msg = xqueue_interface.send_to_queue(header, body)

    assert error == 1
    assert msg == "Validation error: The field 'student_response' does not exist."


@pytest.mark.django_db
@pytest.mark.parametrize(
    "exception, expected_msg",
    [
        (SubmissionInternalError("database is away <img src=x>"), "the grading queue is unavailable"),
        (RuntimeErrorSubmission("Database access not allowed"), "the grading queue is unavailable"),
        (
            SubmissionRequestError(field_errors={"answer": ["Maximum answer size exceeded."]}),
            "the submission was rejected",
        ),
    ],
)
@patch("xblock_problem.capa.xqueue_submission.XQueueInterfaceSubmission.send_to_submission")
def test_send_to_queue_reports_exceptions_as_errors(mock_send_to_submission, exception, expected_msg):
    """
    A failure inside edx-submissions comes back as an error code and a fixed message, the way
    a connection failure to the XQueue service used to, so the problem can tell the learner to
    try again instead of raising. The message is fixed because display.js shows it as HTML
    and the exception text can carry the learner's answer.
    """
    xqueue_interface = XQueueInterface(block=Mock())
    header = make_xheader(lms_key="default", queue_name="testqueue")
    body = json.dumps({"student_info": json.dumps({"anonymous_student_id": "student_id"})})

    mock_send_to_submission.side_effect = exception
    error, msg = xqueue_interface.send_to_queue(header, body)

    assert error == 1
    assert msg == expected_msg
