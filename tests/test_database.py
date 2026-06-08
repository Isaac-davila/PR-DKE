from database import is_admin
from unittest.mock import patch


@patch("database.has_role")
def test_is_admin(mock_has_role):
    mock_has_role.return_value = True

    result = is_admin("123")

    assert result is True
    mock_has_role.assert_called_once_with("123", ["admin"])