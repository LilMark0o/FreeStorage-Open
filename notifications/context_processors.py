from upload.models import Notificacions


def notification_count(request):
    if request.user.is_authenticated:
        newNotifications = list(Notificacions.objects.filter(
            user=request.user, shown=False))
        return {'notification_count': len(newNotifications)}
    return {'notification_count': 0}
