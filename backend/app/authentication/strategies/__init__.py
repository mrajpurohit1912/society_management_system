"""
Authentication Strategies Sub-Package.
Exports all abstract and concrete strategies following the GoF Strategy Pattern.
"""

from app.authentication.strategies.base import (
    SignupStrategy,
    SigninStrategy,
)
from app.authentication.strategies.username_password import (
    UsernamePasswordStrategy,
    UsernameSigninStrategy,
)
from app.authentication.strategies.email_password import (
    EmailPasswordStrategy,
    EmailPasswordSigninStrategy,
)
from app.authentication.strategies.mobile_otp import (
    MobileOTPStrategy,
    MobileOTPSigninStrategy,
)
from app.authentication.strategies.google_oauth import (
    GoogleStrategy,
    GoogleSigninStrategy,
)
from app.authentication.strategies.admin_signup import (
    AdminSignupStrategy,
)
from app.authentication.security import PasswordHasher

# Backward-compatibility alias for tests and legacy callers
hash_password = PasswordHasher.hash_password

__all__ = [
    "SignupStrategy",
    "SigninStrategy",
    "UsernamePasswordStrategy",
    "UsernameSigninStrategy",
    "EmailPasswordStrategy",
    "EmailPasswordSigninStrategy",
    "MobileOTPStrategy",
    "MobileOTPSigninStrategy",
    "GoogleStrategy",
    "GoogleSigninStrategy",
    "AdminSignupStrategy",
    "hash_password",
]
