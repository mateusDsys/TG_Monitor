import pygame
import os
import math
import wave
import struct

def generate_sounds():
    """Gera sons sintéticos focados em frequências graves e confortáveis para o ouvido."""
    os.makedirs("sounds", exist_ok=True)
    
    # Reduzindo drasticamente as frequências. O ouvido humano acha mais confortável sons entre 200Hz e 800Hz.
    # Usando principalmente onda "sine" (senoidal) que é suave e redonda.
    
    sounds = {
        # Um "tum" encorpado, como uma notificação moderna de celular (400Hz)
        "Som 1 (Beep)": [(400, 0.3, "sine")],
        
        # Um zumbido grave de alerta duplo (tipo vibração forte de mesa - 150Hz)
        "Som 2 (Alerta)": [(150, 0.15, "sine"), (0, 0.05, "sine"), (150, 0.2, "sine")],
        
        # Acorde suave de subida, muito confortável (Dó3, Mi3, Sol3 - graves)
        "Som 3 (Suave)": [(261.63, 0.2, "sine"), (329.63, 0.2, "sine"), (392.00, 0.4, "sine")],
        
        # Um gongo tibetano suave (começa em 300Hz e vai decaindo na nossa percepção simulada)
        "Som 4 (Sino)": [(300, 0.1, "sine"), (250, 0.5, "sine")], 
        
        # Notificação de "atenção" parecida com radar de submarino (Grave e rítmico - 200Hz)
        "Som 5 (Urgente)": [(200, 0.08, "sine"), (0, 0.05, "sine")] * 4
    }
    
    for name, sequence in sounds.items():
        filename = f"sounds/{name}.wav"
        sample_rate = 44100
        
        with wave.open(filename, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            
            for freq, duration, wave_type in sequence:
                n_samples = int(sample_rate * duration)
                for i in range(n_samples):
                    t = 2.0 * math.pi * freq * i / sample_rate
                    val = math.sin(t)
                    
                    # Suavização (Envelope) MUITO maior para deixar o som redondo
                    # Fade in de 15% e Fade out de 40% do tempo do som
                    env = 1.0
                    fade_in_samples = int(n_samples * 0.15)
                    fade_out_samples = int(n_samples * 0.4)
                    
                    if i < fade_in_samples: 
                        env = i / fade_in_samples
                    elif i > n_samples - fade_out_samples: 
                        env = (n_samples - i) / fade_out_samples
                    
                    # Volume geral mais contido (70% do máximo) para não assustar
                    value = int(32767.0 * val * env * 0.7)
                    f.writeframesraw(struct.pack('<h', value))

def init_audio():
    """Inicializa o sistema de som."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
        generate_sounds()
    except Exception as e:
        print(f"Erro init áudio: {e}")

def play_sound(name, volume):
    """Toca o som com reset forçado para evitar travamentos do buffer."""
    if not name: return
    filename = f"sounds/{name}.wav"
    if os.path.exists(filename):
        try:
            pygame.mixer.stop() # Para som atual para não encavalar
            sound = pygame.mixer.Sound(filename)
            sound.set_volume(float(volume))
            sound.play()
        except Exception as e:
            print(f"Erro play: {e}")
