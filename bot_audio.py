import pygame
import os
import math
import wave
import struct

def generate_sounds():
    """Gera sons sintéticos mais altos e claros misturando ondas e frequências."""
    os.makedirs("sounds", exist_ok=True)
    
    # Cada som é uma lista de tuplas: (frequência_hz, duração_segundos)
    # Frequência 0 significa silêncio (pausa)
    sounds = {
        "Som 1 (Beep)": [(800, 0.3)],
        "Som 2 (Alerta)": [(1200, 0.1), (0, 0.05), (1200, 0.1), (0, 0.05), (1200, 0.2)],
        "Som 3 (Suave)": [(440, 0.2), (554, 0.2), (659, 0.5)],
        "Som 4 (Sino)": [(1046.50, 0.1), (1318.51, 0.4)], 
        "Som 5 (Urgente)": [(2000, 0.08), (0, 0.05), (2000, 0.08), (0, 0.05), (2000, 0.08), (0, 0.05), (2000, 0.08)]
    }
    
    for name, sequence in sounds.items():
        filename = f"sounds/{name}.wav"
        # Regeramos todos os áudios para aplicar a nova potência
        sample_rate = 44100
        
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            
            for freq, duration in sequence:
                n_samples = int(sample_rate * duration)
                for i in range(n_samples):
                    # Fade in/out muito curto apenas para evitar "estalos" no alto-falante
                    env = 1.0
                    if i < 200: env = i / 200
                    elif i > n_samples - 200: env = (n_samples - i) / 200
                    
                    if freq == 0:
                        value = 0
                    else:
                        t = 2.0 * math.pi * freq * i / sample_rate
                        sine_val = math.sin(t)
                        # Mistura onda senoidal com onda quadrada para dar bastante volume e clareza
                        square_val = 1.0 if sine_val > 0 else -1.0
                        mixed = (sine_val * 0.3 + square_val * 0.7) * env
                        # Multiplica pelo max volume suportado (32767) com um pequeno respiro (0.95)
                        value = int(32767.0 * mixed * 0.95)
                        
                    data = struct.pack('<h', value)
                    f.writeframesraw(data)

def init_audio():
    """Inicializa o sistema de som."""
    try:
        pygame.mixer.init()
        generate_sounds()
    except Exception as e:
        print(f"Erro ao inicializar áudio: {e}")

def play_sound(name, volume):
    """Toca o som especificado com o volume desejado."""
    if not name: return
    filename = f"sounds/{name}.wav"
    if os.path.exists(filename):
        try:
            sound = pygame.mixer.Sound(filename)
            sound.set_volume(float(volume))
            sound.play()
        except Exception as e:
            print(f"Erro ao tocar som: {e}")
