from uv_audit.environment_handler import parse_pip_list_to_requirements


def test_parse_pip_list_to_requirements_typical_output():
    # arrange
    pip_list_output = (
        "Package    Version\n---------- -------\nclick      8.2.1\nrequests   2.32.3\n"
    )

    # act
    result = parse_pip_list_to_requirements(pip_list_output)

    # assert
    assert result == ["click==8.2.1", "requests==2.32.3"]


def test_parse_pip_list_to_requirements_empty_input():
    # act
    result = parse_pip_list_to_requirements("")

    # assert
    assert result == []


def test_parse_pip_list_to_requirements_skips_blank_and_short_lines():
    # arrange
    pip_list_output = (
        "Package    Version\n"
        "---------- -------\n"
        "\n"
        "click      8.2.1\n"
        "badline\n"
        "requests   2.32.3\n"
    )

    # act
    result = parse_pip_list_to_requirements(pip_list_output)

    # assert
    assert result == ["click==8.2.1", "requests==2.32.3"]
