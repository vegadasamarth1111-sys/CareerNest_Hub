from .models import Profile


class EnsureUserProfileMiddleware:
    """
    Keep auth/profile data consistent so templates and role checks are reliable.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            default_role = "admin" if user.is_superuser else "student"
            full_name = user.get_full_name()

            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={
                    "role": default_role,
                    "email": user.email or "",
                    "full_name": full_name or "",
                },
            )

            update_fields = []

            if not profile.role:
                profile.role = default_role
                update_fields.append("role")

            if user.is_superuser and profile.role != "admin":
                profile.role = "admin"
                if "role" not in update_fields:
                    update_fields.append("role")

            if not profile.email and user.email:
                profile.email = user.email
                update_fields.append("email")

            if not profile.full_name and full_name:
                profile.full_name = full_name
                update_fields.append("full_name")

            if update_fields:
                profile.save(update_fields=update_fields)

        response = self.get_response(request)
        return response
