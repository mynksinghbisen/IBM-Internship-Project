from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import base64
import time
# from dotenv import load_dotenv
from dotenv import load_dotenv
import socket

# Force IPv4
original_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'socialai-secret-key-2024')

HF_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
HF_HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

IMAGE_MODELS = [
    "black-forest-labs/FLUX.1-dev",
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-3-medium-diffusers",
]


TEXT_MODELS = [
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3.5-mini-instruct",
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
]



@app.route('/')
def index():
    return send_from_directory('templates', 'login.html')

@app.route('/login.html')
def login():
    return send_from_directory('templates', 'login.html')

@app.route('/signup.html')
def signup():
    return send_from_directory('templates', 'signup.html')

@app.route('/<path:filename>')
def serve_file(filename):
    if filename.endswith('.html'):
        return send_from_directory('templates', filename)
    return send_from_directory('static', filename)


@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    if not HF_API_KEY:
        return jsonify({'error': 'HUGGINGFACE_API_KEY not set in .env'}), 500

    data     = request.get_json()
    topic    = data.get('topic', '').strip()
    desc     = data.get('description', '').strip()
    platform = data.get('platform', 'Instagram')

    if not topic and not desc:
        return jsonify({'error': 'Topic or description is required'}), 400

    platform_style = {
        'Instagram': 'vibrant aesthetic photography, instagram worthy, colorful, stunning lighting, 4k',
        'LinkedIn':  'clean professional corporate photo, white background, business style, sharp',
        'Twitter':   'colorful eye-catching graphic, dynamic composition, bright vivid colors, photorealistic, 4k',
    }.get(platform, 'high quality, detailed, 4k')

    prompt = f"{topic}, {desc}, {platform_style}, full color, vibrant colors, highly detailed, trending, photorealistic"
    payload = {
        "inputs": prompt,
        "parameters": {"num_inference_steps": 28, "guidance_scale": 7.5},
    }

    last_err = "All models failed"
    for model in IMAGE_MODELS:
        url = f"https://router.huggingface.co/hf-inference/models/{model}"
        try:
            print(f"Trying image model: {model}")
            resp = requests.post(url, headers=HF_HEADERS, json=payload, timeout=90)
            print(f"Status: {resp.status_code} | Content-Type: {resp.headers.get('content-type','')}")

            if resp.status_code == 200 and resp.headers.get('content-type', '').startswith('image'):
                b64 = base64.b64encode(resp.content).decode()
                print(f"Image generated with: {model}")
                return jsonify({'success': True, 'image': f'data:image/jpeg;base64,{b64}', 'model': model})

            if resp.status_code == 503:
                print(f"Model loading, waiting 20s...")
                time.sleep(20)
                resp = requests.post(url, headers=HF_HEADERS, json=payload, timeout=90)
                if resp.status_code == 200 and resp.headers.get('content-type', '').startswith('image'):
                    b64 = base64.b64encode(resp.content).decode()
                    return jsonify({'success': True, 'image': f'data:image/jpeg;base64,{b64}', 'model': model})

            try:
                last_err = resp.json().get('error', f'HTTP {resp.status_code}')
            except:
                last_err = f'HTTP {resp.status_code}'
            print(f"Image model failed: {model} | {last_err}")

        except requests.Timeout:
            last_err = f'Timeout on {model}'
            continue
        except Exception as e:
            last_err = str(e)
            continue

    return jsonify({'error': f'Image generation failed: {last_err}'}), 500


@app.route('/api/generate-caption', methods=['POST'])
def generate_caption():
    if not HF_API_KEY:
        return jsonify({'error': 'HUGGINGFACE_API_KEY not set in .env'}), 500

    data     = request.get_json()
    topic    = data.get('topic', '').strip()
    desc     = data.get('description', '').strip()
    platform = data.get('platform', 'Instagram')
    tone     = data.get('tone', 'Professional')

    if not topic and not desc:
        return jsonify({'error': 'Topic or description is required'}), 400

    platform_rules = {
        'Instagram': 'Add 10-15 relevant hashtags at the end. Use emojis. Keep it engaging and visual.',
        'LinkedIn':  'Professional tone. No excessive emojis. Max 2-3 hashtags. Use line breaks for readability.',
        'Twitter':   'Keep total under 280 characters. 1-2 hashtags max. Punchy and concise.',
    }.get(platform, 'Write an engaging social media caption.')

    tone_guide = {
        'Professional':  'formal, authoritative, polished business language',
        'Witty & Funny': 'humorous, witty, clever jokes, make people laugh and share',
        'Inspirational': 'motivating, uplifting, thought-provoking, include a call-to-action',
        'Casual':        'friendly, conversational, relaxed like texting a friend',
        'Bold':          'confident, direct, powerful short sentences, strong statement',
        'Empathetic':    'warm, emotionally connected, caring, understanding audience feelings',
        'Educational':   'informative, teach something, share useful facts or tips',
        'Storytelling':  'narrative mini-story, hook in first line, personal and engaging',
    }.get(tone, 'engaging and creative')

    subject = f"{topic}. {desc}".strip('. ')

    last_err = "All models failed"
    for model_id in TEXT_MODELS:
        chat_url = f"https://router.huggingface.co/hf-inference/models/{model_id}/v1/chat/completions"
        try:
            print(f"Trying caption model: {model_id}")
            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a social media expert. Write only the caption text. No explanations, no intro, no quotes."
                    },
                    {
                        "role": "user",
                        "content": f"Write a {platform} social media caption about: {subject}. Tone: {tone_guide}. {platform_rules}"
                    }
                ],
                "max_tokens": 400,
                "temperature": 0.8,
                "stream": False
            }

            resp = requests.post(chat_url, headers=HF_HEADERS, json=payload, timeout=60)
            print(f"Caption status: {resp.status_code}")

            if resp.status_code == 503:
                time.sleep(15)
                resp = requests.post(chat_url, headers=HF_HEADERS, json=payload, timeout=60)

            if resp.status_code == 200:
                result = resp.json()
                caption = ""
                if isinstance(result, list) and result:
                 caption = result[0].get('generated_text', '')
                elif isinstance(result, dict):
                 caption = result.get('generated_text', '')

                caption = caption.strip().strip('"').strip("'").strip()
                for tag in ['[/INST]', '<|assistant|>', '<|end|>', '[INST]', '<s>', '</s>']:
                    if tag in caption:
                        caption = caption.split(tag)[-1].strip()

                print(f"Caption result: {caption[:80]}...")
                if len(caption) > 20:
                    return jsonify({'success': True, 'caption': caption, 'model': model_id})
                else:
                    last_err = f"Caption too short"
                    continue
            else:
                try:
                    last_err = resp.json().get('error', f'HTTP {resp.status_code}')
                except:
                    last_err = f'HTTP {resp.status_code}'
                print(f"Caption model failed: {model_id} | {last_err}")
                continue

        except requests.Timeout:
            last_err = f'Timeout on {model_id}'
            continue
        except Exception as e:
            last_err = str(e)
            continue

    print(f"All caption models failed. Using fallback. Last error: {last_err}")
    fallback = build_fallback_caption(topic or desc, platform, tone)
    return jsonify({'success': True, 'caption': fallback, 'model': 'fallback'})


