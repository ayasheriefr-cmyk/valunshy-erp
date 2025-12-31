from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'الإعدادات الأساسية'

    def ready(self):
        import re
        from django.contrib.auth.models import User
        from django.contrib.auth import validators
        from django.utils.translation import gettext_lazy as _

        # 1. Global Monkey-patch: Update the validator classes themselves
        # This ensures that forms (like UserCreationForm) which create their own validator instances
        # will use the relaxed regex.
        relaxed_regex = r'^[\w.@+ -]+$'
        compiled_regex = re.compile(relaxed_regex)
        relaxed_message = _(
            'أدخل اسم مستخدم صحيح. هذا الحقل يمكن أن يحتوي على حروف، أرقام، والرموز @/./+/-/_ والمسافات فقط.'
        )

        validators.UnicodeUsernameValidator.regex = compiled_regex
        validators.UnicodeUsernameValidator.message = relaxed_message
        
        # Also handle ASCII validator just in case, though Unicode is default in Py3
        validators.ASCIIUsernameValidator.regex = compiled_regex
        validators.ASCIIUsernameValidator.message = relaxed_message

        # 2. Model Level: Ensure help text and direct model validation are also updated
        username_field = User._meta.get_field('username')
        username_field.help_text = _('مطلوب. 150 حرفاً أو أقل. الحروف والأرقام والرموز @/./+/-/_ والمسافات فقط.')
        
        # We also need to update existing instances on the model field
        for v in username_field.validators:
            if hasattr(v, 'regex') and (isinstance(v, validators.UnicodeUsernameValidator) or isinstance(v, validators.ASCIIUsernameValidator)):
                v.regex = compiled_regex
                v.message = relaxed_message
