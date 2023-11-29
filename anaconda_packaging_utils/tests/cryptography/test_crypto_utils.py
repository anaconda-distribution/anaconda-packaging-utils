"""
File:           test_crypto_utils.py
Description:    Tests cryptography utilities library
"""
import anaconda_packaging_utils.cryptography.utils as crypto_utils


def test_is_valid_hex() -> None:
    """
    Tests `is_valid_hex()` function
    """
    # Valid strings of various lengths pass
    assert crypto_utils.is_valid_hex("044af71389ac2ad3d3ece24d0baf4c07")
    assert crypto_utils.is_valid_hex("044AF71389AC2AD3D3ECE24D0BAF4C07")
    assert crypto_utils.is_valid_hex("8dbd20507a8edbc05bd0cbc92ee4d5aba718415f4d1be289fa598cc2077b6243")
    assert crypto_utils.is_valid_hex("42")
    assert crypto_utils.is_valid_hex("0042")
    # Invalid strings fail
    assert not crypto_utils.is_valid_hex("044af71389ac2aq3d3ece24d0baf4c07")
    assert not crypto_utils.is_valid_hex("foobar")
    assert not crypto_utils.is_valid_hex("00:42")


def test_is_valid_md5() -> None:
    """
    Tests `is_valid_md5()` function
    """
    # Valid strings
    assert crypto_utils.is_valid_md5("044af71389ac2ad3d3ece24d0baf4c07")
    assert crypto_utils.is_valid_md5("044AF71389AC2AD3D3ECE24D0BAF4C07")
    # Invalid strings
    assert not crypto_utils.is_valid_md5("044af71389ac2aq3d3ece24d0baf4c07")
    assert not crypto_utils.is_valid_md5("044af71389ac2ad3d3ece24d0baf4c07a")
    assert not crypto_utils.is_valid_md5("044af71389ac2add3ece24d0baf4c07")


def test_is_valid_sha256() -> None:
    """
    Tests `is_valid_sha256()` function
    """
    # Valid strings
    assert crypto_utils.is_valid_sha256("8dbd20507a8edbc05bd0cbc92ee4d5aba718415f4d1be289fa598cc2077b6243")
    assert crypto_utils.is_valid_sha256("8DBD20507A8EDBC05BD0CBC92EE4D5ABA718415F4D1BE289FA598CC2077B6243")
    # Invalid strings
    assert not crypto_utils.is_valid_sha256("8dbd20507a8edbc05bd0cbc92ee4d5aba7184l5f4d1be289fa598cc2077b6243")
    assert not crypto_utils.is_valid_sha256("8dbd20507a8edbc05bd0cbc92ee4d5aba718415f4d1be289fa598cc2077b6243f")
    assert not crypto_utils.is_valid_sha256("8dbd20507a8edbc05bd0cbc92ee4d5aba718415f4d1be289fa598cc2077b624")


def test_is_valid_sha1() -> None:
    """
    Tests `is_valid_sha1()` function
    """
    # Valid strings
    assert crypto_utils.is_valid_sha1("5885a3b911f95660068923a12112b095e658bd84")
    assert crypto_utils.is_valid_sha1("5885A3B911F95660068923A12112B095E658BD84")
    # Invalid strings
    assert not crypto_utils.is_valid_sha1("5885a3b911f95660068923a12112b095e658bd8")
    assert not crypto_utils.is_valid_sha1("5885a3b911f95660068923a12112b095e658bd84f")
    assert not crypto_utils.is_valid_sha1("5885a3b911f95660068923a12112b095g658bd84")


def test_cast_hex_str_to_int() -> None:
    """
    Tests `cast_hex_str_to_int` function
    """
    assert crypto_utils.cast_hex_str_to_int("42") == 66
    assert crypto_utils.cast_hex_str_to_int("a") == 10
    assert crypto_utils.cast_hex_str_to_int("044af71389ac2ad3d3ece24d0baf4c07") == 5706153253786014303167714186088107015
    assert (
        crypto_utils.cast_hex_str_to_int("8dbd20507a8edbc05bd0cbc92ee4d5aba718415f4d1be289fa598cc2077b6243")
        == 64110268771069374191257748999639774710236764556754189598445367147908461978179  # pylint: disable=line-too-long
    )
