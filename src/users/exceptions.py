from fastapi import HTTPException, status


class ActionException:
    invalid_action = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action in token"
    )


class TokenException:
    token_expired_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action in token"
    )

    invalid_token = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")


class UserHTTPException:
    """Custom HTTP exceptions related to user operations."""

    email_already_registered = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User with this email already exists.",
    )
    user_not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found.",
    )
    user_already_confirmed = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User already confirmed.",
    )
    invalid_or_expired_token = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired token.",
    )
    server_error = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An error occurred while registering the user.",
    )

    password_reset_successful = {"detail": "Password successfully reset."}
    confirmation_email_sent = {"detail": "Confirmation email successfully sent."}
    password_reset_email_sent = {"detail": "Password reset email successfully sent."}
