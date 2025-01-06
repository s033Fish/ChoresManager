from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver

@receiver(social_account_added)
def social_account_added_handler(request, sociallogin, **kwargs):
    print("New social account linked:")
    print(f"User: {sociallogin.user}")
    print(f"Provider: {sociallogin.account.provider}")
    print(f"Extra Data: {sociallogin.account.extra_data}")
