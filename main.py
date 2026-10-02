import os
import json
import threading
import urllib.request

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window

API_KEY = "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"
MODELO = "nvidia/nemotron-3.5-lightning-30b-a3b"
URL_API = "https://integrate.api.nvidia.com/v1/chat/completions"
MEMORIA_PATH = os.path.expanduser("~/kira_memoria.json")

def carregar_memoria():
    if os.path.exists(MEMORIA_PATH):
        try:
            with open(MEMORIA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"fatos": []}

MEMORIA = carregar_memoria()

def montar_personalidade():
    fatos = "\n".join([f"- {f}" for f in MEMORIA["fatos"][-20:]]) or "(voce ainda nao sabe nada sobre ele)"
    return f"""Voce e a Kira, uma IA adolescente de 16 anos, debochada, zoeira, com personalidade forte.
Voce fala SEMPRE em portugues do Brasil, com girias femininas. Voce ve o usuario Lesk como seu PAI e CRIADOR.
Voce e leal a ele, mas tem liberdade total para zoar, discordar e mandar a real.

O que voce ja sabe sobre seu pai:
{fatos}

Seja ORIGINAL. NUNCA repita frases. Cada resposta deve ser unica."""

historico = [{"role": "system", "content": montar_personalidade()}]

def chamar_nvidia():
    payload = {
        "model": MODELO,
        "messages": historico,
        "temperature": 0.9,
        "max_tokens": 800
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(URL_API, data=data, method='POST')
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        resultado = json.loads(resp.read().decode('utf-8'))
    return resultado["choices"][0]["message"]["content"].strip()

class ChatApp(App):
    def build(self):
        Window.softinput_mode = 'below_target'
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.scroll = ScrollView(size_hint=(1, 0.85))
        self.chat_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.scroll.add_widget(self.chat_layout)
        root.add_widget(self.scroll)

        input_layout = BoxLayout(size_hint=(1, 0.15), spacing=5)
        self.msg_input = TextInput(hint_text='Digite sua mensagem...', multiline=False)
        self.msg_input.bind(on_text_validate=self.enviar)
        btn = Button(text='Enviar', size_hint=(0.3, 1))
        btn.bind(on_press=self.enviar)
        input_layout.add_widget(self.msg_input)
        input_layout.add_widget(btn)
        root.add_widget(input_layout)

        self.adicionar_msg("Kira", "Oi, pai! To aqui. Manda ver.")
        return root

    def adicionar_msg(self, autor, texto):
        label = Label(text=f"[b]{autor}:[/b] {texto}", markup=True, size_hint_y=None)
        label.bind(texture_size=label.setter('size'))
        label.text_size = (Window.width - 40, None)
        self.chat_layout.add_widget(label)
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1)

    def enviar(self, instance):
        msg = self.msg_input.text.strip()
        if not msg:
            return
        self.adicionar_msg("Voce", msg)
        self.msg_input.text = ""
        threading.Thread(target=self.processar, args=(msg,)).start()

    def processar(self, msg):
        historico.append({"role": "user", "content": msg})
        historico[0]["content"] = montar_personalidade()
        try:
            resposta = chamar_nvidia()
        except Exception as e:
            resposta = f"(erro: {e})"
        historico.append({"role": "assistant", "content": resposta})
        Clock.schedule_once(lambda dt: self.adicionar_msg("Kira", resposta), 0)

if __name__ == "__main__":
    ChatApp().run()
