from enea_client.utils.sanitizer import Sanitizer


def test_sanitizer_call() -> None:
    data = (
        '\u0000"=""2025-09-01 00:59"""\u0000;"0,507";"0";"0,507";"0"\n'
        'some line with "---" that should be removed\n'
        '\u0000"=""2025-09-01 01:59"""\u0000;"0,503";"0";"0,503";"0"\n'
        'another "---" line to remove\n'
        '\u0000"=""2025-09-01 02:59"""\u0000;"0,561";"0";"0,561";"0"\n'
        'normal line with numbers 12,34 and 56,78'
    )

    result = Sanitizer.call(data)

    expected = (
        '"2025-09-01 00:59";"0.507";"0";"0.507";"0"\n'
        '"2025-09-01 01:59";"0.503";"0";"0.503";"0"\n'
        '"2025-09-01 02:59";"0.561";"0";"0.561";"0"\n'
        'normal line with numbers 12.34 and 56.78'
    )

    assert result == expected
