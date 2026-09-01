"""
New tests to improve coverage of BcryptPasswordHasher._permit (lines 61-71).

Gap identified by pytest-cov: the PasswordHasherBusyError path triggered
when the semaphore times out was not covered by existing tests.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import pytest

from app.outbound.adapters.bcrypt_password_hasher import (
    BcryptPasswordHasher,
    HasherSemaphore,
    HasherThreadPoolExecutor,
)
from app.outbound.adapters.exceptions import PasswordHasherBusyError
from tests.unit.core.common.services.factories import create_raw_password


def _make_hasher(semaphore: HasherSemaphore) -> BcryptPasswordHasher:
    executor = HasherThreadPoolExecutor(ThreadPoolExecutor(max_workers=1))
    return BcryptPasswordHasher(
        pepper=b"Habanero",
        work_factor=4,  # low cost for speed in tests
        executor=executor,
        semaphore=semaphore,
        semaphore_wait_timeout_s=0.001,  # very short timeout
    )


@pytest.mark.asyncio
async def test_raises_password_hasher_busy_error_when_semaphore_is_exhausted() -> None:
    """Lines 66-67: PasswordHasherBusyError raised when semaphore times out.

    We pre-acquire the semaphore to simulate all slots being busy,
    then try to hash — the _permit context manager must raise the error.
    """
    semaphore = HasherSemaphore(asyncio.Semaphore(1))
    await semaphore.acquire()  # exhaust all slots

    sut = _make_hasher(semaphore)
    pwd = create_raw_password()

    with pytest.raises(PasswordHasherBusyError):
        await sut.hash(pwd)

    semaphore.release()  # cleanup


@pytest.mark.asyncio
async def test_semaphore_is_released_after_successful_hash() -> None:
    """Lines 68-71: verify semaphore is released in the finally block.

    After a successful hash, the semaphore must be available again
    (i.e. release() was called in the finally clause).
    """
    semaphore = HasherSemaphore(asyncio.Semaphore(1))
    executor = HasherThreadPoolExecutor(ThreadPoolExecutor(max_workers=1))

    sut = BcryptPasswordHasher(
        pepper=b"Habanero",
        work_factor=4,
        executor=executor,
        semaphore=semaphore,
        semaphore_wait_timeout_s=3,
    )
    pwd = create_raw_password()

    await sut.hash(pwd)

    # After hash, semaphore value should be back to 1 (released)
    assert semaphore._value == 1
