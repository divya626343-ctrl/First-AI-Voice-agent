import speech_recognition as sr

recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.8
recognizer.non_speaking_duration = 0.5
recognizer.dynamic_energy_threshold = True


mic = sr.Microphone(sample_rate=16000)
calibrated = False


def listen_and_transcribe(timeout= 8, phrase_limit= 20):
    global calibrated
    with mic as source:
        if not calibrated:
            recognizer.adjust_for_ambient_noise(source, duration =1)
            calibrated = True
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit = phrase_limit)
        except sr.WaitTimeoutError:
            return None
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

    