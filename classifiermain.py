from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics.texture import Texture
import cv2
import numpy as np
import tensorflow as tf
import pickle
import datetime

class VideoClassifierApp(App):

    def __init__(self, **kwargs):
        super(VideoClassifierApp, self).__init__(**kwargs)
        self.event_labels = {0: "Bombblast", 1: "Firing", 2: "Tank", 3: "Safe"}
        self.esp_cam_url = ""
        self.video_capture = None
        self.error_label = None
        self.log_file_path = "detection_log.txt"
        self.load_resources()

    def build(self):
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        enter_ip_label = TextInput(hint_text="Enter the IP", multiline=False, size_hint=(0.8, None), height=40)
        self.layout.add_widget(enter_ip_label)

        submit_button = Button(text="Start", on_press=self.on_submit, size_hint=(0.8, None), height=40, background_color=(0, 0.8, 0, 1))
        self.layout.add_widget(submit_button)

        self.image_widget = Image(allow_stretch=True, size_hint=(1, 0.7))
        self.layout.add_widget(self.image_widget)

        self.error_label = TextInput(readonly=True, multiline=False, size_hint=(1, 0.1), height=40, foreground_color=(1, 0, 0, 1))
        self.layout.add_widget(self.error_label)

        stop_button = Button(text="Stop", on_press=self.on_stop_video, size_hint=(0.8, None), height=40, background_color=(0.8, 0, 0, 1))
        self.layout.add_widget(stop_button)

        show_log_button = Button(text="Show Log", on_press=self.show_log_screen, size_hint=(0.8, None), height=40, background_color=(0, 0, 0.8, 1))
        self.layout.add_widget(show_log_button)

        return self.layout

    def load_resources(self):
        model_path = r"D:\videoclassifier\videoclassificationmodel\classificationmodel"
        binarizer_path = r"D:\videoclassifier\videoclassificationmodel\classificationbinarizer\videoclassification_binarizer.pickle"

        self.loaded_model = tf.keras.models.load_model(model_path)

        with open(binarizer_path, 'rb') as binarizer_file:
            self.lb = pickle.load(binarizer_file)

    def on_submit(self, instance):
        ip_input = None
        for widget in self.layout.walk():
            if isinstance(widget, TextInput):
                ip_input = widget
                break
        self.esp_cam_url = ip_input.text

        if self.start_video_stream():
            Clock.schedule_interval(self.update, 1.0 / 30.0)
            self.error_label.text = ""
        else:
            self.error_label.text = "IP not found"

    def start_video_stream(self):
        if self.video_capture is not None and self.video_capture.isOpened():
            self.video_capture.release()

        self.video_capture = cv2.VideoCapture(self.esp_cam_url)
        return self.video_capture.isOpened()

    def update(self, dt):
        ret, frame = self.video_capture.read()

        if not ret:
            print("Error: Failed to capture a frame.")
            return

        detected_frame = self.detect_events(frame)

        self.image_widget.texture = self.texture_from_frame(detected_frame)

    def detect_events(self, frame, confidence_threshold=0.9):
        detected_frame = frame.copy()

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (224, 224))
        image = np.expand_dims(image, axis=0)

        predictions = self.loaded_model.predict(image)
        event_index = int(np.argmax(predictions))
        confidence = predictions[0, event_index]

        event_label = self.event_labels.get(event_index, "Unknown")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if confidence > confidence_threshold:
            log_entry = f"{timestamp} - Event Detected: {event_label}"
            self.log_to_file(log_entry)

            cv2.putText(detected_frame, event_label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            cv2.putText(detected_frame, "Safe", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        return detected_frame

    def log_to_file(self, log_entry):
        with open(self.log_file_path, 'a') as log_file:
            log_file.write(log_entry + '\n')

    def texture_from_frame(self, frame):
        buf1 = cv2.flip(frame, 0)
        buf = buf1.tobytes()

        image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
        image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        return image_texture

    def on_stop_video(self, instance):
        if self.video_capture is not None and self.video_capture.isOpened():
            self.video_capture.release()
            Clock.unschedule(self.update)

    def show_log_screen(self, instance):
        log_screen = self.create_log_screen()
        self.layout.clear_widgets()
        self.layout.add_widget(log_screen)

    def create_log_screen(self):
        log_screen = BoxLayout(orientation='vertical', spacing=10, padding=10)

        log_entries = self.read_log_entries()
        log_label = Label(text='\n'.join(log_entries), font_size=14, size_hint_y=None, height=len(log_entries) * 25)
        scroll_view = ScrollView(size_hint=(1, 0.8))
        scroll_view.add_widget(log_label)

        back_button = Button(text="Back to Main Screen", on_press=self.back_to_main_screen, size_hint=(0.8, None), height=40, background_color=(0.8, 0.8, 0.8, 1))

        log_screen.add_widget(scroll_view)
        log_screen.add_widget(back_button)

        return log_screen

    def read_log_entries(self):
        try:
            with open(self.log_file_path, 'r') as log_file:
                log_entries = log_file.readlines()
            return log_entries
        except FileNotFoundError:
            return ["Log file not found."]

    def back_to_main_screen(self, instance):
        self.layout.clear_widgets()
        self.layout.add_widget(self.build())

if __name__ == '__main__':
    VideoClassifierApp().run()