def build_fallback_caption(topic, platform, tone):
    topic = topic.strip().capitalize()
    ig_tags = f"#{topic.replace(' ','').lower()} #socialmedia #content #trending #viral #explore #instagood #reels #post #digital"
    li_tags = f"#{topic.replace(' ','').lower()} #linkedin #professional"
    tw_tags = f"#{topic.replace(' ','').lower()}"

    templates = {
        'Instagram': {
            'Professional':  f"Elevating the conversation around {topic}. Excellence isn't an accident — it's a habit. 💼✨\n\n{ig_tags}",
            'Witty & Funny': f"Me: I'll keep it short about {topic}.\nAlso me: 📝📝📝\n\nSend help. 😂\n\n{ig_tags}",
            'Inspirational': f"Every great journey starts with a single step. Today, that step is {topic}. 🚀\nDream big. Start now. ✨\n\n{ig_tags}",
            'Casual':        f"Just vibing with some {topic} content today ☀️ Drop a ❤️ if you relate!\n\n{ig_tags}",
            'Bold':          f"No fluff. No filler. Just {topic}. 🔥\nThis changes everything.\n\n{ig_tags}",
            'Empathetic':    f"We all have a story. Here's mine about {topic}. 💛\nYou're not alone in this journey.\n\n{ig_tags}",
            'Educational':   f"📚 Did you know? Everything you need to know about {topic} — in one post.\nSave this for later! 👇\n\n{ig_tags}",
            'Storytelling':  f"It started with {topic}. Nobody knew what would happen next... 🧵\nRead the thread below. ⬇️\n\n{ig_tags}",
        },
        'LinkedIn': {
            'Professional':  f"Sharing some thoughts on {topic}.\n\nIn today's landscape, this has never been more important.\n\n▸ Focus on what matters\n▸ Stay consistent\n▸ Keep growing\n\nWhat's your take? 👇\n\n{li_tags}",
            'Witty & Funny': f"Hot take on {topic}: it's more complicated than it looks. 😄\n\nAgree or disagree? 👇\n\n{li_tags}",
            'Inspirational': f"Success in {topic} doesn't happen overnight.\n\nIt takes dedication and courage.\n\nKeep pushing forward. 🚀\n\n{li_tags}",
            'Casual':        f"Real talk about {topic} — it's been quite a journey! 🙌\n\n{li_tags}",
            'Bold':          f"{topic.upper()}. This is the conversation we need right now.\n\n{li_tags}",
            'Empathetic':    f"Behind every success story with {topic} is someone who almost gave up. 💙\n\n{li_tags}",
            'Educational':   f"3 things about {topic} most people get wrong:\n\n1️⃣ Consistency beats perfection\n2️⃣ Community matters most\n3️⃣ Start before you're ready\n\nSave this. 📌\n\n{li_tags}",
            'Storytelling':  f"18 months ago, I knew nothing about {topic}. Today, it changed everything. 👇\n\n{li_tags}",
        },
        'Twitter': {
            'Professional':  f"Thoughts on {topic}: quality always wins. {tw_tags}",
            'Witty & Funny': f"{topic} got me like 😭 anyone else? {tw_tags}",
            'Inspirational': f"Your {topic} journey starts with one decision. Make it today. 🚀 {tw_tags}",
            'Casual':        f"ngl {topic} has been living rent free in my head 😅 {tw_tags}",
            'Bold':          f"{topic}. No cap. This is the way. 🔥 {tw_tags}",
            'Empathetic':    f"To everyone figuring out {topic} — you're doing better than you think. 💙 {tw_tags}",
            'Educational':   f"Quick {topic} tip that changed everything 🧵👇 {tw_tags}",
            'Storytelling':  f"A thread about {topic} and why it matters more than you think 🧵 {tw_tags}",
        }
    }

    plat_templates = templates.get(platform, templates['Instagram'])
    return plat_templates.get(tone, plat_templates.get('Professional', f"Excited to share about {topic}! 🚀"))


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'hf_configured': bool(HF_API_KEY)})


if __name__ == '__main__':
    print("SocialFlow AI running at http://localhost:5000")
    app.run(debug=True, port=5000)