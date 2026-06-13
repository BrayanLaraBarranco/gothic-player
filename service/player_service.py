"""
Servicio de reproducción en segundo plano para Android
Permite que el audio continúe cuando la app está minimizada
"""
import os
import sys

# Necesario para servicios Android
if 'ANDROID_ARGUMENT' in os.environ:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kivy.utils import platform

if platform == 'android':
    try:
        from android import mActivity  # type: ignore
        from jnius import autoclass  # type: ignore

        # Configurar notificación de servicio en primer plano
        PythonService = autoclass('org.kivy.android.PythonService')
        PythonService.mService.setAutoRestartService(True)

        # Notificación persistente
        Context        = autoclass('android.content.Context')
        Intent         = autoclass('android.content.Intent')
        NotifManager   = autoclass('android.app.NotificationManager')
        NotifCompat    = autoclass('androidx.core.app.NotificationCompat')
        NotifChannel   = autoclass('android.app.NotificationChannel')

        CHANNEL_ID = 'gothic_player_channel'

        def create_notification_channel(service):
            channel = NotifChannel(
                CHANNEL_ID,
                'Music Player Pro Gothic',
                NotifManager.IMPORTANCE_LOW,
            )
            channel.setDescription('Reproducción de audio en segundo plano')
            nm = service.getSystemService(Context.NOTIFICATION_SERVICE)
            nm.createNotificationChannel(channel)

        def show_foreground_notification(service, title='Music Player Pro', text='Reproduciendo...'):
            create_notification_channel(service)
            builder = NotifCompat.Builder(service, CHANNEL_ID)
            builder.setContentTitle(title)
            builder.setContentText(text)
            builder.setSmallIcon(service.getApplicationInfo().icon)
            builder.setOngoing(True)
            builder.setPriority(NotifCompat.PRIORITY_LOW)
            service.startForeground(1, builder.build())

        # Iniciar como servicio en primer plano
        service = PythonService.mService
        show_foreground_notification(service)

        print('[PlayerService] Servicio en primer plano iniciado')

    except Exception as e:
        print(f'[PlayerService] Error iniciando servicio: {e}')

# El servicio corre en loop esperando comandos
# En la práctica, el audio lo maneja el proceso principal
# Este servicio solo mantiene el proceso vivo en Android
import time
while True:
    time.sleep(60)
