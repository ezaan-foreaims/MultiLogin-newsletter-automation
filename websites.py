from config import WEBSITES_FILE

def load_websites():
    try:
        with open(WEBSITES_FILE,'r',encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except:
        return ["https://scribblezone.com","https://hedd.audio"]
