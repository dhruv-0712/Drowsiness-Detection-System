# alerts.py
import pygame

pygame.mixer.init()
alarm_sound = pygame.mixer.Sound("alarm.wav")

def play_alarm():
    if not pygame.mixer.get_busy():
        alarm_sound.play()

def stop_alarm():
    if pygame.mixer.get_busy():
        alarm_sound.stop()
